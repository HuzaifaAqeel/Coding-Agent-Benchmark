from harness.scoring import TaskScore, compute_summary


def _make_score(agent, task, tests_passed, tests_total, seconds, timed_out=False):
    return TaskScore(
        task=task, agent=agent, model="test-model",
        tests_passed=tests_passed, tests_total=tests_total,
        correctness=tests_passed / tests_total if tests_total else 0,
        wall_clock_seconds=seconds,
        timed_out=timed_out,
        status="timeout" if timed_out else ("pass" if tests_total and tests_passed == tests_total else "fail"),
        error=None,
        failure_summary=None,
    )


def test_summary_counts_passed_tasks():
    scores = [
        _make_score("claude", "task1", 5, 5, 30),
        _make_score("claude", "task2", 3, 5, 40),
        _make_score("codex", "task1", 5, 5, 45),
        _make_score("codex", "task2", 5, 5, 35),
    ]
    summary = compute_summary(scores)
    assert summary["claude"]["tasks_fully_passed"] == 1
    assert summary["codex"]["tasks_fully_passed"] == 2


def test_summary_avg_correctness():
    scores = [
        _make_score("claude", "task1", 4, 4, 30),
        _make_score("claude", "task2", 2, 4, 40),
    ]
    summary = compute_summary(scores)
    assert summary["claude"]["avg_correctness"] == 0.75


def test_summary_excludes_timed_out_from_speed():
    scores = [
        _make_score("claude", "task1", 4, 4, 30),
        _make_score("claude", "task2", 0, 4, 300, timed_out=True),
    ]
    summary = compute_summary(scores)
    assert summary["claude"]["avg_speed_seconds"] == 30.0


def test_summary_includes_status_and_failure_summary():
    score = TaskScore(
        task="task1",
        agent="claude",
        model="test-model",
        tests_passed=0,
        tests_total=0,
        correctness=0,
        wall_clock_seconds=12,
        timed_out=False,
        status="error",
        error="pytest collection error",
        failure_summary="pytest collection error",
    )
    summary = compute_summary([score])
    saved = summary["claude"]["scores"][0]
    assert saved["status"] == "error"
    assert saved["failure_summary"] == "pytest collection error"
