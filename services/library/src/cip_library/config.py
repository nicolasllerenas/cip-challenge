from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CIP_LIBRARY_")

    data_dir: Path = Path(".data/library")
    embedder: Literal["hashing", "fastembed"] = "hashing"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: int = 1200
    chunk_overlap: int = 150
    crossref_enabled: bool = False
    crossref_mailto: str | None = None
