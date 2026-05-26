from pathlib import Path

TESTING_DASHBOARD_HTML = (Path(__file__).parent.parent / "templates" / "testing_dashboard.html").read_text()
