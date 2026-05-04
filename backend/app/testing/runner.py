from __future__ import annotations

from pathlib import Path
import time
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_soc_tests() -> dict[str, Any]:
    """
    Execute SOC pytest suite programmatically and return structured summary.
    This wrapper never changes test logic; it only orchestrates and captures output.
    """
    try:
        import pytest
    except Exception as exc:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration": 0.0,
            "failures": [
                {
                    "test": "pytest_import",
                    "error": f"pytest unavailable: {exc}",
                }
            ],
        }

    class _CapturePlugin:
        def __init__(self) -> None:
            self.total = 0
            self.passed = 0
            self.failed = 0
            self.failures: list[dict[str, str]] = []

        def pytest_runtest_logreport(self, report):  # type: ignore[no-untyped-def]
            if report.when != "call":
                return
            self.total += 1
            if report.passed:
                self.passed += 1
                return
            if report.failed:
                self.failed += 1
                error = str(getattr(report, "longreprtext", "") or "Assertion failure")
                self.failures.append(
                    {
                        "test": str(getattr(report, "nodeid", "unknown_test")),
                        "error": error[:1800],
                    }
                )

    plugin = _CapturePlugin()
    target = _repo_root() / "backend" / "tests" / "test_soc_dashboard.py"
    start = time.perf_counter()
    exit_code = pytest.main([str(target), "-q"], plugins=[plugin])
    duration = round(time.perf_counter() - start, 3)

    # Some pytest failures can happen before tests execute (collection/import errors).
    if plugin.total == 0 and int(exit_code) != 0 and not plugin.failures:
        plugin.failures.append(
            {
                "test": "pytest_collection",
                "error": f"pytest exited with code {int(exit_code)} before running tests",
            }
        )

    return {
        "total": plugin.total,
        "passed": plugin.passed,
        "failed": plugin.failed,
        "duration": duration,
        "failures": plugin.failures,
    }
