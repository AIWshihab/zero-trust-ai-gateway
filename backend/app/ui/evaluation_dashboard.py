from pathlib import Path

EVALUATION_DASHBOARD_HTML = (Path(__file__).parent.parent / "templates" / "evaluation_dashboard.html").read_text()
