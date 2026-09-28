from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEST_RUNTIME = ROOT / "data" / "runtime-test"
TEST_RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ["STRUCTURED_DIR"] = str(ROOT / "data" / "structured")
os.environ["KNOWLEDGE_DIR"] = str(ROOT)
os.environ["RUNTIME_DIR"] = str(TEST_RUNTIME)
os.environ["SQLITE_PATH"] = str(TEST_RUNTIME / "nexora-test.db")
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "")

from backend.app.db import init_db  # noqa: E402

init_db()
