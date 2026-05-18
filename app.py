import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

if os.environ.get("VERCEL"):
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url or "sqlite" in db_url.lower():
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////tmp/itwin_ops.db"

from app.main import app  # noqa: E402
