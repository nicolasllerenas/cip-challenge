from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CIP_GATEWAY_")

    library_url: str = "http://127.0.0.1:8001"
    agents_url: str = "http://127.0.0.1:8002"
    documents_url: str = "http://127.0.0.1:8003"
    data_dir: Path = Path(".data/gateway")
    exports_dir: Path = Path("exports")
    heartbeat_seconds: float = 15.0
    cors_origins: list[str] = [
        "tauri://localhost",
        "http://tauri.localhost",
        "http://localhost:1420",
        "http://localhost:5173",
    ]
