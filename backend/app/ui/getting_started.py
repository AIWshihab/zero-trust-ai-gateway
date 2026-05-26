from pathlib import Path

GETTING_STARTED_HTML = (Path(__file__).parent.parent / "templates" / "getting_started.html").read_text()
