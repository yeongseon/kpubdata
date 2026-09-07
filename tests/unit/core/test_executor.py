"""core/executor.py 단위 테스트 — spec 실행기의 관찰 가능한 동작을 검증한다.

FakeTransport/FakeConfig는 실제 HttpTransport·KPubDataConfig의 해당 인터페이스를
표준 타입을 유지하며 대체한다(재사용 패턴: tests/unit/providers/datago/conftest.py).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.executor import (
    SpecDatasetAdapter,
    SpecExecutor,
    build_spec_dataset_ref,
)
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.spec import SpecDefinition, load_spec_file
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ProviderResponseError,
    RateLimitError,
    ServiceUnavailableError,
    TransportError,
)

SPECS_DIR = Path(__file__).resolve().parents[3] / "src" / "kpubdata" / "specs"
FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


class FakeResponse:
    """httpx.Response의 최소 인터페이스(content·headers)를 흉내낸다."""

    def __init__(self, content: bytes, content_type: str = "application/json") -> None:
        self.content = content
        self.headers = {"content-type": content_type}


class FakeTransport:
    """요청을 기록하고 미리 준비한 응답(또는 예외)을 반환한다."""

    def __init__(
        self,
        responses: list[FakeResponse] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.calls: list[dict[str, object]] = []
        self._responses = list(responses or [])
        self._error = error

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        json_body: object = None,
        dataset_id: str | None = None,
        provider: str | None = None,
        secret_values: tuple[str, ...] = (),
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": dict(params or {}),
                "dataset_id": dataset_id,
                "provider": provider,
            }
        )
        if self._error is not None:
            raise self._error
        if not self._responses:
            raise AssertionError("FakeTransport에 준비된 응답이 없습니다.")
        return self._responses.pop(0)


class FakeConfig(KPubDataConfig):
    """키 조회만 고정값으로 대체한 설정."""

    def get_provider_key(self, provider: str) -> str | None:
        return f"test-key-{provider}"

    def require_provider_key(self, provider: str) -> str:
        return f"test-key-{provider}"


def _golden_spec(dataset_key: str) -> SpecDefinition:
    """번들 골든 spec을 로드한다."""
    return load_spec_file(SPECS_DIR / "datago" / f"{dataset_key}.yaml")


def _standard_envelope(
    items: list[dict[str, object]] | dict[str, object] | None,
    total_count: int | None = 30,
    result_code: str = "00",
) -> FakeResponse:
    """data.go.kr standard envelope 응답을 만든다."""
    body: dict[str, object] = {}
    if items is None:
        body["items"] = None
    else:
        body["items"] = {"item": items}
    if total_count is not None:
        body["totalCount"] = str(total_count)
    payload = {"response": {"header": {"resultCode": result_code, "resultMsg": "OK"}, "body": body}}
    return FakeResponse(json.dumps(payload).encode("utf-8"))


def _make_executor(transport: FakeTransport) -> SpecExecutor:
    return SpecExecutor(transport, FakeConfig())


def _ref(spec: SpecDefinition) -> DatasetRef:
    return build_spec_dataset_ref(spec)


@pytest.fixture()
def apt_spec() -> SpecDefinition:
    return _golden_spec("apt_trade")


@pytest.fixture()
def village_spec() -> SpecDefinition:
    return _golden_spec("village_fcst")


# ----------------------------------------------------------------------
# 파라미터 조립
# ----------------------------------------------------------------------


def test_build_params_assembles_auth_format_pagination_filters(apt_spec: SpecDefinition) -> None:
    """인증·포맷·페이지네이션·필터가 모두 조립된다."""
    executor = _make_executor(FakeTransport())
    query = Query(filters={"LAWD_CD": "11110", "DEAL_YMD": "202401"}, page=2, page_size=50)
    params = executor.build_params(apt_spec, query)

    assert params["serviceKey"] == "test-key-datago"
    assert params["resultType"] == "json"
    assert params["pageNo"] == "2"
    assert params["numOfRows"] == "50"
    assert params["LAWD_CD"] == "11110"
    assert params["DEAL_YMD"] == "202401"


def test_build_params_reserved_keys_not_overwritten(apt_spec: SpecDefinition) -> None:
    """사용자 필터가 인증/포맷/페이지 파라미터를 덮어쓰지 않는다."""
    executor = _make_executor(FakeTransport())
    query = Query(filters={"serviceKey": "hijack", "pageNo": "999"})
    params = executor.build_params(apt_spec, query)
    assert params["serviceKey"] == "test-key-datago"
    assert params["pageNo"] == "1"


def test_build_params_max_size_clamp(apt_spec: SpecDefinition) -> None:
    """page_size가 max_size를 초과하면 잘린다."""
    executor = _make_executor(FakeTransport())
    params = executor.build_params(apt_spec, Query(page=1, page_size=99999))
    assert int(params["numOfRows"]) == 1000


def test_build_params_unsupported_pagination_raises(apt_spec: SpecDefinition) -> None:
    """미지원 페이지네이션 방식은 NotImplementedError를 낸다."""
    executor = _make_executor(FakeTransport())
    spec = replace(apt_spec, pagination=replace(apt_spec.pagination, type="index_range"))
    with pytest.raises(NotImplementedError, match="index_range"):
        executor.build_params(spec, Query(page=1))


# ----------------------------------------------------------------------
# query: envelope·페이지네이션
# ----------------------------------------------------------------------


def test_query_multi_items_with_total_count(apt_spec: SpecDefinition) -> None:
    """총건수 기반 next_page 계산이 어댑터 시맨틱과 일치한다."""
    items = [{"아파트": "래미안", "거래금액": "120,000"} for _ in range(10)]
    transport = FakeTransport([_standard_envelope(items, total_count=30)])
    executor = _make_executor(transport)
    batch = executor.query(apt_spec, _ref(apt_spec), Query(page=1, page_size=10))
    assert len(batch.items) == 10
    assert batch.total_count == 30
    assert batch.next_page == 2
    call = transport.calls[0]
    assert (
        call["url"]
        == "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    )
    assert call["provider"] == "datago"
    assert call["dataset_id"] == "datago.apt_trade"


def test_query_single_item_dict_wrapped(apt_spec: SpecDefinition) -> None:
    """단일 item dict가 1건 리스트로 정규화된다."""
    transport = FakeTransport([_standard_envelope({"아파트": "단일"}, total_count=1)])
    executor = _make_executor(transport)
    batch = executor.query(apt_spec, _ref(apt_spec), Query(page=1, page_size=10))
    assert batch.items == [{"아파트": "단일"}]
    assert batch.next_page is None


def test_query_empty_items(apt_spec: SpecDefinition) -> None:
    """빈 페이지는 빈 배치·next_page=None을 반환한다."""
    transport = FakeTransport([_standard_envelope(None, total_count=None)])
    executor = _make_executor(transport)
    batch = executor.query(apt_spec, _ref(apt_spec), Query(page=1, page_size=10))
    assert batch.items == []
    assert batch.total_count is None
    assert batch.next_page is None


def test_query_full_page_without_total_suggests_next(apt_spec: SpecDefinition) -> None:
    """총건수가 없을 때 꽉 찬 페이지는 다음 페이지 신호로 간주한다."""
    items = [{"no": i} for i in range(10)]
    transport = FakeTransport([_standard_envelope(items, total_count=None)])
    executor = _make_executor(transport)
    batch = executor.query(apt_spec, _ref(apt_spec), Query(page=1, page_size=10))
    assert batch.next_page == 2


def test_query_default_page_size_is_100(apt_spec: SpecDefinition) -> None:
    """page 미지정 시 page=1·page_size=100 기본값이 쓰인다."""
    transport = FakeTransport([_standard_envelope([{"x": 1}], total_count=1)])
    executor = _make_executor(transport)
    executor.query(apt_spec, _ref(apt_spec), Query())
    params = transport.calls[0]["params"]
    assert isinstance(params, dict)
    assert params["pageNo"] == "1"
    assert params["numOfRows"] == "100"


# ----------------------------------------------------------------------
# query: 에러 매핑
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "expected_exc"),
    [
        ("30", AuthError),
        ("31", AuthError),
        ("20", AuthError),
        ("32", AuthError),
        ("22", RateLimitError),
        ("10", InvalidRequestError),
        ("12", DatasetNotFoundError),
        ("01", ServiceUnavailableError),
        ("02", ServiceUnavailableError),
        ("99", ProviderResponseError),
    ],
)
def test_query_error_code_table(
    apt_spec: SpecDefinition, code: str, expected_exc: type[Exception]
) -> None:
    """resultCode→표준 예외 매핑 테이블이 어댑터와 동일하다."""
    payload = {
        "response": {
            "header": {"resultCode": code, "resultMsg": f"에러 {code}"},
            "body": {"items": None},
        }
    }
    transport = FakeTransport([FakeResponse(json.dumps(payload).encode())])
    executor = _make_executor(transport)
    with pytest.raises(expected_exc) as exc_info:
        executor.query(apt_spec, _ref(apt_spec), Query())
    assert getattr(exc_info.value, "provider_code", None) == code


@pytest.mark.parametrize("ok_code", ["000", "0"])
def test_query_ok_values_numeric_zero(apt_spec: SpecDefinition, ok_code: str) -> None:
    """ "000"/"0" 성공 코드도 int 정규화로 통과한다."""
    payload = {
        "response": {
            "header": {"resultCode": ok_code, "resultMsg": "OK"},
            "body": {"items": {"item": {"a": 1}}, "totalCount": "1"},
        }
    }
    transport = FakeTransport([FakeResponse(json.dumps(payload).encode())])
    executor = _make_executor(transport)
    batch = executor.query(apt_spec, _ref(apt_spec), Query())
    assert len(batch.items) == 1


def test_query_missing_result_code_raises(apt_spec: SpecDefinition) -> None:
    """resultCode가 없는 envelope은 ProviderResponseError가 된다."""
    transport = FakeTransport([FakeResponse(b'{"response": {"header": {}, "body": {}}}')])
    executor = _make_executor(transport)
    with pytest.raises(ProviderResponseError, match="에러 코드"):
        executor.query(apt_spec, _ref(apt_spec), Query())


def test_query_http_403_maps_to_auth_error(apt_spec: SpecDefinition) -> None:
    """전송 계층 403(httpx 원인 체인)은 활용신청 힌트 AuthError가 된다."""
    request = httpx.Request("GET", "https://apis.data.go.kr/x")
    response = httpx.Response(status_code=403, request=request)
    cause = httpx.HTTPStatusError("403", request=request, response=response)
    transport_error = TransportError("forbidden", provider="datago")
    transport_error.__cause__ = cause
    executor = _make_executor(FakeTransport(error=transport_error))
    with pytest.raises(AuthError, match="활용"):
        executor.query(apt_spec, _ref(apt_spec), Query())


# ----------------------------------------------------------------------
# query: XML·fields 정규화
# ----------------------------------------------------------------------


def test_query_xml_format_hint(village_spec: SpecDefinition) -> None:
    """format_hint=xml이 포맷 파라미터를 바꾸고 XML 응답을 파싱한다."""
    xml_payload = (
        "<response><header><resultCode>00</resultCode></header>"
        "<body><items><item><category>T1H</category><fcstValue>12.3</fcstValue></item></items>"
        "<totalCount>1</totalCount></body></response>"
    )
    transport = FakeTransport([FakeResponse(xml_payload.encode(), content_type="text/xml")])
    executor = _make_executor(transport)
    batch = executor.query(
        village_spec,
        _ref(village_spec),
        Query(filters={"base_date": "20250401", "base_time": "0500", "nx": 55, "ny": 127}),
        format_hint="xml",
    )
    params = transport.calls[0]["params"]
    assert isinstance(params, dict)
    assert params["dataType"] == "XML"
    assert params["base_date"] == "20250401"
    assert batch.items == [{"category": "T1H", "fcstValue": "12.3"}]
    assert batch.total_count == 1


def test_query_fields_normalization() -> None:
    """fields 선언이 있으면 rename·transform·캐스팅이 적용된다."""
    spec = load_spec_file(FIXTURES_DIR / "specs" / "valid_full.yaml")
    record = {"거래금액": "120,000", "년": "2024"}
    payload = {
        "response": {
            "header": {"resultCode": "00"},
            "body": {"items": {"item": record}, "totalCount": "1"},
        }
    }
    transport = FakeTransport([FakeResponse(json.dumps(payload).encode())])
    executor = _make_executor(transport)
    batch = executor.query(spec, _ref(spec), Query())
    item = batch.items[0]
    assert item["deal_amount"] == 120000
    assert "거래금액" not in item
    assert item["년"] == "2024"


# ----------------------------------------------------------------------
# 미지원 envelope / SpecDatasetAdapter
# ----------------------------------------------------------------------


def test_query_unsupported_envelope_raises(apt_spec: SpecDefinition) -> None:
    """datago_standard 외 envelope은 NotImplementedError."""
    spec = replace(apt_spec, response=replace(apt_spec.response, envelope="seoul_service_row"))
    executor = _make_executor(FakeTransport())
    with pytest.raises(NotImplementedError, match="seoul_service_row"):
        executor.query(spec, _ref(spec), Query())


def test_spec_dataset_adapter_surface(
    apt_spec: SpecDefinition, village_spec: SpecDefinition
) -> None:
    """어댑터 프로토콜 표면(list/search/get/query/raw)이 동작한다."""
    raw_payload = {"response": {"header": {"resultCode": "00"}, "body": {"items": None}}}
    transport = FakeTransport(
        [
            _standard_envelope([{"a": 1}], total_count=1),
            FakeResponse(json.dumps(raw_payload).encode()),
        ]
    )
    executor = _make_executor(transport)
    adapter = SpecDatasetAdapter("datago", [apt_spec, village_spec], executor)

    assert adapter.name == "datago"
    assert adapter.requires_api_key is True

    keys = {ref.dataset_key for ref in adapter.list_datasets()}
    assert keys == {"apt_trade", "village_fcst"}

    hits = adapter.search_datasets("예보")
    assert {ref.dataset_key for ref in hits} == {"village_fcst"}

    ref = adapter.get_dataset("apt_trade")
    assert ref.id == "datago.apt_trade"

    with pytest.raises(DatasetNotFoundError):
        adapter.get_dataset("nope")

    batch = adapter.query_records(ref, Query(page=1, page_size=10))
    assert len(batch.items) == 1

    raw = adapter.call_raw(ref, "raw", {"LAWD_CD": "11110"})
    assert isinstance(raw, dict) and "response" in raw


def test_spec_dataset_adapter_get_schema_is_none(apt_spec: SpecDefinition) -> None:
    """get_schema는 정직하게 None을 반환한다."""
    executor = _make_executor(FakeTransport())
    adapter = SpecDatasetAdapter("datago", [apt_spec], executor)
    assert adapter.get_schema(adapter.get_dataset("apt_trade")) is None
