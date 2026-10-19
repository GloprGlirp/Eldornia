import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ.setdefault("ELDORNIA_DEBUG", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
