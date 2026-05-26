from pathlib import Path

SIGNUP_HTML = (Path(__file__).parent.parent / "templates" / "signup.html").read_text()
