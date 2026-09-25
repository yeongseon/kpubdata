"""도달성 프로브 (#499).

데이터셋 추가에서 사람만 할 수 있는 단계는 data.go.kr 활용신청 하나인데, 어느
데이터셋이 그걸 기다리는지가 문서 비고란 텍스트에만 있었다. 에이전트는 spec 작업을
시작한 뒤에야 403 으로 알게 됐다 — 되돌릴 작업을 먼저 하는 셈이다.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from kpubdata._probe import (
    ProbeResult,
    classify,
    render_apply_report,
    service_id_of,
    summarize,
    write_report,
)
from kpubdata.core.spec import find_spec
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ParseError,
    RateLimitError,
    ServiceUnavailableError,
    TransportError,
)

_NOW = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def _result(dataset_id: str, service_id: str, status: str) -> ProbeResult:
    return ProbeResult(dataset_id=dataset_id, service_id=service_id, status=status, probed_at=_NOW)


class TestClassification:
    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            (None, "ok"),
            (AuthError("not activated"), "auth-403"),
            (TransportError("forbidden", status_code=403), "auth-403"),
            (InvalidRequestError("missing param"), "params-400"),
            (DatasetNotFoundError("gone"), "gone"),
            (ServiceUnavailableError("down"), "gone"),
            (TransportError("boom", status_code=500), "gone"),
            (ParseError("bad body"), "gone"),
        ],
    )
    def test_each_failure_lands_in_its_bucket(
        self, error: BaseException | None, expected: str
    ) -> None:
        assert classify(error)[0] == expected

    def test_a_rate_limit_counts_as_reachable(self) -> None:
        """한도 초과는 "도달은 된다" 는 뜻이다 — 활용신청 대상이 아니다.

        ``RateLimitError`` 가 ``TransportError`` 의 하위라, 판정 순서를 뒤집으면
        조용히 ``gone`` 으로 분류된다. 실제로 그렇게 짰다가 고쳤다.
        """
        assert classify(RateLimitError("quota exceeded"))[0] == "ok"


class TestServiceIdGrouping:
    """활용신청은 데이터셋이 아니라 **서비스** 단위로 한다."""

    def test_datasets_sharing_a_service_share_an_id(self) -> None:
        ids = {
            service_id_of(spec)
            for dataset_id in ("datago.air_quality", "datago.air_station")
            if (spec := find_spec(dataset_id)) is not None
        }

        assert ids == {"ArpltnInforInqireSvc"}

    def test_a_different_service_gets_a_different_id(self) -> None:
        spec = find_spec("datago.apt_trade")
        assert spec is not None

        assert service_id_of(spec) != "ArpltnInforInqireSvc"


class TestApplyReport:
    def test_it_groups_by_service_not_dataset(self) -> None:
        """이게 보고서의 요점이다 — 데이터셋별로 나열하면 3번 신청해야 하는 것처럼 보인다."""
        results = [
            _result("datago.air_quality", "ArpltnInforInqireSvc", "auth-403"),
            _result("datago.air_station", "ArpltnInforInqireSvc", "auth-403"),
            _result("datago.airkorea_forecast", "ArpltnInforInqireSvc", "auth-403"),
        ]

        report = render_apply_report(results)

        assert "서비스 1건을 신청하면 데이터셋 3종이 풀립니다" in report
        assert report.count("## ") == 1

    def test_only_pending_datasets_appear(self) -> None:
        results = [
            _result("datago.ok", "OkSvc", "ok"),
            _result("datago.broken", "GoneSvc", "gone"),
            _result("datago.pending", "PendingSvc", "auth-403"),
        ]

        report = render_apply_report(results)

        assert "PendingSvc" in report
        assert "OkSvc" not in report
        assert "GoneSvc" not in report

    def test_nothing_pending_says_so(self) -> None:
        report = render_apply_report([_result("datago.ok", "OkSvc", "ok")])

        assert "없습니다" in report


class TestReportFile:
    def test_it_writes_the_documented_shape(self, tmp_path: Path) -> None:
        out = tmp_path / "key-scope.json"

        write_report([_result("datago.x", "XSvc", "auth-403")], out)

        payload = json.loads(out.read_text(encoding="utf-8"))
        assert set(payload) == {"probed_at", "results"}
        assert payload["results"][0] == {
            "dataset_id": "datago.x",
            "service_id": "XSvc",
            "status": "auth-403",
            "probed_at": _NOW,
            "detail": "",
        }

    def test_results_are_sorted_so_the_file_is_diffable(self, tmp_path: Path) -> None:
        out = tmp_path / "key-scope.json"

        write_report([_result("datago.b", "S", "ok"), _result("datago.a", "S", "ok")], out)

        ids = [r["dataset_id"] for r in json.loads(out.read_text(encoding="utf-8"))["results"]]
        assert ids == sorted(ids)


def test_summarize_counts_each_bucket() -> None:
    results = [
        _result("a", "S", "ok"),
        _result("b", "S", "auth-403"),
        _result("c", "S", "auth-403"),
    ]

    assert summarize(results) == {"ok": 1, "auth-403": 2}
