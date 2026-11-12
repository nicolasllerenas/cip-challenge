import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CIP_AGENTS_")

    library_url: str = "http://127.0.0.1:8001"
    llm_provider: Literal["auto", "anthropic", "offline"] = "auto"
    model_fast: str = "claude-haiku-5-5"
    model_strong: str = "claude-opus-5-5"
    evidence_per_section: int = 8
    max_repairs: int = 1
    request_timeout_seconds: float = 120.0

    @property
    def resolved_provider(self) -> Literal["anthropic", "offline"]:
        if self.llm_provider != "auto":
            return self.llm_provider
        has_credentials = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        return "anthropic" if has_credentials else "offline"
