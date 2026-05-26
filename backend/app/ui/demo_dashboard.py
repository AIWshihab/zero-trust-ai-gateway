from pathlib import Path

DEMO_DASHBOARD_HTML = (Path(__file__).parent.parent / "templates" / "demo_dashboard.html").read_text()
