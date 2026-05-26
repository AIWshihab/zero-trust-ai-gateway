from pathlib import Path

LOGS_HTML = (Path(__file__).parent.parent / "templates" / "logs.html").read_text()
