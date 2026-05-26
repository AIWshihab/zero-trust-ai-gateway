from pathlib import Path

DASHBOARD_HTML = (Path(__file__).parent.parent / "templates" / "dashboard.html").read_text()
