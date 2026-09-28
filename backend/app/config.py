from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    mcp_url: str = "http://localhost:8000/mcp"
    sqlite_path: Path = Path("data/runtime/nexora.db")
    runtime_dir: Path = Path("data/runtime")
    api_port: int = 8080
    max_history_messages: int = 16
    max_tool_hops: int = 8
    tool_timeout_seconds: float = 8.0


settings = Settings()
