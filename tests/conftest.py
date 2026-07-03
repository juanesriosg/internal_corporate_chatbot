from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.backend.config import LLMProvider, Settings
from app.backend.main import app
from app.backend.rag.ingest import ingest_corpus


@pytest.fixture()
def local_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("MOCK_DATA_DIR", "mock_data")
    monkeypatch.setenv("LOCAL_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    return Settings(
        llm_provider=LLMProvider.LOCAL,
        mock_data_dir=Path("mock_data"),
        local_artifact_dir=tmp_path / "artifacts",
    )


@pytest.fixture(scope="session")
def session_ingested_settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    settings = Settings(
        llm_provider=LLMProvider.LOCAL,
        mock_data_dir=Path("mock_data"),
        local_artifact_dir=tmp_path_factory.mktemp("rag-artifacts"),
    )
    ingest_corpus(settings.mock_data_dir, settings.local_artifact_dir, settings)
    return settings


@pytest.fixture()
def ingested_settings(
    session_ingested_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> Settings:
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("MOCK_DATA_DIR", str(session_ingested_settings.mock_data_dir))
    monkeypatch.setenv("LOCAL_ARTIFACT_DIR", str(session_ingested_settings.local_artifact_dir))
    return session_ingested_settings


@pytest.fixture()
def api_client(
    ingested_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("MOCK_DATA_DIR", str(ingested_settings.mock_data_dir))
    monkeypatch.setenv("LOCAL_ARTIFACT_DIR", str(ingested_settings.local_artifact_dir))
    with TestClient(app) as client:
        yield client
