from unittest.mock import patch

from harness.runner import AgentRunner
from harness.config import AgentConfig


def test_prepare_workspace_copies_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("code here")
    (repo / "subdir").mkdir()
    (repo / "subdir" / "util.py").write_text("util code")

    runner = AgentRunner(AgentConfig(
        name="test", command="echo", args=[], model=None, timeout_seconds=60
    ))
    workspace = runner.prepare_workspace(repo)
    assert (workspace / "main.py").exists()
    assert (workspace / "main.py").read_text() == "code here"
    assert (workspace / "subdir" / "util.py").exists()
    runner.cleanup()


def test_copy_tests_into_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("assert True")

    runner = AgentRunner(AgentConfig(
        name="test", command="echo", args=[], model=None, timeout_seconds=60
    ))
    runner.copy_tests(tests_dir, workspace)
    assert (workspace / "tests" / "test_main.py").exists()


def test_run_passes_rendered_env_overrides(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runner = AgentRunner(AgentConfig(
        name="codex",
        command="codex",
        args=["exec", "{prompt}", "-m", "{model}"],
        model="gpt-test",
        timeout_seconds=60,
        env={"CODEX_HOME": "{root}/harness/codex-home", "WORKSPACE_PATH": "{workspace}"},
    ))

    with patch("harness.runner.subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        runner.run("solve it", workspace)

    _, kwargs = mock_run.call_args
    env = kwargs["env"]
    assert env["CODEX_HOME"].endswith("/harness/codex-home")
    assert env["WORKSPACE_PATH"] == str(workspace)
    assert kwargs["cwd"] is None
