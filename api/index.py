import os
import sys

# Ensure project root is on sys.path and is the working directory
# so all relative imports and static file paths in app/ resolve correctly.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_root)
sys.path.insert(0, _root)

# Vercel's filesystem is read-only outside /tmp.
# Override the SQLite path when running on Vercel so the DB can be created.
if os.environ.get("VERCEL"):
    _db = os.environ.get("DATABASE_URL", "")
    if not _db or "sqlite" in _db.lower():
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////tmp/itwin_ops.db"

# Vercel's Python runtime serves ASGI apps directly. Do not wrap FastAPI with
# Mangum here; Mangum expects AWS Lambda event shapes and causes
# FUNCTION_INVOCATION_FAILED on Vercel.
from app.main import app  # noqa: E402
