from pathlib import Path

import pytest
from cip_library.api import create_app
from cip_library.config import Settings
from cip_testkit import build_corpus
from fastapi.testclient import TestClient


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    folder = tmp_path / "articulos"
    build_corpus(folder)
    return folder


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(data_dir=tmp_path / "data")))
