import pytest

from app.config import Settings


def test_missing_asr_configuration_is_explicit() -> None:
    settings = Settings(asr_api_url="", asr_api_key="", _env_file=None)

    with pytest.raises(RuntimeError, match="ASR_API_URL"):
        settings.ensure_asr_configured()


def test_cors_origins_are_split() -> None:
    settings = Settings(cors_origins="http://a.test, http://b.test ,,", _env_file=None)

    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]


def test_llm_api_url_is_normalized_for_langchain() -> None:
    settings = Settings(llm_api_url="https://api.example.test/v1/chat/completions", _env_file=None)

    assert settings.normalized_llm_base_url == "https://api.example.test/v1"


def test_asr_base_url_is_normalized_to_transcription_endpoint() -> None:
    settings = Settings(asr_api_url="https://api.example.test/v1", _env_file=None)

    assert settings.normalized_asr_api_url == "https://api.example.test/v1/audio/transcriptions"


def test_asr_transcription_endpoint_is_preserved() -> None:
    settings = Settings(asr_api_url="https://api.example.test/v1/audio/transcriptions", _env_file=None)

    assert settings.normalized_asr_api_url == "https://api.example.test/v1/audio/transcriptions"
