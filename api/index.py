import sys
import os
from pathlib import Path

# Add project root directory to sys.path so backend modules are importable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set VERCEL environment variable flag
os.environ.setdefault("VERCEL", "1")

from backend.main import app
from backend.database import init_db
from backend.seed_data import seed_events

# Ensure database is initialized and seeded on serverless cold start
try:
    init_db()
    seed_events()
except Exception as e:
    print(f"Vercel startup init notice: {e}")
