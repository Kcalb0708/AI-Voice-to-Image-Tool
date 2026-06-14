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

        files = {
            "file": (
                filename or "speech.webm",
                audio,
                content_type or "application/octet-stream",
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
            raise ProviderResponseError(f"语音识别服务返回状态码 {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderResponseError("无法读取语音识别服务的响应。") from exc

        text = extract_text(payload)
        if not text:
            raise ProviderResponseError("语音识别服务没有返回文本。")
        return text


def extract_text(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("text", "transcript", "result"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""
