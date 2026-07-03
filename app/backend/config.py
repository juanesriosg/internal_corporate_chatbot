from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    LOCAL = "local"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: LLMProvider = LLMProvider.OPENAI

    openai_api_key: str = ""
    openai_chat_model: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_temperature: float = 0.2
    openai_max_output_tokens: int = 700
    openai_timeout_seconds: float = 60

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = ""
    azure_openai_chat_deployment: str = ""
    azure_openai_embedding_deployment: str = ""

    mock_data_dir: Path = Path("mock_data")
    local_artifact_dir: Path = Path(".local")
    vector_backend: str = "chroma"
    chroma_collection: str = "corporate_chunks"

    tenant_id: str = "default"
    local_embedding_dimensions: int = Field(default=384, ge=32)
    chunk_max_words: int = Field(default=220, ge=50)
    chunk_overlap_words: int = Field(default=45, ge=0)
    retrieval_top_k: int = Field(default=5, ge=1)
    retrieval_candidate_count: int = Field(default=40, ge=5)

    api_auth_enabled: bool = False
    api_basic_username: str = ""
    api_basic_password: str = ""
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    def require_openai_chat(self) -> None:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        if not self.openai_chat_model:
            raise ValueError("OPENAI_CHAT_MODEL is required when LLM_PROVIDER=openai.")

    def require_openai_embeddings(self) -> None:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        if not self.openai_embedding_model:
            raise ValueError("OPENAI_EMBEDDING_MODEL is required when LLM_PROVIDER=openai.")

    def require_azure_openai(self) -> None:
        missing = [
            name
            for name, value in [
                ("AZURE_OPENAI_API_KEY", self.azure_openai_api_key),
                ("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
                ("AZURE_OPENAI_API_VERSION", self.azure_openai_api_version),
                ("AZURE_OPENAI_CHAT_DEPLOYMENT", self.azure_openai_chat_deployment),
                ("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", self.azure_openai_embedding_deployment),
            ]
            if not value
        ]
        if missing:
            raise ValueError(
                "Missing Azure OpenAI settings for LLM_PROVIDER=azure_openai: "
                + ", ".join(missing)
            )


def get_settings() -> Settings:
    return Settings()
