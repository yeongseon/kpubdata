"""Client.dataset(key).list(**params).items 소비자 계약 테스트.

이 테스트는 kpubdata-builder와 같은 소비자가 의존하는 핵심 계약을 검증합니다:
- Client.dataset(key).list(**params).items 속성이 존재하는지
- items가 반복 가능한지
- 각 항목이 dict 형태인지
- keyword fetch parameter가 adapter/transport 계층까지 전달되는지
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import httpx

from kpubdata import Client
from kpubdata.core.models import RecordBatch


def _fixture_path(name: str) -> Path:
    """
    내부 헬퍼로서 fixture path 처리를 담당한다.
    """
    return Path(__file__).resolve().parents[1] / "fixtures" / "datago" / name


def _load_fixture_bytes(name: str) -> bytes:
    """
    내부 헬퍼로서 load fixture bytes 처리를 담당한다.
    """
    return _fixture_path(name).read_bytes()


def _build_mock_response(fixture_name: str) -> httpx.Response:
    """
    fixture 데이터로부터 httpx.Response를 생성한다.
    """
    data = _load_fixture_bytes(fixture_name)
    return httpx.Response(
        status_code=200,
        content=data,
        request=httpx.Request("GET", "http://example.com"),
    )


class TestClientDatasetListContract:
    """
    Client.dataset(key).list(**params).items 계약 검증 테스트.

    kpubdata-builder와 같은 소비자가 의존하는 핵심 계약을 검증합니다:
    1. items 속성이 존재하고 반복 가능한지
    2. 각 item이 dict 형태인지
    3. keyword parameter가 adapter 계층까지 전달되는지
    """

    @patch("httpx.Client.request")
    def test_list_returns_record_batch(self, mock_request: Mock) -> None:
        """
        dataset.list()가 RecordBatch 객체를 반환하는지 검증한다.
        """
        mock_request.return_value = _build_mock_response("success_single_page.json")
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.village_fcst")
        batch = dataset.list()

        # RecordBatch 타입인지 확인
        assert isinstance(batch, RecordBatch)
        assert batch.dataset is not None

    @patch("httpx.Client.request")
    def test_list_items_attribute_exists(self, mock_request: Mock) -> None:
        """
        Client.dataset(key).list(**params).items 속성이 존재하는지 검증한다.
        """
        mock_request.return_value = _build_mock_response("success_single_page.json")
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.village_fcst")
        batch = dataset.list()

        # items 속성이 존재하는지 확인
        assert hasattr(batch, "items")
        assert batch.items is not None

    @patch("httpx.Client.request")
    def test_list_items_is_iterable(self, mock_request: Mock) -> None:
        """
        items 속성이 반복 가능한지 검증한다.
        """
        mock_request.return_value = _build_mock_response("success_single_page.json")
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.village_fcst")
        batch = dataset.list()

        # items를 반복할 수 있는지 확인
        item_count = 0
        for _item in batch.items:
            item_count += 1

        assert item_count > 0

    @patch("httpx.Client.request")
    def test_list_items_are_dicts(self, mock_request: Mock) -> None:
        """
        items의 각 항목이 dict 형태인지 검증한다.
        """
        mock_request.return_value = _build_mock_response("success_single_page.json")
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.village_fcst")
        batch = dataset.list()

        # 모든 item이 dict인지 확인
        for item in batch.items:
            assert isinstance(item, dict), f"Expected dict, got {type(item)}"

    @patch("httpx.Client.request")
    def test_list_items_with_filter_parameters(self, mock_request: Mock) -> None:
        """
        keyword filter parameter가 transport 계층까지 전달되는지 검증한다.
        """
        mock_request.return_value = _build_mock_response("success_single_page.json")
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.village_fcst")

        # keyword parameter를 전달하여 호출
        batch = dataset.list(page=1, page_size=10)

        # 결과가 정상적으로 반환되는지 확인
        assert batch is not None
        assert hasattr(batch, "items")
        assert isinstance(batch.items, list)

        # HTTP 호출이 있었는지 확인
        assert mock_request.called
        assert mock_request.call_count >= 1

        # HTTP 요청의 실제 파라미터를 검증
        call_args = mock_request.call_args
        assert call_args is not None

        # httpx.request의 params 인자를 추출
        params = call_args.kwargs.get("params")
        assert params is not None, "HTTP 요청에 params가 전달되지 않음"

        # DataGo adapter는 canonical 'page'를 'pageNo'로 변환
        assert "pageNo" in params, "pageNo 파라미터가 요청에 없음"
        assert params["pageNo"] == "1", "pageNo 값이 1이어야 함"

        # DataGo adapter는 canonical 'page_size'를 'numOfRows'로 변환
        assert "numOfRows" in params, "numOfRows 파라미터가 요청에 없음"
        assert params["numOfRows"] == "10", "numOfRows 값이 10이어야 함"

    @patch("httpx.Client.request")
    def test_list_items_with_empty_result(self, mock_request: Mock) -> None:
        """
        빈 결과에서도 items 계약이 지켜지는지 검증한다.
        """
        mock_request.return_value = _build_mock_response("success_empty.json")
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.village_fcst")
        batch = dataset.list()

        # 빈 결과에서도 items 계약이 지켜지는지 확인
        assert hasattr(batch, "items")
        assert isinstance(batch.items, list)
        assert len(batch.items) == 0

    @patch("httpx.Client.request")
    def test_list_items_representative_dataset_contract(self, mock_request: Mock) -> None:
        """
        대표 dataset에서 items 속성이 일관되게 동작하는지 검증한다.
        """
        mock_request.return_value = _build_mock_response("success_single_page.json")
        client = Client(provider_keys={"datago": "test-key"}, cache=False)

        # 대표 dataset이 계약을 준수하는지 확인
        dataset_key = "datago.village_fcst"
        dataset = client.dataset(dataset_key)
        batch = dataset.list()

        # items 계약이 지켜지는지 확인
        assert hasattr(batch, "items"), f"Dataset {dataset_key} missing items attribute"
        assert isinstance(batch.items, list), f"Dataset {dataset_key} items is not a list"

        for item in batch.items:
            assert isinstance(item, dict), f"Dataset {dataset_key} has non-dict item"
