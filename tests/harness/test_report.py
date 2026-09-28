from harness.report import format_report
from harness.scoring import TaskScore


def _make_score(
    agent,
    task,
    passed,
    total,
    seconds,
    *,
    status=None,
    failure_summary=None,
    timed_out=False,
):
    return TaskScore(
        task=task, agent=agent, model="test",
        tests_passed=passed, tests_total=total,
        correctness=passed / total if total else 0,
        wall_clock_seconds=seconds,
        timed_out=timed_out,
        status=status or ("pass" if total and passed == total else "fail"),
        error=failure_summary,
        failure_summary=failure_summary,
    )


def test_format_report_contains_task_results():
    scores = [
        _make_score("claude-code", "task1", 5, 5, 30),
        _make_score("codex", "task1", 3, 5, 45),
    ]
    report = format_report(scores)
    assert "task1" in report
    assert "claude-code" in report.lower() or "Claude Code" in report
    assert "codex" in report.lower() or "Codex" in report


def test_format_report_contains_summary():
    scores = [
        _make_score("claude-code", "task1", 5, 5, 30),
        _make_score("codex", "task1", 5, 5, 45),
    ]
    report = format_report(scores)
    assert "SUMMARY" in report or "Summary" in report


def test_format_report_includes_failure_details():
    scores = [
        _make_score("claude-code", "task1", 0, 0, 30, status="error", failure_summary="pytest collection error"),
        _make_score("codex", "task1", 3, 5, 45, status="fail", failure_summary="2/5 tests failed"),
    ]
    report = format_report(scores)
    assert "FAILURE DETAILS" in report
    assert "task1 [claude-code] ERROR: pytest collection error" in report
    assert "task1 [codex] FAIL: 2/5 tests failed" in report
