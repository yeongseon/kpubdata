from __future__ import annotations

import json
import logging
from pathlib import Path
from types import MappingProxyType
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import AuthError, ProviderResponseError
from kpubdata.providers.localdata.adapter import LocaldataAdapter
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "localdata" / name


def _load_fixture(name: str) -> dict[str, object]:
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload)
        self.content: bytes = self.text.encode()


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


def _build_adapter_with_transport(
    responses: list[FakeResponse],
) -> tuple[LocaldataAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = LocaldataAdapter(
        config=KPubDataConfig(provider_keys={"localdata": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("general_restaurant")
    return adapter, dataset, transport


def _build_dataset_adapter_with_transport(
    dataset_key: str,
    responses: list[FakeResponse],
) -> tuple[LocaldataAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = LocaldataAdapter(
        config=KPubDataConfig(provider_keys={"localdata": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset, transport


def test_query_records_parses_success_fixture() -> None:
    payload = _load_fixture("general_restaurant_success.json")
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.next_page is None
    assert batch.raw == payload
    assert batch.items[0]["BPLC_NM"] == "한밥식당"
    assert len(transport.calls) == 1


def test_query_records_raises_auth_error_on_auth_fixture() -> None:
    payload = _load_fixture("error_auth.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    try:
        _ = adapter.query_records(dataset, Query())
    except AuthError as exc_info:
        assert exc_info.provider_code == "30"
        return

    raise AssertionError("AuthError was not raised")


def test_query_records_handles_empty_response() -> None:
    payload = _load_fixture("empty_response.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    assert batch.total_count is None
    assert batch.next_page is None


def test_query_records_handles_empty_response_logs_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    payload = _load_fixture("empty_response.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.localdata")
    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Localdata envelope: zero items"
    )
    assert record.__dict__["dataset_id"] == dataset.id
    assert record.__dict__["page"] == 1
    assert record.__dict__["page_size"] == 100
    assert record.__dict__["total_count"] == 0


def test_query_records_sets_next_page_with_total_count() -> None:
    payload = _load_fixture("general_restaurant_success.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.next_page == 2


def test_query_records_passes_local_code_filter() -> None:
    payload = _load_fixture("general_restaurant_success.json")
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    _ = adapter.query_records(dataset, Query(filters={"localCode": "41135"}))

    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["serviceKey"] == "test-key"
    assert request_params["type"] == "json"
    assert request_params["pageNo"] == "1"
    assert request_params["numOfRows"] == "100"
    assert request_params["localCode"] == "41135"


def test_rest_cafe_query_records_parses_success_fixture() -> None:
    payload = _load_fixture("rest_cafe_success.json")
    adapter, dataset, _ = _build_dataset_adapter_with_transport(
        "rest_cafe", [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[0]["BPLC_NM"] == "카페모카"


def test_adapter_lists_all_datasets() -> None:
    adapter = LocaldataAdapter(config=KPubDataConfig(provider_keys={"localdata": "test-key"}))

    datasets = adapter.list_datasets()

    assert len(datasets) == 195
    assert [dataset.dataset_key for dataset in datasets] == [
        "general_restaurant",
        "rest_cafe",
        "bakery",
        "hospital",
        "clinic",
        "pharmacy",
        "animal_hospital",
        "optical_shop",
        "public_bath",
        "laundry",
        "barber_shop",
        "beauty_salon",
        "pet_grooming",
        "dance_academy",
        "karaoke",
        "singing_bar",
        "billiard_hall",
        "performance_hall",
        "movie_theater",
        "swimming_pool",
        "fitness_center",
        "ice_rink",
        "golf_course",
        "golf_practice_range",
        "horse_riding",
        "ski_resort",
        "affiliated_medical_institution",
        "postpartum_care",
        "safe_over_the_counter_drug_store",
        "emergency_patient_transport",
        "medical_foundation",
        "quasi_medical_business",
        "medical_device_repair",
        "dental_lab",
        "medical_device_sales",
        "animal_breeding",
        "animal_import",
        "animal_care_service",
        "animal_transport",
        "animal_funeral",
        "animal_exhibition",
        "animal_sales",
        "animal_crematorium",
        "animal_training",
        "companion_animal_related_business",
        "livestock_farming",
        "livestock_artificial_insemination_center",
        "slaughterhouse",
        "hatchery",
        "feed_manufacturing",
        "breeding_stock",
        "game_distribution",
        "game_manufacturing",
        "game_provider",
        "composite_game_provider",
        "internet_computer_game_facility",
        "youth_game_provider",
        "electronic_distribution",
        "tourist_performance_hall",
        "tourist_theater_entertainment",
        "tourist_track",
        "tourism_business",
        "tourist_excursion_boat",
        "tourism_convenience_facility",
        "international_conference_facility",
        "foreign_tourist_city_homestay",
        "amusement_facility",
        "general_amusement_facility",
        "comprehensive_amusement_facility",
        "comprehensive_resort_business",
        "specialized_resort_business",
        "hanok_experience",
        "tourism_duty_free",
        "international_conference_planning",
        "popular_culture_arts_planning",
        "culture_industry_company",
        "video_viewing_room",
        "video_distribution",
        "video_small_theater",
        "video_viewing_service",
        "video_production",
        "tourist_accommodation",
        "tourist_pension",
        "rural_guesthouse",
        "small_hotel",
        "foreign_tourist_city_homestay_lodging",
        "general_lodging",
        "hanok_experience_lodging",
        "residential_accommodation",
        "domestic_travel",
        "domestic_international_travel",
        "comprehensive_travel",
        "movie_distribution",
        "movie_screening",
        "movie_import",
        "movie_production",
        "online_music_service",
        "record_distribution",
        "record_production",
        "music_video_distribution",
        "music_video_production",
        "medical_linen_processing",
        "multilevel_sales",
        "large_store",
        "door_to_door_sales",
        "prepaid_installment_trade",
        "ecommerce",
        "mail_order_sales",
        "dance_hall",
        "yacht_marina",
        "motor_racing_course",
        "comprehensive_sports_facility",
        "martial_arts_gym",
        "boxing_gym",
        "contract_foodservice",
        "group_cafeteria",
        "health_functional_food_retail",
        "health_functional_food_specialty",
        "health_functional_food_distributor",
        "food_cold_storage",
        "food_repackaging",
        "food_transportation",
        "food_vending_machine",
        "food_manufacturing",
        "food_additive_manufacturing",
        "edible_ice_sales",
        "onggi_manufacturing",
        "distribution_specialized_sales",
        "instant_food_manufacturing",
        "milk_collection",
        "livestock_processing",
        "livestock_storage",
        "livestock_transportation",
        "livestock_sales",
        "imported_livestock_sales",
        "container_packaging_manufacturing",
        "other_food_sales",
        "imported_food_sales",
        "entertainment_bar",
        "tourist_restaurant",
        "foreigner_exclusive_entertainment_restaurant",
        "tourist_entertainment_restaurant",
        "timber_import_distribution",
        "log_production",
        "sawmill",
        "meter_repair",
        "high_pressure_gas",
        "petroleum_sales",
        "petroleum_import_export",
        "energy_saving_company",
        "lpg_charging",
        "lpg_collective_supply",
        "lpg_sales",
        "electrical_construction",
        "electrical_safety_management_agency",
        "electricity_sales",
        "city_gas",
        "gas_appliance_manufacturing",
        "groundwater_construction",
        "groundwater_impact_assessment",
        "groundwater_purification",
        "building_sanitation_management",
        "water_tank_cleaning",
        "disinfection_business",
        "sanitary_product_manufacturing",
        "sanitation_treatment",
        "waste_treatment",
        "waste_collection_transportation",
        "night_soil_collection_transportation",
        "environmental_measurement_agency",
        "environmental_impact_assessment",
        "air_pollution_prevention_facility",
        "water_pollution_prevention_facility",
        "soil_remediation",
        "noise_vibration_prevention_facility",
        "waste_recycling",
        "medical_waste_treatment",
        "marine_environment_management",
        "environmental_consulting",
        "outdoor_advertising",
        "printing_house",
        "publisher",
        "tobacco_wholesale",
        "tobacco_retail",
        "tobacco_import_sales",
        "international_freight_forwarding",
        "logistics_warehouse",
        "civil_defense_water_supply",
        "funeral_service",
        "elevator_maintenance",
        "elevator_manufacturing_import",
        "caregiver_training_institution",
        "funeral_director_training_institution",
        "free_job_placement",
        "paid_job_placement",
    ]


def test_build_request_url_missing_base_url_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    adapter, dataset, _ = _build_adapter_with_transport([])
    dataset = DatasetRef(
        id=dataset.id,
        provider=dataset.provider,
        dataset_key=dataset.dataset_key,
        name=dataset.name,
        representation=dataset.representation,
        operations=dataset.operations,
        raw_metadata=MappingProxyType(
            {k: v for k, v in dataset.raw_metadata.items() if k != "base_url"}
        ),
        query_support=dataset.query_support,
    )

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.localdata")
    with pytest.raises(ProviderResponseError, match="base_url"):
        _ = adapter.query_records(dataset, Query())

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Localdata dataset metadata missing base_url"
    )
    assert record.__dict__["dataset_id"] == dataset.id


# --- New dataset fixture parsing tests ---


_NEW_DATASETS = [
    ("bakery", "bakery_success.json", "중앙베이커리"),
    ("hospital", "hospital_success.json", "중앙내과의원"),
    ("clinic", "clinic_success.json", "대흥가정의원"),
    ("pharmacy", "pharmacy_success.json", "중앙약국"),
    ("animal_hospital", "animal_hospital_success.json", "중앙24시동물병원"),
    ("optical_shop", "optical_shop_success.json", "선화안경원"),
    ("public_bath", "public_bath_success.json", "중앙대중목욕탕"),
    ("laundry", "laundry_success.json", "깨끗한세탁소"),
    ("barber_shop", "barber_shop_success.json", "클래식이발관"),
    ("beauty_salon", "beauty_salon_success.json", "뷰티헤어살롱"),
    ("pet_grooming", "pet_grooming_success.json", "멍멍살롱중앙점"),
    ("dance_academy", "dance_academy_success.json", "대전리듬댄스학원"),
    ("karaoke", "karaoke_success.json", "노래천국"),
    ("singing_bar", "singing_bar_success.json", "은행스타유흥주점"),
    ("billiard_hall", "billiard_hall_success.json", "유천당구클럽"),
    ("performance_hall", "performance_hall_success.json", "중앙소극장"),
    ("movie_theater", "movie_theater_success.json", "중앙시네마"),
    ("swimming_pool", "swimming_pool_success.json", "산성아쿠아센터"),
    ("fitness_center", "fitness_center_success.json", "태평피트니스클럽"),
    ("ice_rink", "ice_rink_success.json", "대전아이스링크"),
    ("golf_course", "golf_course_success.json", "대전힐즈골프장"),
    ("golf_practice_range", "golf_practice_range_success.json", "문화스크린골프연습장"),
    ("horse_riding", "horse_riding_success.json", "보문승마클럽"),
    ("ski_resort", "ski_resort_success.json", "대전스노우리조트"),
    (
        "affiliated_medical_institution",
        "affiliated_medical_institution_success.json",
        "중앙부속의료기관",
    ),
    ("postpartum_care", "postpartum_care_success.json", "중앙산후조리업"),
    (
        "safe_over_the_counter_drug_store",
        "safe_over_the_counter_drug_store_success.json",
        "중앙안전상비의약품판매업소",
    ),
    (
        "emergency_patient_transport",
        "emergency_patient_transport_success.json",
        "중앙응급환자이송업",
    ),
    ("medical_foundation", "medical_foundation_success.json", "중앙의료법인"),
    ("quasi_medical_business", "quasi_medical_business_success.json", "중앙의료유사업"),
    ("medical_device_repair", "medical_device_repair_success.json", "중앙의료기기수리업"),
    ("dental_lab", "dental_lab_success.json", "중앙치과기공소"),
    ("medical_device_sales", "medical_device_sales_success.json", "중앙의료기기판매업"),
    ("animal_breeding", "animal_breeding_success.json", "중앙동물생산업"),
    ("animal_import", "animal_import_success.json", "중앙동물수입업"),
    ("animal_care_service", "animal_care_service_success.json", "중앙동물위탁관리업"),
    ("animal_transport", "animal_transport_success.json", "중앙동물운송업"),
    ("animal_funeral", "animal_funeral_success.json", "중앙동물장묘업"),
    ("animal_exhibition", "animal_exhibition_success.json", "중앙동물전시업"),
    ("animal_sales", "animal_sales_success.json", "중앙동물판매업"),
    ("animal_crematorium", "animal_crematorium_success.json", "중앙동물화장장업"),
    ("animal_training", "animal_training_success.json", "중앙동물훈련업"),
    (
        "companion_animal_related_business",
        "companion_animal_related_business_success.json",
        "중앙반려동물관련업",
    ),
    ("livestock_farming", "livestock_farming_success.json", "중앙가축사육업"),
    (
        "livestock_artificial_insemination_center",
        "livestock_artificial_insemination_center_success.json",
        "중앙가축인공수정소",
    ),
    ("slaughterhouse", "slaughterhouse_success.json", "중앙도축업"),
    ("hatchery", "hatchery_success.json", "중앙부화업"),
    ("feed_manufacturing", "feed_manufacturing_success.json", "중앙사료제조업"),
    ("breeding_stock", "breeding_stock_success.json", "중앙종축업"),
    ("game_distribution", "game_distribution_success.json", "중앙게임물배급업"),
    ("game_manufacturing", "game_manufacturing_success.json", "중앙게임물제작업"),
    ("game_provider", "game_provider_success.json", "중앙게임제공업"),
    ("composite_game_provider", "composite_game_provider_success.json", "중앙복합유통게임제공업"),
    (
        "internet_computer_game_facility",
        "internet_computer_game_facility_success.json",
        "중앙인터넷컴퓨터게임시설제공업",
    ),
    ("youth_game_provider", "youth_game_provider_success.json", "중앙청소년게임제공업"),
    ("electronic_distribution", "electronic_distribution_success.json", "중앙전자유통배급업"),
    ("tourist_performance_hall", "tourist_performance_hall_success.json", "중앙관광공연장업"),
    (
        "tourist_theater_entertainment",
        "tourist_theater_entertainment_success.json",
        "중앙관광극장유흥업",
    ),
    ("tourist_track", "tourist_track_success.json", "중앙관광궤도업"),
    ("tourism_business", "tourism_business_success.json", "중앙관광사업자"),
    ("tourist_excursion_boat", "tourist_excursion_boat_success.json", "중앙관광유람선업"),
    (
        "tourism_convenience_facility",
        "tourism_convenience_facility_success.json",
        "중앙관광편의시설업",
    ),
    (
        "international_conference_facility",
        "international_conference_facility_success.json",
        "중앙국제회의시설업",
    ),
    (
        "foreign_tourist_city_homestay",
        "foreign_tourist_city_homestay_success.json",
        "중앙외국인관광도시민박업",
    ),
    ("amusement_facility", "amusement_facility_success.json", "중앙유원시설업"),
    ("general_amusement_facility", "general_amusement_facility_success.json", "중앙일반유원시설업"),
    (
        "comprehensive_amusement_facility",
        "comprehensive_amusement_facility_success.json",
        "중앙종합유원시설업",
    ),
    (
        "comprehensive_resort_business",
        "comprehensive_resort_business_success.json",
        "중앙종합휴양업",
    ),
    ("specialized_resort_business", "specialized_resort_business_success.json", "중앙전문휴양업"),
    ("hanok_experience", "hanok_experience_success.json", "중앙한옥체험업"),
    ("tourism_duty_free", "tourism_duty_free_success.json", "중앙관광면세업"),
    (
        "international_conference_planning",
        "international_conference_planning_success.json",
        "중앙국제회의기획업",
    ),
    (
        "popular_culture_arts_planning",
        "popular_culture_arts_planning_success.json",
        "중앙대중문화예술기획업",
    ),
    ("culture_industry_company", "culture_industry_company_success.json", "중앙문화산업전문회사"),
    ("video_viewing_room", "video_viewing_room_success.json", "중앙비디오물감상실업"),
    ("video_distribution", "video_distribution_success.json", "중앙비디오물배급업"),
    ("video_small_theater", "video_small_theater_success.json", "중앙비디오물소극장업"),
    ("video_viewing_service", "video_viewing_service_success.json", "중앙비디오물시청제공업"),
    ("video_production", "video_production_success.json", "중앙비디오물제작업"),
    ("tourist_accommodation", "tourist_accommodation_success.json", "중앙관광숙박업"),
    ("tourist_pension", "tourist_pension_success.json", "중앙관광펜션업"),
    ("rural_guesthouse", "rural_guesthouse_success.json", "중앙농어촌민박업"),
    ("small_hotel", "small_hotel_success.json", "중앙소형호텔업"),
    (
        "foreign_tourist_city_homestay_lodging",
        "foreign_tourist_city_homestay_lodging_success.json",
        "중앙외국인관광도시민박업숙박",
    ),
    ("general_lodging", "general_lodging_success.json", "중앙일반숙박업"),
    ("hanok_experience_lodging", "hanok_experience_lodging_success.json", "중앙한옥체험업숙박"),
    ("residential_accommodation", "residential_accommodation_success.json", "중앙생활숙박업"),
    ("domestic_travel", "domestic_travel_success.json", "중앙국내여행업"),
    (
        "domestic_international_travel",
        "domestic_international_travel_success.json",
        "중앙국내외여행업",
    ),
    ("comprehensive_travel", "comprehensive_travel_success.json", "중앙종합여행업"),
    ("movie_distribution", "movie_distribution_success.json", "중앙영화배급업"),
    ("movie_screening", "movie_screening_success.json", "중앙영화상영업"),
    ("movie_import", "movie_import_success.json", "중앙영화수입업"),
    ("movie_production", "movie_production_success.json", "중앙영화제작업"),
    ("online_music_service", "online_music_service_success.json", "중앙온라인음악서비스제공업"),
    ("record_distribution", "record_distribution_success.json", "중앙음반물배급업"),
    ("record_production", "record_production_success.json", "중앙음반물제작업"),
    ("music_video_distribution", "music_video_distribution_success.json", "중앙음악영상물배급업"),
    ("music_video_production", "music_video_production_success.json", "중앙음악영상물제작업"),
    (
        "medical_linen_processing",
        "medical_linen_processing_success.json",
        "중앙의료기관세탁물처리업",
    ),
    ("multilevel_sales", "multilevel_sales_success.json", "중앙다단계판매업체"),
    ("large_store", "large_store_success.json", "중앙대규모점포"),
    ("door_to_door_sales", "door_to_door_sales_success.json", "중앙방문판매업"),
    ("prepaid_installment_trade", "prepaid_installment_trade_success.json", "중앙선불식할부거래업"),
    ("ecommerce", "ecommerce_success.json", "중앙전자상거래업"),
    ("mail_order_sales", "mail_order_sales_success.json", "중앙통신판매업"),
    ("dance_hall", "dance_hall_success.json", "중앙무도장업"),
    ("yacht_marina", "yacht_marina_success.json", "중앙요트장업"),
    ("motor_racing_course", "motor_racing_course_success.json", "중앙자동차경주장업"),
    (
        "comprehensive_sports_facility",
        "comprehensive_sports_facility_success.json",
        "중앙종합체육시설업",
    ),
    ("martial_arts_gym", "martial_arts_gym_success.json", "중앙체육도장업"),
    ("boxing_gym", "boxing_gym_success.json", "중앙권투전용체육시설"),
    ("contract_foodservice", "contract_foodservice_success.json", "중앙위탁급식영업"),
    ("group_cafeteria", "group_cafeteria_success.json", "중앙집단급식소"),
    (
        "health_functional_food_retail",
        "health_functional_food_retail_success.json",
        "중앙건강기능식품일반판매업",
    ),
    (
        "health_functional_food_specialty",
        "health_functional_food_specialty_success.json",
        "중앙건강기능식품전문판매업",
    ),
    (
        "health_functional_food_distributor",
        "health_functional_food_distributor_success.json",
        "중앙건강기능식품유통전문판매업",
    ),
    ("food_cold_storage", "food_cold_storage_success.json", "중앙식품냉동냉장업"),
    ("food_repackaging", "food_repackaging_success.json", "중앙식품소분업"),
    ("food_transportation", "food_transportation_success.json", "중앙식품운반업"),
    ("food_vending_machine", "food_vending_machine_success.json", "중앙식품자동판매기영업"),
    ("food_manufacturing", "food_manufacturing_success.json", "중앙식품제조가공업"),
    (
        "food_additive_manufacturing",
        "food_additive_manufacturing_success.json",
        "중앙식품첨가물제조업",
    ),
    ("edible_ice_sales", "edible_ice_sales_success.json", "중앙식용얼음판매업"),
    ("onggi_manufacturing", "onggi_manufacturing_success.json", "중앙옹기류제조업"),
    (
        "distribution_specialized_sales",
        "distribution_specialized_sales_success.json",
        "중앙유통전문판매업",
    ),
    (
        "instant_food_manufacturing",
        "instant_food_manufacturing_success.json",
        "중앙즉석판매제조가공업",
    ),
    ("milk_collection", "milk_collection_success.json", "중앙집유업"),
    ("livestock_processing", "livestock_processing_success.json", "중앙축산물가공업"),
    ("livestock_storage", "livestock_storage_success.json", "중앙축산물보관업"),
    ("livestock_transportation", "livestock_transportation_success.json", "중앙축산물운반업"),
    ("livestock_sales", "livestock_sales_success.json", "중앙축산물판매업"),
    ("imported_livestock_sales", "imported_livestock_sales_success.json", "중앙축산물수입판매업"),
    (
        "container_packaging_manufacturing",
        "container_packaging_manufacturing_success.json",
        "중앙용기포장류제조업",
    ),
    ("other_food_sales", "other_food_sales_success.json", "중앙기타식품판매업"),
    ("imported_food_sales", "imported_food_sales_success.json", "중앙식품등수입판매업"),
    ("entertainment_bar", "entertainment_bar_success.json", "중앙유흥주점영업"),
    ("tourist_restaurant", "tourist_restaurant_success.json", "중앙관광식당"),
    (
        "foreigner_exclusive_entertainment_restaurant",
        "foreigner_exclusive_entertainment_restaurant_success.json",
        "중앙외국인전용유흥음식점업",
    ),
    (
        "tourist_entertainment_restaurant",
        "tourist_entertainment_restaurant_success.json",
        "중앙관광유흥음식점업",
    ),
    ("timber_import_distribution", "timber_import_distribution_success.json", "중앙목재수입유통업"),
    ("log_production", "log_production_success.json", "중앙원목생산업"),
    ("sawmill", "sawmill_success.json", "중앙제재업"),
    ("meter_repair", "meter_repair_success.json", "중앙계량기수리업"),
    ("high_pressure_gas", "high_pressure_gas_success.json", "중앙고압가스업"),
    ("petroleum_sales", "petroleum_sales_success.json", "중앙석유판매업"),
    ("petroleum_import_export", "petroleum_import_export_success.json", "중앙석유수출입업"),
    ("energy_saving_company", "energy_saving_company_success.json", "중앙에너지절약전문기업"),
    ("lpg_charging", "lpg_charging_success.json", "중앙액화석유가스충전사업"),
    ("lpg_collective_supply", "lpg_collective_supply_success.json", "중앙액화석유가스집단공급사업"),
    ("lpg_sales", "lpg_sales_success.json", "중앙액화석유가스판매사업"),
    ("electrical_construction", "electrical_construction_success.json", "중앙전기공사업"),
    (
        "electrical_safety_management_agency",
        "electrical_safety_management_agency_success.json",
        "중앙전기안전관리대행사업",
    ),
    ("electricity_sales", "electricity_sales_success.json", "중앙전기판매사업"),
    ("city_gas", "city_gas_success.json", "중앙도시가스사업"),
    (
        "gas_appliance_manufacturing",
        "gas_appliance_manufacturing_success.json",
        "중앙가스용품제조사업",
    ),
    ("groundwater_construction", "groundwater_construction_success.json", "중앙지하수시공업체"),
    (
        "groundwater_impact_assessment",
        "groundwater_impact_assessment_success.json",
        "중앙지하수영향조사기관",
    ),
    ("groundwater_purification", "groundwater_purification_success.json", "중앙지하수정화업체"),
    (
        "building_sanitation_management",
        "building_sanitation_management_success.json",
        "중앙건물위생관리업",
    ),
    ("water_tank_cleaning", "water_tank_cleaning_success.json", "중앙저수조청소업"),
    ("disinfection_business", "disinfection_business_success.json", "중앙소독업"),
    (
        "sanitary_product_manufacturing",
        "sanitary_product_manufacturing_success.json",
        "중앙위생용품제조업",
    ),
    ("sanitation_treatment", "sanitation_treatment_success.json", "중앙위생처리업"),
    ("waste_treatment", "waste_treatment_success.json", "중앙폐기물처리업"),
    (
        "waste_collection_transportation",
        "waste_collection_transportation_success.json",
        "중앙폐기물수집운반업",
    ),
    (
        "night_soil_collection_transportation",
        "night_soil_collection_transportation_success.json",
        "중앙분뇨수집운반업",
    ),
    (
        "environmental_measurement_agency",
        "environmental_measurement_agency_success.json",
        "중앙환경측정대행업",
    ),
    (
        "environmental_impact_assessment",
        "environmental_impact_assessment_success.json",
        "중앙환경영향평가업",
    ),
    (
        "air_pollution_prevention_facility",
        "air_pollution_prevention_facility_success.json",
        "중앙대기오염방지시설업",
    ),
    (
        "water_pollution_prevention_facility",
        "water_pollution_prevention_facility_success.json",
        "중앙수질오염방지시설업",
    ),
    ("soil_remediation", "soil_remediation_success.json", "중앙토양정화업"),
    (
        "noise_vibration_prevention_facility",
        "noise_vibration_prevention_facility_success.json",
        "중앙소음진동방지시설업",
    ),
    ("waste_recycling", "waste_recycling_success.json", "중앙폐기물재활용업"),
    ("medical_waste_treatment", "medical_waste_treatment_success.json", "중앙의료폐기물처리업"),
    (
        "marine_environment_management",
        "marine_environment_management_success.json",
        "중앙해양환경관리업",
    ),
    ("environmental_consulting", "environmental_consulting_success.json", "중앙환경컨설팅업"),
    ("outdoor_advertising", "outdoor_advertising_success.json", "중앙옥외광고업"),
    ("printing_house", "printing_house_success.json", "중앙인쇄사"),
    ("publisher", "publisher_success.json", "중앙출판사"),
    ("tobacco_wholesale", "tobacco_wholesale_success.json", "중앙담배도매업"),
    ("tobacco_retail", "tobacco_retail_success.json", "중앙담배소매업"),
    ("tobacco_import_sales", "tobacco_import_sales_success.json", "중앙담배수입판매업체"),
    (
        "international_freight_forwarding",
        "international_freight_forwarding_success.json",
        "중앙국제물류주선업",
    ),
    ("logistics_warehouse", "logistics_warehouse_success.json", "중앙물류창고업체"),
    ("civil_defense_water_supply", "civil_defense_water_supply_success.json", "중앙민방위급수시설"),
    ("funeral_service", "funeral_service_success.json", "중앙상조업"),
    ("elevator_maintenance", "elevator_maintenance_success.json", "중앙승강기유지관리업체"),
    (
        "elevator_manufacturing_import",
        "elevator_manufacturing_import_success.json",
        "중앙승강기제조및수입업체",
    ),
    (
        "caregiver_training_institution",
        "caregiver_training_institution_success.json",
        "중앙요양보호사교육기관",
    ),
    (
        "funeral_director_training_institution",
        "funeral_director_training_institution_success.json",
        "중앙장례지도사교육기관",
    ),
    ("free_job_placement", "free_job_placement_success.json", "중앙무료직업소개소"),
    ("paid_job_placement", "paid_job_placement_success.json", "중앙유료직업소개소"),
]


@pytest.mark.parametrize(
    ("dataset_key", "fixture_name", "expected_first_name"),
    _NEW_DATASETS,
    ids=[d[0] for d in _NEW_DATASETS],
)
def test_new_dataset_query_records_parses_success_fixture(
    dataset_key: str,
    fixture_name: str,
    expected_first_name: str,
) -> None:
    payload = _load_fixture(fixture_name)
    adapter, dataset, _ = _build_dataset_adapter_with_transport(
        dataset_key, [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.items[0]["BPLC_NM"] == expected_first_name
