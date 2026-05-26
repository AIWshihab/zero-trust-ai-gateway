from pathlib import Path

SOC_DASHBOARD_HTML = (Path(__file__).parent.parent / "templates" / "soc_dashboard.html").read_text()
