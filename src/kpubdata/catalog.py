"""카탈로그 — 데이터셋 탐색, 검색, 해석."""

from __future__ import annotations

import builtins
import logging
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import cast

from kpubdata.core.models import DatasetRef
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError, ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry

logger = logging.getLogger("kpubdata.catalog")

# 검색 결과에 포함되기 위한 데이터셋의 최소 관련도 점수(0.0–1.0).
_DEFAULT_SCORE_THRESHOLD = 0.5

# 토큰 중첩 점수 구간 — 항상 부분 문자열 1.0 점수보다 엄격히 낮게 유지하여
# 정확한 부분 문자열 일치가 순위 우선권을 유지하도록 한다.
_TOKEN_OVERLAP_FLOOR = 0.7
_TOKEN_OVERLAP_CEIL = 0.95

# 유니코드 단어 토큰(문자, 숫자, 밑줄)이다. ``village_fcst`` 같은 식별자형 토큰은
# 하나의 토큰으로 유지되며, 이는 Provider 카탈로그에서 dataset_key 문자열이
# 작성되는 방식과 일치한다.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _normalize(text: str) -> str:
    """검색 비교를 위해 문자열을 NFC 정규화하고 공백 제거 후 소문자화한다."""
    return unicodedata.normalize("NFC", text).strip().casefold()


def _tokenize(text: str) -> frozenset[str]:
    """*text*를 결정적인 정규화 단어 토큰 집합으로 분해한다."""
    if not text:
        return frozenset()
    return frozenset(_TOKEN_RE.findall(_normalize(text)))


@dataclass(slots=True, frozen=True)
class _IndexedItem:
    """단일 데이터셋용 사전 계산 검색 페이로드.

    :class:`DatasetRef`와 정규화된 필드 문자열, 결정적인 토큰 집합을 함께
    보관하여 :class:`Catalog.search`가 호출마다 정규화 작업을 다시 하지 않고도
    각 항목의 점수를 계산할 수 있게 한다.
    """

    dataset: DatasetRef
    fields: tuple[str, ...]
    tokens: frozenset[str]


def _build_index(datasets: builtins.list[DatasetRef]) -> builtins.list[_IndexedItem]:
    """*datasets*에 대한 메모리 내 검색 인덱스를 구성한다.

    각 항목은 정규화된 필드 문자열(name, description, tags, id,
    dataset_key, provider)과 그 필드들에서 추출한 단어 토큰의 합집합을
    노출한다. 인덱스 구성은 후보 집합 크기에 대해 O(n)이며 검색 호출당 한 번
    실행된다.
    """
    index: builtins.list[_IndexedItem] = []
    for dataset in datasets:
        field_sources: builtins.list[str] = [
            dataset.name,
            dataset.id,
            dataset.dataset_key,
            dataset.provider,
        ]
        if dataset.description:
            field_sources.append(dataset.description)
        field_sources.extend(dataset.tags)

        normalized_fields: builtins.list[str] = []
        tokens: set[str] = set()
        for source in field_sources:
            normalized = _normalize(source)
            normalized_fields.append(normalized)
            tokens.update(_TOKEN_RE.findall(normalized))

        index.append(
            _IndexedItem(
                dataset=dataset,
                fields=tuple(normalized_fields),
                tokens=frozenset(tokens),
            )
        )
    return index


def _score_indexed(
    needle: str,
    needle_tokens: frozenset[str],
    item: _IndexedItem,
) -> float:
    """사전 정규화된 질의와 그 토큰 집합으로 *item*의 점수를 계산한다.

    우선순위에 따른 점수 계층은 다음과 같다.

    1. 인덱싱된 필드 어디에서든 **정확한 부분 문자열** 일치 → ``1.0``.
    2. **토큰 중첩도** = 일치한 질의 토큰 수 / 전체 질의 토큰 수. 이 값은
       ``[_TOKEN_OVERLAP_FLOOR, _TOKEN_OVERLAP_CEIL]`` 구간으로 사상되어,
       토큰 증거가 부분 문자열 일치보다 높은 순위를 차지하지 않게 한다.
    3. 필드 전반의 ``SequenceMatcher`` 비율을 이용한 **퍼지 보정**.

    1단계가 일치하지 않으면 최종 점수는 ``max(2단계, 3단계)``가 된다. 이는
    기존 재현율을 유지하면서(퍼지 결과를 버리지 않으면서) 토큰 증거로 임계값
    근처의 결과를 더 잘 끌어올리기 위함이다.
    """
    if not needle:
        return 1.0

    for text in item.fields:
        if needle in text:
            return 1.0

    overlap_score = 0.0
    if needle_tokens:
        matched = len(needle_tokens & item.tokens)
        if matched:
            ratio = matched / len(needle_tokens)
            overlap_score = (
                _TOKEN_OVERLAP_FLOOR + (_TOKEN_OVERLAP_CEIL - _TOKEN_OVERLAP_FLOOR) * ratio
            )

    fuzzy_score = 0.0
    for text in item.fields:
        candidate = SequenceMatcher(None, needle, text).ratio()
        if candidate > fuzzy_score:
            fuzzy_score = candidate

    return max(overlap_score, fuzzy_score)


def _score_dataset(needle: str, dataset: DatasetRef) -> float:
    """단일 데이터셋을 *needle*에 대해 점수화한다(공개 내부 헬퍼).

    전체 인덱스를 만들지 않고 한 데이터셋만 점수화하려는 호출자를 위해
    유지된다. 내부적으로 일회성 인덱스 항목을 만들어 동작이
    :class:`Catalog.search`와 일치하도록 한다.
    """
    needle_normalized = _normalize(needle)
    if not needle_normalized:
        return 1.0
    needle_tokens = frozenset(_TOKEN_RE.findall(needle_normalized))
    index = _build_index([dataset])
    return _score_indexed(needle_normalized, needle_tokens, index[0])


class Catalog:
    """등록된 Provider 전반에서 데이터셋 탐색 기능을 제공한다."""

    _registry: ProviderRegistry

    def __init__(self, registry: ProviderRegistry) -> None:
        """제공자 레지스트리에 연결된 카탈로그를 초기화한다."""

        self._registry = registry

    def list(self, *, provider: str | None = None) -> builtins.list[DatasetRef]:
        """탐색 가능한 데이터셋을 반환하며, 필요하면 Provider로 필터링한다.

        예외:
            ProviderNotRegisteredError: ``provider``가 주어졌지만 알 수 없는 경우.
        """

        logger.debug("Catalog list", extra={"provider_filter": provider})
        if provider is not None:
            adapter = self._get_adapter(provider)
            provider_datasets = adapter.list_datasets()
            logger.debug(
                "Catalog list result",
                extra={"provider": provider, "count": len(provider_datasets)},
            )
            return provider_datasets

        datasets: builtins.list[DatasetRef] = []
        for provider_name in self._registry:
            adapter = self._get_adapter(provider_name)
            datasets.extend(adapter.list_datasets())
        logger.debug(
            "Catalog list result",
            extra={"provider": None, "count": len(datasets)},
        )
        return datasets

    def search(
        self,
        text: str,
        *,
        provider: str | None = None,
        threshold: float = _DEFAULT_SCORE_THRESHOLD,
    ) -> builtins.list[DatasetRef]:
        """이름, 설명, 태그, id를 대상으로 퍼지 매칭하여 데이터셋을 검색한다.

        결과는 관련도 점수에 따라 내림차순으로 반환된다.
        점수가 *threshold*(0.0–1.0)를 충족하는 데이터셋만 포함된다.

        예외:
            ProviderNotRegisteredError: ``provider``가 주어졌지만 알 수 없는 경우.
        """

        logger.debug(
            "Catalog search",
            extra={"text": text, "provider_filter": provider, "threshold": threshold},
        )
        candidates = self.list(provider=provider)
        index = _build_index(candidates)

        needle_normalized = _normalize(text)
        needle_tokens = frozenset(_TOKEN_RE.findall(needle_normalized))

        scored: builtins.list[tuple[float, DatasetRef]] = []
        for item in index:
            score = _score_indexed(needle_normalized, needle_tokens, item)
            if score >= threshold:
                scored.append((score, item.dataset))

        # 점수 내림차순, 이후 안정적인 순서를 위해 id 기준으로 정렬
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        results = [dataset for _, dataset in scored]

        logger.debug(
            "Catalog search result",
            extra={
                "provider": provider,
                "text": text,
                "candidates": len(candidates),
                "count": len(results),
            },
        )
        return results

    def resolve(self, dataset_id: str) -> tuple[ProviderAdapter, DatasetRef]:
        """``provider.dataset_key``를 어댑터와 데이터셋 참조로 해석한다.

        예외:
            DatasetNotFoundError: 데이터셋 id 형식이 잘못되었거나 찾을 수 없는 경우.
            ProviderNotRegisteredError: Provider가 등록되지 않은 경우.
        """

        provider_name, dataset_key = self._split_dataset_id(dataset_id)
        logger.debug(
            "Catalog resolve",
            extra={
                "dataset_id": dataset_id,
                "provider": provider_name,
                "dataset_key": dataset_key,
            },
        )
        adapter = self._get_adapter(provider_name)

        try:
            return adapter, adapter.get_dataset(dataset_key)
        except DatasetNotFoundError:
            logger.debug(
                "Catalog resolve failed: dataset not found",
                extra={"dataset_id": dataset_id, "provider": provider_name},
            )
            raise
        except Exception as exc:
            logger.debug(
                "Catalog resolve failed: adapter raised",
                extra={
                    "dataset_id": dataset_id,
                    "provider": provider_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise DatasetNotFoundError(
                f"Dataset not found: {dataset_id}",
                provider=provider_name,
                dataset_id=dataset_id,
            ) from exc

    def _get_adapter(self, provider: str) -> ProviderAdapter:
        """레지스트리에서 Provider 어댑터를 가져오거나 정규 예외를 발생시킨다."""

        try:
            return cast(ProviderAdapter, self._registry.get(provider))
        except ProviderNotRegisteredError:
            raise

    @staticmethod
    def _split_dataset_id(dataset_id: str) -> tuple[str, str]:
        """정규 데이터셋 id를 ``(provider, dataset_key)``로 분리한다."""

        parts = dataset_id.split(".", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise DatasetNotFoundError(
                f"Invalid dataset id format: {dataset_id}", dataset_id=dataset_id
            )
        return parts[0], parts[1]


__all__ = ["Catalog", "_score_dataset", "_tokenize"]
