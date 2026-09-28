from pathlib import Path

from harness.config import load_config


def test_load_config_reads_agent_env(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  codex:
    command: "codex"
    env:
      CODEX_HOME: "{root}/harness/codex-home"
    args: ["exec", "{prompt}"]
    model: "gpt-test"
    timeout_seconds: 123
test_runners:
  python:
    command: "pytest {test_dir}"
    pattern: "tests/"
results_dir: "results"
""".strip()
    )

    config = load_config(config_path)

    assert len(config.agents) == 1
    assert config.agents[0].env == {"CODEX_HOME": "{root}/harness/codex-home"}
    assert config.agents[0].timeout_seconds == 123
