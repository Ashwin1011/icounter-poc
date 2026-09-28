from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from mcp_server.errors import err
from mcp_server.settings import settings

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
VECTOR_SIZE = 384


def _chunk_markdown(text: str, heading: str = "") -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_heading = heading or "Introduction"
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                sections.append((current_heading, "\n".join(current).strip()))
                current = []
            current_heading = line.lstrip("#").strip() or current_heading
            continue
        current.append(line)
    if current:
        sections.append((current_heading, "\n".join(current).strip()))

    chunks: list[tuple[str, str]] = []
    for section_heading, body in sections:
        if not body:
            continue
        words = body.split()
        if len(words) <= 180:
            chunks.append((section_heading, body))
            continue
        step = 140
        overlap = 30
        for start in range(0, len(words), step - overlap):
            piece = " ".join(words[start : start + step]).strip()
            if piece:
                chunks.append((section_heading, piece))
    return chunks


class RagStore:
    def __init__(self) -> None:
        self._client: QdrantClient | None = None
        self._embedder = None

    def connect(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(url=settings.qdrant_url, timeout=15)
        return self._client

    def embedder(self):
        if self._embedder is None:
            from fastembed import TextEmbedding

            cache = settings.runtime_dir / "fastembed"
            cache.mkdir(parents=True, exist_ok=True)
            self._embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=str(cache))
        return self._embedder

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self.embedder().embed(texts)]

    def health(self) -> dict[str, Any]:
        try:
            self.connect().get_collections()
            return {"ok": True, "service": "qdrant"}
        except Exception as exc:  # noqa: BLE001
            return err("database_unavailable", f"Qdrant is unavailable: {exc}", retryable=True)

    def ingest(self, knowledge_dir: Path) -> dict[str, int]:
        client = self.connect()
        if client.collection_exists(settings.qdrant_collection):
            client.delete_collection(settings.qdrant_collection)
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE),
        )
        points: list[qmodels.PointStruct] = []
        texts: list[str] = []
        payloads: list[dict[str, Any]] = []
        for path in sorted(knowledge_dir.rglob("*.md")):
            rel = path.relative_to(knowledge_dir).as_posix()
            title = path.stem.replace("-", " ")
            category = rel.split("/")[0]
            raw = path.read_text(encoding="utf-8")
            first_heading = ""
            match = re.search(r"^#\s+(.+)$", raw, re.MULTILINE)
            if match:
                first_heading = match.group(1).strip()
            for index, (heading, chunk) in enumerate(_chunk_markdown(raw, first_heading)):
                texts.append(chunk)
                payloads.append(
                    {
                        "path": rel,
                        "category": category,
                        "title": first_heading or title,
                        "heading": heading,
                        "chunk_index": index,
                        "text": chunk,
                    }
                )
        if not texts:
            return {"chunks": 0}
        vectors = self.embed(texts)
        for payload, vector in zip(payloads, vectors, strict=True):
            uid = hashlib.md5(f"{payload['path']}:{payload['chunk_index']}".encode()).hexdigest()
            points.append(
                qmodels.PointStruct(
                    id=uid,
                    vector=vector,
                    payload=payload,
                )
            )
        client.upsert(collection_name=settings.qdrant_collection, points=points)
        return {"chunks": len(points)}

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        category: str | None = None,
    ) -> dict[str, Any]:
        try:
            client = self.connect()
            vector = self.embed([query])[0]
            query_filter = None
            if category:
                query_filter = qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="category",
                            match=qmodels.MatchValue(value=category),
                        )
                    ]
                )
            hits = client.query_points(
                collection_name=settings.qdrant_collection,
                query=vector,
                query_filter=query_filter,
                limit=max(1, min(limit, 8)),
                score_threshold=0.25,
            )
        except Exception as exc:  # noqa: BLE001
            return err("database_unavailable", f"Qdrant search failed: {exc}", retryable=True)

        results = []
        for hit in hits.points:
            payload = hit.payload or {}
            results.append(
                {
                    "text": payload.get("text", ""),
                    "score": float(hit.score),
                    "citation": {
                        "title": payload.get("title"),
                        "path": payload.get("path"),
                        "heading": payload.get("heading"),
                    },
                }
            )
        if not results:
            return {
                "results": [],
                "message": "no matching documents",
            }
        return {"results": results}


rag = RagStore()
