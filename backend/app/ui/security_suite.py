from pathlib import Path

SECURITY_SUITE_HTML = (Path(__file__).parent.parent / "templates" / "security_suite.html").read_text()
