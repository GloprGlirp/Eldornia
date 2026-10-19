"""Lädt die zuletzt von GitHub Actions gebaute Web-Version des Clients nach client/export/web (für /play).

Schlägt der Download fehl, startet der Server trotzdem – /play zeigt dann einen Hinweis.
"""
import io
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = os.environ.get("GITHUB_REPO", "GloprGlirp/Eldornia")
URL = os.environ.get("WEB_BUILD_URL", f"https://github.com/{REPO}/releases/latest/download/eldornia-web.zip")
DST = Path(__file__).resolve().parents[1] / "client" / "export" / "web"

try:
    with urllib.request.urlopen(URL, timeout=60) as r:
        data = r.read()
    DST.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(DST)
    print(f"Web-Client entpackt nach {DST} ({len(data) // 1024} KB)")
except Exception as e:  # noqa: BLE001
    print(f"Web-Client konnte nicht geladen werden ({e}) – /play bleibt leer.", file=sys.stderr)
