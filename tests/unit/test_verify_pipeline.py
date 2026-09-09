"""Phase 2 검증 파이프라인 단위 테스트 — record·verify·replay의 오프라인 동작 검증.

실호출 기록은 `make record`(integration 성격)로 별도 수행한다. 여기서는
FakeTransport 주입으로 record의 파일 산출물, verify의 무결성 규칙,
replay의 매칭 규칙을 결정적으로 검증한다.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest

from kpubdata import Client

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
SPECS_DIR = REPO_ROOT / "src" / "kpubdata" / "specs"


def _load_script(name: str):
    """scripts/ 모듈을 로드한다(scripts를 sys.path에 넣어 redact import 지원)."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


record_mod = _load_script("record")
verify_mod = _load_script("verify_spec")


# ----------------------------------------------------------------------
# record: 산출물 3종 + 정화 + 해시
# ----------------------------------------------------------------------


class FakeLiveTransport:
    """실호출 대신 표준 envelope을 주는 전송 계층."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

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
    ) -> object:

        self.calls.append({"url": url, "params": dict(params or {})})
        # village_fcst의 xml 예제는 XML 응답을 흉내낸다.
        fmt = (
            (params or {}).get("dataType")
            or (params or {}).get("_type")
            or (params or {}).get("resultType")
        )
        key = dataset_id or ""
        if key == "datago.village_fcst" and fmt == "XML":
            xml = (
                "<response><header><resultCode>00</resultCode></header>"
                "<body><items><item><category>T1H</category></item></items>"
                "<totalCount>1</totalCount></body></response>"
            )
            return httpx.Response(
                200,
                content=xml.encode(),
                headers={"content-type": "text/xml"},
                request=httpx.Request("GET", url),
            )
        payload = {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "OK"},
                "body": {"items": {"item": [{"no": 1}, {"no": 2}]}, "totalCount": "2"},
            }
        }
        return httpx.Response(
            200,
            content=json.dumps(payload).encode(),
            headers={"content-type": "application/json"},
            request=httpx.Request("GET", url),
        )


class FakeLiveConfig(record_mod.KPubDataConfig):
    """키를 고정값으로 제공하는 설정."""

    def get_provider_key(self, provider: str) -> str | None:
        return "real-secret-key" if provider == "datago" else None

    def require_provider_key(self, provider: str) -> str:
        return "real-secret-key"


def test_record_dataset_writes_three_files(tmp_path: Path) -> None:
    """example마다 raw·meta·expected 3종이 기록되고 키가 정화된다."""
    transport = FakeLiveTransport()
    written = record_mod.record_dataset(
        "datago.apt_trade",
        fixtures_root=tmp_path,
        config=FakeLiveConfig(),
        transport=transport,  # type: ignore[arg-type]
        recorded_by="agent-test",
    )
    out_dir = tmp_path / "datago" / "apt_trade"
    examples = sorted(path.name.removesuffix(".raw.json") for path in out_dir.glob("*.raw.json"))
    assert len(examples) >= 1
    assert len(written) == len(examples) * 3

    for name in examples:
        raw = json.loads((out_dir / f"{name}.raw.json").read_text(encoding="utf-8"))
        meta = json.loads((out_dir / f"{name}.meta.json").read_text(encoding="utf-8"))
        expected = json.loads((out_dir / f"{name}.expected.json").read_text(encoding="utf-8"))

        # 키 정화: meta params와 raw 어디에도 실제 키가 없다.
        assert "real-secret-key" not in json.dumps(meta) + json.dumps(raw)
        assert meta["params"]["serviceKey"] == "[REDACTED]"
        assert meta["recorded_by"] == "agent-test"
        assert meta["dataset_id"] == "datago.apt_trade"
        assert meta["endpoint"].endswith("getRTMSDataSvcAptTradeDev")
        # 해시 정합: verify가 같은 규칙으로 재계산해 일치해야 한다.
        canon = json.dumps(raw, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
        import hashlib

        assert hashlib.sha256(canon.encode()).hexdigest() == meta["response_sha256"]
        # expected 스냅샷
        assert expected == {"items": [{"no": 1}, {"no": 2}], "total_count": 2}


# ----------------------------------------------------------------------
# verify: 무결성·replay 계약
# ----------------------------------------------------------------------


def _record_apt(tmp_path: Path) -> None:
    """verify 테스트용으로 apt_trade fixture를 기록한다."""
    record_mod.record_dataset(
        "datago.apt_trade",
        fixtures_root=tmp_path,
        config=FakeLiveConfig(),
        transport=FakeLiveTransport(),  # type: ignore[arg-type]
        recorded_by="test",
    )


def test_verify_passes_on_fresh_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """방금 기록한 fixture는 검증을 통과한다."""
    _record_apt(tmp_path)
    monkeypatch.setattr(verify_mod, "FIXTURES_ROOT", tmp_path)
    steps = verify_mod._verify_fixtures(_spec("datago.apt_trade"))
    assert steps, "fixture 검증 단계가 생성되어야 한다"
    assert all(step.passed for step in steps)


def test_verify_fails_when_fixture_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """fixture가 없으면 실패하고 record 안내를 출력한다."""
    monkeypatch.setattr(verify_mod, "FIXTURES_ROOT", Path("/nonexistent"))
    steps = verify_mod._verify_fixtures(_spec("datago.apt_trade"))
    assert not all(step.passed for step in steps)
    assert any("make record" in step.detail for step in steps)


def test_verify_fails_on_hash_tamper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """기록 후 raw를 수정하면 해시 불일치로 실패한다(agent 위조 차단)."""
    _record_apt(tmp_path)
    monkeypatch.setattr(verify_mod, "FIXTURES_ROOT", tmp_path)
    raw_file = next((tmp_path / "datago" / "apt_trade").glob("*.raw.json"))
    payload = json.loads(raw_file.read_text(encoding="utf-8"))
    payload["response"]["body"]["totalCount"] = "999"
    raw_file.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8"
    )
    steps = verify_mod._verify_fixtures(_spec("datago.apt_trade"))
    assert any("해시" in step.name and not step.passed for step in steps)


def test_verify_fails_when_spec_field_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """spec의 items_path를 바꾸면 replay 단계에서 실패한다(컷오버 검증 시나리오)."""
    _record_apt(tmp_path)
    monkeypatch.setattr(verify_mod, "FIXTURES_ROOT", tmp_path)
    from dataclasses import replace

    spec = _spec("datago.apt_trade")
    tampered = replace(
        spec, response=replace(spec.response, items_path="response.body.items.OTHER")
    )
    steps = verify_mod._verify_fixtures(tampered)
    assert not all(step.passed for step in steps)


def _spec(dataset_id: str):
    from kpubdata.core.spec import find_spec

    spec = find_spec(dataset_id)
    assert spec is not None
    return spec


# ----------------------------------------------------------------------
# replay: 매칭·실패 안내
# ----------------------------------------------------------------------


def test_replay_matches_recorded_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """기록된 시그니처(키 제외)로 요청하면 fixture 응답이 돌아온다."""
    _record_apt(tmp_path)
    monkeypatch.setenv("KPUBDATA_REPLAY_DIR", str(tmp_path))
    from kpubdata.transport.replay import replay_response

    response = replay_response(
        "GET",
        "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
        params={
            "serviceKey": "any-other-key",
            "pageNo": "1",
            "numOfRows": "100",
            "LAWD_CD": "11110",
            "DEAL_YMD": "202401",
            "resultType": "json",
        },
        dataset_id="datago.apt_trade",
        provider="datago",
    )
    payload = json.loads(response.content)
    assert payload["response"]["header"]["resultCode"] == "00"


def test_replay_miss_raises_with_record_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """등록된 데이터셋·엔드포인트인데 파라미터가 다르면 make record 안내와 함께 실패."""
    _record_apt(tmp_path)
    monkeypatch.setenv("KPUBDATA_REPLAY_DIR", str(tmp_path))
    from kpubdata.exceptions import InvalidRequestError
    from kpubdata.transport.replay import replay_response

    # 미등록 데이터셋/엔드포인트는 불간섭(None) — 무관 요청은 실호출 경로.
    assert replay_response("GET", "https://never.recorded/api", params={}) is None

    # 등록된 조합 + 다른 파라미터 → 엄격 실패.
    with pytest.raises(InvalidRequestError, match="make record"):
        replay_response(
            "GET",
            "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
            params={"pageNo": "99", "numOfRows": "1", "LAWD_CD": "11110", "DEAL_YMD": "202401"},
            dataset_id="datago.apt_trade",
            provider="datago",
        )


def test_client_replay_mode_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """KPUBDATA_MODE=replay에서 Client 질의가 fixture로 서빙된다(실호출 0)."""
    _record_apt(tmp_path)
    monkeypatch.setenv("KPUBDATA_REPLAY_DIR", str(tmp_path))
    monkeypatch.setenv("KPUBDATA_MODE", "replay")

    client = Client(provider_keys={"datago": "test-key"}, cache=False)
    batch = client.dataset("datago.apt_trade").list(
        LAWD_CD="11110", DEAL_YMD="202401", page=1, page_size=100
    )
    assert batch.items == [{"no": 1}, {"no": 2}]
    assert batch.total_count == 2
