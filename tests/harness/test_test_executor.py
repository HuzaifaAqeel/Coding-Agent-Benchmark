from harness.test_executor import TestExecutor as HarnessTestExecutor


def test_parse_pytest_output_all_pass():
    output = """
test_main.py::test_one PASSED
test_main.py::test_two PASSED

============================== 2 passed ==============================
"""
    result = HarnessTestExecutor.parse_pytest_output(output, returncode=0)
    assert result.tests_total == 2
    assert result.tests_passed == 2
    assert result.passed is True


def test_parse_pytest_output_some_fail():
    output = """
test_main.py::test_one PASSED
test_main.py::test_two FAILED
test_main.py::test_three PASSED

========================= 2 passed, 1 failed =========================
"""
    result = HarnessTestExecutor.parse_pytest_output(output, returncode=1)
    assert result.tests_total == 3
    assert result.tests_passed == 2
    assert result.passed is False
    assert result.status == "fail"


def test_parse_pytest_output_collection_error():
    output = """
============================= test session starts ==============================
collecting ... collected 0 items / 1 error

==================================== ERRORS ====================================
ERROR collecting tests/test_math_utils.py
ModuleNotFoundError: No module named 'math_utils'
=========================== short test summary info ============================
ERROR tests/test_math_utils.py
=============================== 1 error in 0.05s ===============================
"""
    result = HarnessTestExecutor.parse_pytest_output(output, returncode=2)
    assert result.tests_total == 0
    assert result.tests_passed == 0
    assert result.passed is False
    assert result.status == "error"
    assert result.error == "pytest import error: ModuleNotFoundError: No module named 'math_utils'"


def test_parse_pytest_output_no_tests_ran():
    output = """
============================= test session starts ==============================
collected 0 items

============================ no tests ran in 0.01s =============================
"""
    result = HarnessTestExecutor.parse_pytest_output(output, returncode=5)
    assert result.status == "error"
    assert result.error == "pytest runner error: no tests ran in 0.01s"


def test_parse_jest_output_all_pass():
    output = """
Tests:       5 passed, 5 total
"""
    result = HarnessTestExecutor.parse_jest_output(output, returncode=0)
    assert result.tests_total == 5
    assert result.tests_passed == 5
    assert result.passed is True
    assert result.status == "pass"


def test_parse_jest_output_prefers_tests_over_suites():
    output = """
Test Suites: 1 passed, 1 total
Tests:       5 passed, 5 total
"""
    result = HarnessTestExecutor.parse_jest_output(output, returncode=0)
    assert result.tests_total == 5
    assert result.tests_passed == 5
    assert result.passed is True


def test_parse_jest_output_runner_error_without_summary():
    output = """
Error: Cannot find module 'jest'
"""
    result = HarnessTestExecutor.parse_jest_output(output, returncode=1)
    assert result.tests_total == 0
    assert result.tests_passed == 0
    assert result.status == "error"
    assert result.error == "Error: Cannot find module 'jest'"


def test_parse_make_test_output():
    output = """
[PASS] test_insert
[PASS] test_delete
[FAIL] test_search
Results: 2/3 passed
"""
    result = HarnessTestExecutor.parse_make_test_output(output, returncode=1)
    assert result.tests_total == 3
    assert result.tests_passed == 2
    assert result.passed is False
    assert result.status == "fail"


def test_parse_make_test_output_runner_error_without_results():
    output = """
make: *** No rule to make target 'test'.  Stop.
"""
    result = HarnessTestExecutor.parse_make_test_output(output, returncode=2)
    assert result.tests_total == 0
    assert result.tests_passed == 0
    assert result.status == "error"
    assert result.error == "make: *** No rule to make target 'test'. Stop."
