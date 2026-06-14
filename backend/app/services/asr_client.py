import re
from typing import Any

import httpx

from app.config import Settings
from app.errors import ProviderConfigurationError, ProviderResponseError


class ASRClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def transcribe(self, filename: str, content_type: str, audio: bytes) -> str:
        try:
            self.settings.ensure_asr_configured()
        except RuntimeError as exc:
            raise ProviderConfigurationError(str(exc)) from exc

        headers = {"Authorization": f"Bearer {self.settings.asr_api_key}"}
        data: dict[str, str] = {}
        if self.settings.asr_model:
            data["model"] = self.settings.asr_model
        if self.settings.asr_language:
            data["language"] = self.settings.asr_language
        if self.settings.asr_response_format:
            data["response_format"] = self.settings.asr_response_format

        upload_content_type = normalize_audio_content_type(content_type)
        files = {
            "file": (
                filename or "speech.webm",
                audio,
                upload_content_type,
            )
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.asr_timeout_seconds) as client:
                response = await client.post(
                    self.settings.normalized_asr_api_url,
                    headers=headers,
                    data=data,
                    files=files,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            provider_message = extract_provider_error_message(exc.response)
            detail = f"语音识别服务返回状态码 {exc.response.status_code}"
            if provider_message:
                detail = f"{detail}：{provider_message}"
            raise ProviderResponseError(detail) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderResponseError("无法读取语音识别服务的响应。") from exc

        text = extract_text(payload)
        if not text:
            raise ProviderResponseError("语音识别服务没有返回文本，请确认录音中包含清晰语音。")
        return text


def extract_text(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("text", "transcript", "result"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def normalize_audio_content_type(content_type: str) -> str:
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type or "application/octet-stream"


def extract_provider_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = response.text

    message = extract_error_message(payload)
    if not message:
        return ""
    return sanitize_provider_message(message)


def extract_error_message(payload: Any) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            nested = error.get("message") or error.get("detail")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
        if isinstance(error, str) and error.strip():
            return error.strip()

        for key in ("detail", "message", "msg"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(payload, str):
        return payload.strip()
    return ""


def sanitize_provider_message(message: str) -> str:
    redacted = re.sub(r"Bearer\s+[\w.\-]+", "Bearer [已隐藏]", message)
    redacted = re.sub(r"sk-[\w\-]+", "[已隐藏]", redacted)
    redacted = " ".join(redacted.split())
    return redacted[:300]
