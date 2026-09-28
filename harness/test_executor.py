import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from harness.config import TestRunnerConfig


@dataclass
class TestResult:
    tests_total: int
    tests_passed: int
    passed: bool
    raw_output: str
    error: str | None = None
    status: str = "pass"


class TestExecutor:
    def __init__(self, config: TestRunnerConfig):
        self.config = config

    def run(self, workspace: Path) -> TestResult:
        test_dir = workspace / self.config.pattern.rstrip("/")
        cmd = self.config.command.replace("{test_dir}", str(test_dir)).replace("{workspace}", str(workspace))

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=120, cwd=str(workspace),
            )
            output = result.stdout + "\n" + result.stderr

            if self.config.language == "python":
                return self.parse_pytest_output(output, result.returncode)
            elif self.config.language in ("typescript", "angular"):
                return self.parse_jest_output(output, result.returncode)
            elif self.config.language in ("c", "cpp"):
                return self.parse_make_test_output(output, result.returncode)

            return TestResult(
                tests_total=0, tests_passed=0, passed=result.returncode == 0,
                raw_output=output,
                error=None if result.returncode == 0 else self.summarize_generic_issue(output),
                status="pass" if result.returncode == 0 else "error",
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                tests_total=0, tests_passed=0, passed=False,
                raw_output="", error="Test execution timed out", status="timeout",
            )

    @staticmethod
    def parse_pytest_output(output: str, returncode: int) -> TestResult:
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        error_match = re.search(r"(\d+) errors?", output)
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        errors = int(error_match.group(1)) if error_match else 0
        total = passed + failed
        if returncode == 0:
            status = "pass"
            error = None
        elif failed > 0 and errors == 0:
            status = "fail"
            error = None
        else:
            status = "error"
            error = TestExecutor.summarize_pytest_issue(output)

        return TestResult(
            tests_total=total, tests_passed=passed,
            passed=status == "pass", raw_output=output, error=error, status=status,
        )

    @staticmethod
    def parse_jest_output(output: str, returncode: int) -> TestResult:
        # Prefer the "Tests:" summary line so we do not accidentally parse
        # "Test Suites: X total" as the total number of tests.
        tests_line_match = re.search(r"Tests:\s*(.+)", output)
        search_scope = tests_line_match.group(1) if tests_line_match else output
        passed_match = re.search(r"(\d+)\s+passed", search_scope)
        total_match = re.search(r"(\d+)\s+total", search_scope)
        passed = int(passed_match.group(1)) if passed_match else 0
        total = int(total_match.group(1)) if total_match else 0
        if returncode == 0:
            status = "pass"
            error = None
        elif total > 0:
            status = "fail"
            error = None
        else:
            status = "error"
            error = TestExecutor.summarize_generic_issue(output)
        return TestResult(
            tests_total=total, tests_passed=passed,
            passed=status == "pass", raw_output=output, error=error, status=status,
        )

    @staticmethod
    def parse_make_test_output(output: str, returncode: int) -> TestResult:
        results_match = re.search(r"(\d+)/(\d+) passed", output)
        if results_match:
            passed = int(results_match.group(1))
            total = int(results_match.group(2))
        else:
            passed = len(re.findall(r"\[PASS\]", output))
            failed = len(re.findall(r"\[FAIL\]", output))
            total = passed + failed
        if total > 0:
            status = "pass" if passed == total else "fail"
            error = None
        elif returncode == 0:
            status = "pass"
            error = None
        else:
            status = "error"
            error = TestExecutor.summarize_generic_issue(output)
        return TestResult(
            tests_total=total, tests_passed=passed,
            passed=status == "pass", raw_output=output, error=error, status=status,
        )

    @staticmethod
    def summarize_pytest_issue(output: str) -> str:
        detail = TestExecutor._find_first_match(
            output,
            [
                r"ModuleNotFoundError: .+",
                r"ImportError: .+",
                r"SyntaxError: .+",
                r"ERROR collecting .+",
                r"collected \d+ items? / \d+ errors?",
                r"no tests ran(?: in [^=\n]+)?",
            ],
        )
        if detail:
            lowered = detail.lower()
            if "modulenotfounderror" in lowered or "importerror" in lowered:
                return f"pytest import error: {detail}"
            if "syntaxerror" in lowered:
                return f"pytest syntax error: {detail}"
            if "error collecting" in lowered or "collected " in lowered:
                return f"pytest collection error: {detail}"
            if "no tests ran" in lowered:
                return f"pytest runner error: {detail}"

        generic_detail = TestExecutor.summarize_generic_issue(output)
        return f"pytest error: {generic_detail}" if generic_detail else "pytest error"

    @staticmethod
    def summarize_generic_issue(output: str) -> str:
        line = TestExecutor._first_meaningful_line(output)
        return line or "runner exited non-zero without a parsed test summary"

    @staticmethod
    def _find_first_match(output: str, patterns: list[str]) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return TestExecutor._compact_whitespace(match.group(0))
        return None

    @staticmethod
    def _first_meaningful_line(output: str) -> str | None:
        ignored_prefixes = (
            "=",
            "-",
            "platform ",
            "cachedir:",
            "rootdir:",
            "plugins:",
            "collecting ",
            "test session starts",
        )
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(ignored_prefixes):
                continue
            return TestExecutor._compact_whitespace(line)
        return None

    @staticmethod
    def _compact_whitespace(text: str) -> str:
        return " ".join(text.split())
