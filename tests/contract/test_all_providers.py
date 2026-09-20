"""모든 Provider 어댑터의 공통 계약 테스트를 매개변수화하여 실행한다.

기존 개별 테스트 파일(test_bok.py, test_datago.py 등)에 중복되던
ProviderAdapterContract 테스트를 단일 파일에서 데이터 기반으로 실행한다.
Provider별 고유 설정만 _PROVIDER_CONFIGS 에 선언하면 된다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pandas as pd
import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.transport.http import HttpTransport
from tests.contract.provider_adapter import ProviderAdapterContract

# ---------------------------------------------------------------------------
# 공통 Fake 응답 / Transport 클래스
# ---------------------------------------------------------------------------


class _FakeResponse:
    """HTTP 응답을 흉내내는 테스트용 가짜 응답 객체."""

    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data
        self.text: str = data.decode("utf-8")


class _FixtureTransport:
    """미리 저장된 fixture 파일로 HTTP 요청을 흉내내는 테스트용 전송 계층."""

    def __init__(self, fixture_dir: Path, fixture_names: list[str]) -> None:
        self._responses: list[_FakeResponse] = [
            _FakeResponse((fixture_dir / name).read_bytes()) for name in fixture_names
        ]
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        """요청을 기록하고 다음 fixture 응답을 반환한다."""
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("fixture 응답이 남아있지 않다")
        return self._responses.pop(0)


# ---------------------------------------------------------------------------
# Provider 설정 데이터 클래스
# ---------------------------------------------------------------------------

_FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


@dataclass(frozen=True)
class ProviderConfig:
    """하나의 Provider 계약 테스트에 필요한 설정을 담는 데이터 클래스."""

    # 테스트 식별용 ID (pytest 출력에 표시)
    id: str
    # 어댑터를 생성하는 팩토리 함수
    adapter_factory: Callable[[], ProviderAdapter]
    # 유효/무효 데이터셋 키
    valid_dataset_key: str
    invalid_dataset_key: str
    # sample_query 생성 인자
    sample_query: Query
    # raw_operation (operation_name, params)
    raw_operation: tuple[str, dict[str, object]]


# ---------------------------------------------------------------------------
# Provider별 어댑터 팩토리 함수 정의
# ---------------------------------------------------------------------------


def _generic_adapter_factory(
    provider_name: str,
    module_path: str,
    class_name: str,
    fixture_dir_name: str,
    fixture_name: str,
    fixture_count: int = 5,
    provider_key_name: str | None = None,
    provider_key_value: str = "test-key",
) -> Callable[[], ProviderAdapter]:
    """대부분의 Provider에 사용할 수 있는 범용 어댑터 팩토리를 반환한다."""

    def factory() -> ProviderAdapter:
        fixture_dir = _FIXTURES_ROOT / fixture_dir_name
        transport = _FixtureTransport(fixture_dir, [fixture_name] * fixture_count)
        key_name = provider_key_name if provider_key_name is not None else provider_name
        config = KPubDataConfig(provider_keys={key_name: provider_key_value})
        module = import_module(module_path)
        adapter_cls = getattr(module, class_name)
        return cast(
            ProviderAdapter,
            adapter_cls(
                config=config,
                transport=cast(HttpTransport, cast(object, transport)),
            ),
        )

    return factory


def _krx_adapter_factory() -> ProviderAdapter:
    """KRX 어댑터는 pykrx 모킹이 필요하므로 별도 팩토리를 정의한다."""
    from kpubdata.providers.krx.adapter import KrxAdapter

    def _index_frame() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "시가": [2650.0],
                "고가": [2675.0],
                "저가": [2641.0],
                "종가": [2669.0],
                "거래량": [410000000],
                "거래대금": [8100000000000],
                "상장시가총액": [2100000000000],
            },
            index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
        )

    adapter = KrxAdapter(config=KPubDataConfig())
    adapter._pykrx = SimpleNamespace(
        stock=SimpleNamespace(
            get_index_ohlcv=lambda *_args: _index_frame(),
            get_market_trading_value_by_date=lambda *_args, **_kwargs: pd.DataFrame(
                {
                    "개인": [100],
                    "기관합계": [50],
                    "외국인합계": [30],
                    "기타법인": [20],
                    "전체": [0],
                },
                index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
            ),
            get_market_fundamental=lambda *_args, **_kwargs: pd.DataFrame(
                {
                    "PER": [150.0],
                    "PBR": [1.5],
                    "DIV": [3.0],
                    "EPS": [1500.0],
                    "BPS": [6000.0],
                },
                index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
            ),
        )
    )
    return adapter


def _sgis_adapter_factory() -> ProviderAdapter:
    """SGIS 어댑터는 auth_client 모킹이 필요하므로 별도 팩토리를 정의한다."""

    class _FakeAuthClient:
        """SGIS 인증 토큰을 흉내내는 가짜 클라이언트."""

        def get_access_token(self) -> str:
            return "fake-access-token"

    fixture_dir = _FIXTURES_ROOT / "sgis"
    transport = _FixtureTransport(fixture_dir, ["sido_boundary.geojson"] * 5)
    config = KPubDataConfig(provider_keys={"sgis": "consumer-key:consumer-secret"})
    module = import_module("kpubdata.providers.sgis.adapter")
    adapter_cls = module.SgisAdapter
    return cast(
        ProviderAdapter,
        adapter_cls(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
            auth_client=_FakeAuthClient(),
        ),
    )


def _localdata_adapter_factory() -> ProviderAdapter:
    """Localdata 어댑터는 대량의 fixture 파일이 필요하므로 별도 팩토리를 정의한다."""
    fixture_dir = _FIXTURES_ROOT / "localdata"
    # Localdata는 list_datasets 호출 시 모든 데이터셋에 대해 fixture가 필요함
    fixture_names = sorted(f.name for f in fixture_dir.glob("*_success.json"))
    transport = _FixtureTransport(fixture_dir, fixture_names)
    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    module = import_module("kpubdata.providers.localdata.adapter")
    adapter_cls = module.LocaldataAdapter
    return cast(
        ProviderAdapter,
        adapter_cls(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        ),
    )


# ---------------------------------------------------------------------------
# 전체 Provider 설정 목록
# ---------------------------------------------------------------------------

_PROVIDER_CONFIGS: list[ProviderConfig] = [
    # --- BOK ---
    ProviderConfig(
        id="bok",
        adapter_factory=_generic_adapter_factory(
            "bok",
            "kpubdata.providers.bok.adapter",
            "BokAdapter",
            "bok",
            "success_single_page.json",
        ),
        valid_dataset_key="base_rate",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(start_date="202401", end_date="202403"),
        raw_operation=(
            "StatisticSearch",
            {"start_date": "202401", "end_date": "202403", "frequency": "M"},
        ),
    ),
    # --- DataGo (기본 village_fcst) ---
    ProviderConfig(
        id="datago",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_single_page.json",
        ),
        valid_dataset_key="village_fcst",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(),
        raw_operation=("getVilageFcst", {}),
    ),
    # --- DataGo bond_price ---
    ProviderConfig(
        id="datago-bond_price",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_bond_price.json",
        ),
        valid_dataset_key="bond_price",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"basDt": "20260102"}),
        raw_operation=("getBondPriceInfo", {"basDt": "20260102", "page": 1, "page_size": 5}),
    ),
    # --- DataGo sports_facility ---
    ProviderConfig(
        id="datago-sports_facility",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_sports_facility.json",
        ),
        valid_dataset_key="sports_facility",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"sidoNm": "경기도"}),
        raw_operation=("TODZ_API_SFMS_FACI", {"sidoNm": "경기도", "page": 1, "page_size": 5}),
    ),
    # --- DataGo culture_facility ---
    ProviderConfig(
        id="datago-culture_facility",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_culture_facility.json",
        ),
        valid_dataset_key="culture_facility",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"faciCl": "공연장"}),
        raw_operation=("cultureartspaces/performingplace", {"page": 1, "page_size": 5}),
    ),
    # --- DataGo airkorea_station_realtime ---
    ProviderConfig(
        id="datago-airkorea_station_realtime",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_airkorea_station_realtime.json",
        ),
        valid_dataset_key="airkorea_station_realtime",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"stationName": "강남구"}),
        raw_operation=(
            "getMsrstnAcctoRltmMesureDnsty",
            {"stationName": "강남구", "page": 1, "page_size": 5},
        ),
    ),
    # --- DataGo airkorea_forecast ---
    ProviderConfig(
        id="datago-airkorea_forecast",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_airkorea_forecast.json",
        ),
        valid_dataset_key="airkorea_forecast",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"informCode": "PM10"}),
        raw_operation=("getMinuDustFrcstDspth", {"informCode": "PM10", "page": 1, "page_size": 5}),
    ),
    # --- DataGo asos_daily ---
    ProviderConfig(
        id="datago-asos_daily",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_asos_daily.json",
        ),
        valid_dataset_key="asos_daily",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(
            filters={"stnIds": "108", "startDt": "20260331", "endDt": "20260401"},
            page_size=10,
        ),
        raw_operation=(
            "getWthrDataList",
            {
                "stnIds": "108",
                "startDt": "20260331",
                "endDt": "20260401",
                "page": 1,
                "page_size": 5,
            },
        ),
    ),
    # --- DataGo asos_hourly ---
    ProviderConfig(
        id="datago-asos_hourly",
        adapter_factory=_generic_adapter_factory(
            "datago",
            "kpubdata.providers.datago.adapter",
            "DataGoAdapter",
            "datago",
            "success_asos_hourly.json",
        ),
        valid_dataset_key="asos_hourly",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(
            filters={"stnIds": "108", "startDt": "20260401", "endDt": "20260401"},
            page_size=10,
        ),
        raw_operation=(
            "getWthrDataList",
            {
                "stnIds": "108",
                "startDt": "20260401",
                "endDt": "20260401",
                "page": 1,
                "page_size": 5,
            },
        ),
    ),
    # --- KOSIS ---
    ProviderConfig(
        id="kosis",
        adapter_factory=_generic_adapter_factory(
            "kosis",
            "kpubdata.providers.kosis.adapter",
            "KosisAdapter",
            "kosis",
            "success_single_page.json",
        ),
        valid_dataset_key="population_migration",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(start_date="202401", end_date="202401"),
        raw_operation=("statisticsParameterData", {}),
    ),
    # --- Seoul (subway_realtime_arrival) ---
    ProviderConfig(
        id="seoul",
        adapter_factory=_generic_adapter_factory(
            "seoul",
            "kpubdata.providers.seoul.adapter",
            "SeoulAdapter",
            "seoul",
            "subway_realtime_arrival_success.json",
        ),
        valid_dataset_key="subway_realtime_arrival",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"stationName": "강남"}),
        raw_operation=(
            "realtimeStationArrival",
            {"stationName": "강남", "page_no": 1, "page_size": 5},
        ),
    ),
    # --- Seoul bike_realtime ---
    ProviderConfig(
        id="seoul-bike_realtime",
        adapter_factory=_generic_adapter_factory(
            "seoul",
            "kpubdata.providers.seoul.adapter",
            "SeoulAdapter",
            "seoul",
            "bike_realtime_success.json",
        ),
        valid_dataset_key="bike_realtime",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(),
        raw_operation=("bikeList", {"page_no": 1, "page_size": 5}),
    ),
    # --- Seoul bike_station_master ---
    ProviderConfig(
        id="seoul-bike_station_master",
        adapter_factory=_generic_adapter_factory(
            "seoul",
            "kpubdata.providers.seoul.adapter",
            "SeoulAdapter",
            "seoul",
            "bike_station_master_success.json",
        ),
        valid_dataset_key="bike_station_master",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(),
        raw_operation=("tbCycleStationInfo", {"page_no": 1, "page_size": 5}),
    ),
    # --- Seoul park_info ---
    ProviderConfig(
        id="seoul-park_info",
        adapter_factory=_generic_adapter_factory(
            "seoul",
            "kpubdata.providers.seoul.adapter",
            "SeoulAdapter",
            "seoul",
            "park_info.json",
        ),
        valid_dataset_key="park_info",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(),
        raw_operation=("GetParkInfo", {"page_no": 1, "page_size": 5}),
    ),
    # --- Seoul park_usage ---
    ProviderConfig(
        id="seoul-park_usage",
        adapter_factory=_generic_adapter_factory(
            "seoul",
            "kpubdata.providers.seoul.adapter",
            "SeoulAdapter",
            "seoul",
            "park_usage.json",
        ),
        valid_dataset_key="park_usage",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(),
        raw_operation=("SearchParkInfoService", {"page_no": 1, "page_size": 5}),
    ),
    # --- Seoul citydata ---
    ProviderConfig(
        id="seoul-citydata",
        adapter_factory=_generic_adapter_factory(
            "seoul",
            "kpubdata.providers.seoul.adapter",
            "SeoulAdapter",
            "seoul",
            "citydata.json",
        ),
        valid_dataset_key="citydata",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"area": "광화문·덕수궁"}, page_size=1),
        raw_operation=("citydata_ppltn", {"area": "광화문·덕수궁", "page_no": 1, "page_size": 1}),
    ),
    # --- KRX ---
    ProviderConfig(
        id="krx",
        adapter_factory=_krx_adapter_factory,
        valid_dataset_key="kospi_index",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(start_date="20240102", end_date="20240102"),
        raw_operation=("list", {"start_date": "20240102", "end_date": "20240102"}),
    ),
    # --- Law ---
    ProviderConfig(
        id="law",
        adapter_factory=_generic_adapter_factory(
            "law",
            "kpubdata.providers.law.adapter",
            "LawAdapter",
            "law",
            "success_law_search.json",
            provider_key_value="test-law-key",
        ),
        valid_dataset_key="law_search",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"query": "임대차", "search": "1"}),
        raw_operation=("lawSearch", {"query": "임대차", "search": "1"}),
    ),
    # --- Localdata ---
    ProviderConfig(
        id="localdata",
        adapter_factory=_localdata_adapter_factory,
        valid_dataset_key="general_restaurant",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(),
        raw_operation=("info", {"pageNo": "1", "numOfRows": "10"}),
    ),
    # --- LOFIN ---
    ProviderConfig(
        id="lofin",
        adapter_factory=_generic_adapter_factory(
            "lofin",
            "kpubdata.providers.lofin.adapter",
            "LofinAdapter",
            "lofin",
            "success_single_page.json",
            provider_key_name="datago",
        ),
        valid_dataset_key="expenditure_budget",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(),
        raw_operation=("list", {"pIndex": "1", "pSize": "10"}),
    ),
    # --- SEMAS ---
    ProviderConfig(
        id="semas",
        adapter_factory=_generic_adapter_factory(
            "semas",
            "kpubdata.providers.semas.adapter",
            "SemasAdapter",
            "semas",
            "store_one_success.json",
            fixture_count=2,
            provider_key_name="datago",
        ),
        valid_dataset_key="store_one",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"bizesId": "S001"}),
        raw_operation=("storeOne", {"bizesId": "S001"}),
    ),
    # --- SGIS ---
    ProviderConfig(
        id="sgis",
        adapter_factory=_sgis_adapter_factory,
        valid_dataset_key="boundary.sido",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"year": "2023", "low_search": 1}),
        raw_operation=("list", {"year": "2023", "low_search": 1}),
    ),
    # --- FDS ---
    ProviderConfig(
        id="fds",
        adapter_factory=_generic_adapter_factory(
            "fds",
            "kpubdata.providers.fds.adapter",
            "FdsAdapter",
            "fds",
            "traceability_item.json",
        ),
        valid_dataset_key="traceability_item",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(page_size=5),
        raw_operation=("I1200", {"start_idx": 1, "end_idx": 5}),
    ),
    # --- NEIS meal_diet ---
    ProviderConfig(
        id="neis-meal_diet",
        adapter_factory=_generic_adapter_factory(
            "neis",
            "kpubdata.providers.neis.adapter",
            "NeisAdapter",
            "neis",
            "meal_diet.json",
        ),
        valid_dataset_key="meal_diet",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(
            filters={"ATPT_OFCDC_SC_CODE": "B10", "SD_SCHUL_CODE": "7021108"},
            page_size=10,
        ),
        raw_operation=(
            "mealServiceDietInfo",
            {"ATPT_OFCDC_SC_CODE": "B10", "SD_SCHUL_CODE": "7021108", "pIndex": 1, "pSize": 5},
        ),
    ),
    # --- NEIS school_info ---
    ProviderConfig(
        id="neis-school_info",
        adapter_factory=_generic_adapter_factory(
            "neis",
            "kpubdata.providers.neis.adapter",
            "NeisAdapter",
            "neis",
            "school_info.json",
        ),
        valid_dataset_key="school_info",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"ATPT_OFCDC_SC_CODE": "B10"}, page_size=10),
        raw_operation=("schoolInfo", {"ATPT_OFCDC_SC_CODE": "B10", "pIndex": 1, "pSize": 5}),
    ),
    # --- Korean ---
    ProviderConfig(
        id="korean",
        adapter_factory=_generic_adapter_factory(
            "korean",
            "kpubdata.providers.korean.adapter",
            "KoreanAdapter",
            "korean",
            "dict_search.json",
        ),
        valid_dataset_key="dict_search",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"q": "나무"}, page_size=10),
        raw_operation=("search.do", {"q": "나무", "start": 1, "num": 5}),
    ),
    # --- KIPRIS ---
    ProviderConfig(
        id="kipris",
        adapter_factory=_generic_adapter_factory(
            "kipris",
            "kpubdata.providers.kipris.adapter",
            "KiprisAdapter",
            "kipris",
            "patent_family.json",
        ),
        valid_dataset_key="patent_family",
        invalid_dataset_key="nonexistent_dataset_key_xyz",
        sample_query=Query(filters={"applicationNumber": "1020050082226"}, page_size=10),
        raw_operation=("getAppNoPatFamInfoSearch", {"applicationNumber": "1020050082226"}),
    ),
]


# ---------------------------------------------------------------------------
# 매개변수화된 계약 테스트 클래스
# ---------------------------------------------------------------------------


class TestAllProvidersContract(ProviderAdapterContract):
    """모든 Provider 어댑터에 대해 공통 계약 테스트를 매개변수화하여 실행한다.

    _PROVIDER_CONFIGS 에 정의된 각 Provider 설정별로 동일한 계약 테스트 세트가
    자동으로 실행된다.
    """

    @pytest.fixture(
        params=_PROVIDER_CONFIGS,
        ids=[cfg.id for cfg in _PROVIDER_CONFIGS],
    )
    def _provider_config(self, request: pytest.FixtureRequest) -> ProviderConfig:
        """매개변수화된 Provider 설정을 반환한다."""
        return request.param  # type: ignore[no-any-return]

    @pytest.fixture()
    def adapter(self, _provider_config: ProviderConfig) -> ProviderAdapter:
        """Provider 설정에 따라 어댑터를 생성한다."""
        return _provider_config.adapter_factory()

    @pytest.fixture()
    def valid_dataset_key(self, _provider_config: ProviderConfig) -> str:
        """유효한 데이터셋 키를 반환한다."""
        return _provider_config.valid_dataset_key

    @pytest.fixture()
    def invalid_dataset_key(self, _provider_config: ProviderConfig) -> str:
        """무효한 데이터셋 키를 반환한다."""
        return _provider_config.invalid_dataset_key

    @pytest.fixture()
    def sample_dataset(
        self, adapter: ProviderAdapter, _provider_config: ProviderConfig
    ) -> DatasetRef:
        """테스트용 데이터셋 참조를 반환한다."""
        return adapter.get_dataset(_provider_config.valid_dataset_key)

    @pytest.fixture()
    def sample_query(self, _provider_config: ProviderConfig) -> Query:
        """테스트용 쿼리를 반환한다."""
        return _provider_config.sample_query

    @pytest.fixture()
    def raw_operation(self, _provider_config: ProviderConfig) -> tuple[str, dict[str, object]]:
        """테스트용 raw 오퍼레이션을 반환한다."""
        return _provider_config.raw_operation
