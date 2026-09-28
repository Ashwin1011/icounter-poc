from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server.graph import graph
from mcp_server.rag import rag
from mcp_server.settings import settings


def wait_for(check, name: str, attempts: int = 30, delay: float = 2.0) -> None:
    last = None
    for _ in range(attempts):
        result = check()
        if result.get("ok"):
            print(f"{name} is ready")
            return
        last = result
        time.sleep(delay)
    raise RuntimeError(f"{name} did not become ready: {last}")


def main() -> None:
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    wait_for(graph.health, "Neo4j")
    wait_for(rag.health, "Qdrant")
    seeded = graph.seed()
    print(f"Neo4j seeded: {seeded}")
    ingested = rag.ingest(settings.knowledge_dir)
    print(f"Qdrant ingested: {ingested}")
    marker = settings.runtime_dir / "bootstrap.ok"
    marker.write_text("ok\n", encoding="utf-8")


if __name__ == "__main__":
    main()
