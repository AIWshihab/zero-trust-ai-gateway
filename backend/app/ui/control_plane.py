from pathlib import Path

CONTROL_PLANE_HTML = (Path(__file__).parent.parent / "templates" / "control_plane.html").read_text()
