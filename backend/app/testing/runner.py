from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _backend_root() -> Path:
    # Works both locally (…/backend/app/testing/runner.py → parents[2] = backend/)
    # and in Docker  (/app/app/testing/runner.py           → parents[2] = /app)
    return Path(__file__).resolve().parents[2]


def run_soc_tests() -> dict[str, Any]:
    """Execute the full self-test suite in a subprocess and return structured results.

    Running as a subprocess avoids asyncio event-loop conflicts between the
    running uvicorn server and pytest-asyncio's own loop. Results are captured
    via JUnit XML (built into pytest — no extra plugins needed).
    """
    backend = _backend_root()
    test_files = [
        backend / "tests" / "test_gateway_suite.py",
        backend / "tests" / "test_soc_dashboard.py",
    ]
    # Only include files that exist
    test_files = [str(t) for t in test_files if t.exists()]

    if not test_files:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration": 0.0,
            "tests": [],
            "failures": [{"test": "no_test_files", "error": "No test files found"}],
        }

    # Write JUnit XML to a temp file so we can parse structured results
    xml_fd, xml_path = tempfile.mkstemp(suffix=".xml", prefix="zta_tests_")
    os.close(xml_fd)

    env = {**os.environ, "PYTHONPATH": str(backend)}

    cmd = [
        sys.executable, "-m", "pytest",
        *test_files,
        f"--junit-xml={xml_path}",
        "--tb=short",
        "-q",
        "--no-header",
        "--override-ini=asyncio_mode=auto",
    ]

    start = time.perf_counter()
    try:
        subprocess.run(
            cmd,
            cwd=str(backend),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration": round(time.perf_counter() - start, 3),
            "tests": [],
            "failures": [{"test": "timeout", "error": "Test suite timed out after 300 seconds"}],
        }
    except Exception as exc:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration": round(time.perf_counter() - start, 3),
            "tests": [],
            "failures": [{"test": "subprocess_error", "error": str(exc)}],
        }
    duration = round(time.perf_counter() - start, 3)

    # Parse JUnit XML results
    tests: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    passed = 0
    failed = 0

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # JUnit XML may have one or more <testsuite> elements
        suites = list(root.iter("testsuite"))
        if not suites and root.tag == "testsuite":
            suites = [root]

        for suite in suites:
            for tc in suite.findall("testcase"):
                classname = tc.get("classname", "")
                name = tc.get("name", "unknown")
                # Build node ID: classname uses dots, convert to path::name
                node_id = f"{classname.replace('.', '/')}.py::{name}" if classname else name
                dur_ms = round(float(tc.get("time", 0)) * 1000)

                failure_el = tc.find("failure")
                error_el = tc.find("error")
                skipped_el = tc.find("skipped")

                if failure_el is not None or error_el is not None:
                    el = failure_el if failure_el is not None else error_el
                    err_text = (el.text or el.get("message", "Assertion failure"))[:1800]
                    tests.append({"test": node_id, "state": "fail", "duration_ms": dur_ms})
                    failures.append({"test": node_id, "error": err_text.strip()})
                    failed += 1
                elif skipped_el is not None:
                    tests.append({"test": node_id, "state": "skip", "duration_ms": dur_ms})
                else:
                    tests.append({"test": node_id, "state": "pass", "duration_ms": dur_ms})
                    passed += 1
    except Exception as exc:
        failures.append({"test": "xml_parse_error", "error": str(exc)})
    finally:
        try:
            os.unlink(xml_path)
        except OSError:
            pass

    total = len(tests)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "duration": duration,
        "tests": tests,
        "failures": failures,
    }
