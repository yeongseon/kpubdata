"""이번 세션에서 추가된 기능의 통합 테스트.

license 필드, ocean_buoy spec, CI verify, 포지셔닝 변경 등
여러 PR에 걸쳐 추가된 기능이 올바르게 통합되는지 검증한다.
"""

from __future__ import annotations

from kpubdata import Client
from kpubdata.core.spec import LicenseSpec, discover_specs, find_spec


class TestLicenseFieldIntegration:
    """spec license 필드가 전체 파이프라인에서 동작하는지 검증."""

    def test_spec_with_license_loads(self) -> None:
        """license가 있는 spec이 정상 로드된다."""
        spec = find_spec("datago.apt_trade")
        assert spec is not None
        assert isinstance(spec.license, LicenseSpec)
        assert spec.license.type == "공공누리_1유형"
        assert spec.license.commercial_use is True
        assert spec.license.attribution_required is True

    def test_spec_without_license_loads(self) -> None:
        """license가 없는 spec도 정상 로드된다 (None)."""
        spec = find_spec("datago.hospital_info")
        assert spec is not None
        assert spec.license is None

    def test_all_specs_valid_license_or_none(self) -> None:
        """모든 spec의 license가 LicenseSpec이거나 None이다."""
        for spec in discover_specs():
            if spec.license is not None:
                assert isinstance(spec.license, LicenseSpec), f"{spec.id}: invalid license type"

    def test_license_preserved_across_four_datago_specs(self) -> None:
        """PR #443에서 추가한 4개 datago spec에 license가 보존된다."""
        for ds_id in (
            "datago.apt_trade",
            "datago.apt_rent",
            "datago.air_quality",
            "datago.village_fcst",
        ):
            spec = find_spec(ds_id)
            assert spec is not None, f"{ds_id} not found"
            assert spec.license is not None, f"{ds_id} has no license"
            assert spec.license.type == "공공누리_1유형"


class TestOceanBuoyIntegration:
    """ocean_buoy spec이 올바르게 통합되는지 검증."""

    def test_spec_discoverable(self) -> None:
        """ocean_buoy가 discover_specs에 포함된다."""
        specs = discover_specs()
        ids = [s.id for s in specs]
        assert "datago.ocean_buoy" in ids

    def test_spec_fields(self) -> None:
        """ocean_buoy spec의 핵심 필드가 올바르다."""
        spec = find_spec("datago.ocean_buoy")
        assert spec is not None
        assert spec.title.startswith("해양관측부이")
        assert spec.endpoint.operation == "GetTWRecentApiService"
        assert spec.status == "unstable"

        param_names = {p.name for p in spec.params}
        assert "obsCode" in param_names

        field_names = {f.name for f in spec.fields}
        assert "wvhgt" in field_names  # 파고
        assert "wspd" in field_names  # 풍속
        assert "wtem" in field_names  # 수온

    def test_client_resolves_ocean_buoy(self) -> None:
        """Client가 ocean_buoy를 정상적으로 resolve한다."""
        client = Client()
        ds_list = client.datasets.list(provider="datago")
        ocean_ids = [d.id for d in ds_list if "ocean" in d.id]
        assert "datago.ocean_buoy" in ocean_ids


class TestKrxLicenseNotice:
    """KRX 라이선스 경고가 catalogue에서 보존되는지 검증."""

    def test_license_note_in_raw_metadata(self) -> None:
        """3개 KRX 데이터셋에 license_note가 있다."""
        client = Client()
        for ds_id in ("krx.kospi_index", "krx.investor_flow", "krx.market_valuation"):
            ds_ref = next(d for d in client.datasets.list(provider="krx") if d.id == ds_id)
            note = ds_ref.raw_metadata.get("license_note")
            assert note is not None, f"{ds_id}: license_note missing"
            assert "KRX" in note or "재배포" in note


class TestSpecSchemaValidation:
    """spec schema.json에 추가된 license 필드가 검증을 통과하는지."""

    def test_validate_all_specs_pass(self) -> None:
        """전체 spec이 schema 검증을 통과한다."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "scripts/validate_spec.py"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"spec validation failed:\n{result.stdout}\n{result.stderr}"
        assert "실패" not in result.stdout or "0개 실패" in result.stdout


class TestClientIntegrationSmoke:
    """Client 레벨 기본 동작 스모크 테스트."""

    def test_datasets_list_includes_all_providers(self) -> None:
        """Client.datasets.list()가 주요 provider를 포함한다."""
        client = Client()
        all_ds = client.datasets.list()
        providers = {d.provider for d in all_ds}
        # 이번 세션에서 변경한 provider들이 여전히 등록되어 있는지
        assert "datago" in providers
        assert "krx" in providers
        assert "bok" in providers

    def test_search_finds_ocean_buoy(self) -> None:
        """검색으로 ocean_buoy를 찾을 수 있다."""
        client = Client()
        results = client.datasets.search("해양")
        ids = [d.id for d in results]
        assert "datago.ocean_buoy" in ids

    def test_spec_count_increased(self) -> None:
        """spec 데이터셋이 23개 이상이다 (ocean_buoy 추가 후)."""
        specs = discover_specs()
        assert len(specs) >= 23
