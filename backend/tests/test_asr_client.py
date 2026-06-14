import httpx

from app.services.asr_client import (
    extract_provider_error_message,
    normalize_audio_content_type,
)


def test_normalize_audio_content_type_strips_codec_parameters() -> None:
    assert normalize_audio_content_type("audio/webm;codecs=opus") == "audio/webm"


def test_normalize_audio_content_type_falls_back_for_empty_value() -> None:
    assert normalize_audio_content_type("") == "application/octet-stream"


def test_extract_provider_error_message_from_openai_style_payload() -> None:
    response = httpx.Response(
        500,
        json={"error": {"message": "model does not support this file type"}},
    )

    assert extract_provider_error_message(response) == "model does not support this file type"


def test_extract_provider_error_message_redacts_secret_like_values() -> None:
    response = httpx.Response(
        500,
        json={"detail": "upstream failed with Bearer sk-test-secret-token"},
    )

    assert extract_provider_error_message(response) == "upstream failed with Bearer [已隐藏]"
