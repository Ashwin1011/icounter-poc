from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "nexorapass"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "nexora_docs"
    knowledge_dir: Path = Path("knowledge")
    structured_dir: Path = Path("data/structured")
    runtime_dir: Path = Path("data/runtime")
    mcp_port: int = 8000
    fail_mode: str = ""


settings = Settings()
