# 🤖 Coding-Agent-Benchmark

**Benchmark harness for LLM coding agents — run any agent CLI against 11 synthetic SWE tasks and compare correctness vs. speed.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)

Claude Code, Codex, and friends all claim to write code — but which one actually fixes the bug,
how fast, and on what kind of task? **Coding-Agent-Benchmark** runs each configured coding agent in
an isolated temporary workspace against a suite of synthetic software-engineering tasks, then scores
the results with hidden test suites the agents never see. Every run produces a per-task scorecard
(test pass rate, wall-clock time) and a JSON summary you can diff across agents and models.

## Features

- **11 synthetic SWE tasks** across Python, C, C++, TypeScript, and Angular — bugfix, feature,
  scratch-build, refactor, and multifile categories
- **Fair by design** — agents work in temp workspaces and never see the hidden test suites
- **Any agent CLI** — configure any command-line coding agent in `harness/config.yaml`
  (defaults: Claude Code and Codex CLI)
- **Per-task scorecards** — tests passed/total, correctness rate, wall-clock seconds, timeouts,
  and failure summaries
- **Dry-run mode** — validate the whole harness (task loading, test execution, scoring, reports)
  without invoking any agent
- **JSON summaries** — machine-readable results per run for tracking regressions over time

## Tasks

| # | Task | Language | Category |
|---|------|----------|----------|
| 00 | smoke-test | Python | bugfix |
| 01 | python-bugfix-csv | Python | bugfix |
| 02 | c-bugfix-linkedlist | C | bugfix |
| 03 | typescript-feature-table-filter | TypeScript | feature |
| 04 | python-feature-pagination | Python | feature |
| 05 | typescript-scratch-task-queue | TypeScript | scratch |
| 06 | cpp-scratch-lru-cache | C++ | scratch |
| 07 | python-refactor-monolith | Python | refactor |
| 08 | typescript-refactor-callbacks | TypeScript | refactor |
| 09 | c-multifile-segfault | C/C++ | multifile |
| 10 | fullstack-angular-python | Python/Angular | multifile |

Each task is self-contained:

```
tasks/<name>/
  metadata.json   # language, category, timeout
  prompt.md       # instruction given to the agent
  repo/           # source code (broken or incomplete)
  tests/          # hidden test suite
```

## Installation

```bash
pip install -r requirements.txt
```

Prerequisites for a full run: Python 3.11+, your agent CLIs on `PATH` (e.g. `claude`, `codex`),
and the language toolchains for the tasks you run (Python, Node.js, GCC/G++, Make).

## Quick Start

```bash
# Dry run — test every task repo as-is, no agents invoked (no API keys needed)
python -m harness.run --dry-run

# Full benchmark (all agents, all tasks)
python -m harness.run

# Custom config or task directory
python -m harness.run --config path/to/config.yaml --tasks-dir path/to/tasks
```

## Configuring agents

Edit `harness/config.yaml`:

```yaml
agents:
  my-agent:
    command: "my-agent"
    args: ["run", "{prompt}", "--model", "{model}"]
    model: "my-best-model"
    timeout_seconds: 300
```

`{prompt}` is replaced with the task's `prompt.md`, `{model}` with the configured model.
The harness parses each agent's stdout for a completion signal — see `harness/runner.py`.

## How It Works

1. **Load** — tasks and agent configs are loaded from disk; each task declares its language,
   category, and timeout.
2. **Isolate** — the agent gets a fresh copy of the task repo in a temp workspace.
3. **Run** — the agent CLI is invoked with the task prompt; wall-clock time is measured and
   timeouts are enforced per task.
4. **Score** — hidden pytest/jest/make test suites run against the agent's output; pass rate
   becomes the correctness score.
5. **Report** — `harness/report.py` renders a console scorecard and writes `results/<run-id>/summary.json`.

## Extending

Natural next metrics: **token efficiency** (parse usage from agent JSON output in `runner.py`),
cost-per-task (tokens × model pricing), and pass@k sampling. The `TaskScore` dataclass in
`harness/scoring.py` is the place to add them.

## Environment variables

None required by the harness itself — agents authenticate through their own CLIs
(`claude`, `codex`, …). Dry-run mode needs nothing at all.

## License

MIT — see [LICENSE](LICENSE).
