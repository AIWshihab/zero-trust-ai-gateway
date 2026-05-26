from pathlib import Path

CHAT_HTML = (Path(__file__).parent.parent / "templates" / "chat.html").read_text()
