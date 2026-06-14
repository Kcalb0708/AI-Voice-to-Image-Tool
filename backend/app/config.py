from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    asr_api_url: str = ""
    asr_api_key: str = ""
    asr_model: str = "whisper-1"
    asr_timeout_seconds: float = Field(default=45.0, gt=0)

    llm_base_url: str = ""
    llm_api_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: float = Field(default=45.0, gt=0)
    llm_structured_output_method: str = "json_schema"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def ensure_asr_configured(self) -> None:
        missing = []
        if not self.normalized_asr_api_url:
            missing.append("ASR_API_URL")
        if not self.asr_api_key:
            missing.append("ASR_API_KEY")
        if missing:
            raise RuntimeError(f"缺少语音识别配置：{', '.join(missing)}")

    @property
    def normalized_asr_api_url(self) -> str:
        configured = self.asr_api_url.strip().rstrip("/")
        if not configured:
            return ""
        if configured.endswith("/audio/transcriptions"):
            return configured
        return f"{configured}/audio/transcriptions"

    def ensure_llm_configured(self) -> None:
        missing = []
        if not self.normalized_llm_base_url:
            missing.append("LLM_BASE_URL")
        if not self.llm_api_key:
            missing.append("LLM_API_KEY")
        if not self.llm_model:
            missing.append("LLM_MODEL")
        if missing:
            raise RuntimeError(f"缺少大模型配置：{', '.join(missing)}")

    @property
    def normalized_llm_base_url(self) -> str:
        configured = (self.llm_base_url or self.llm_api_url).strip().rstrip("/")
        if not configured:
            return ""
        if configured.endswith("/chat/completions"):
            return configured[: -len("/chat/completions")]
        return configured


@lru_cache
def get_settings() -> Settings:
    return Settings()
