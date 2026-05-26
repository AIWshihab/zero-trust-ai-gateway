from pathlib import Path

FIREWALL_ADMIN_HTML = (Path(__file__).parent.parent / "templates" / "firewall_admin.html").read_text()
