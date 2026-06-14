from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import Settings, get_settings
from app.errors import ProviderConfigurationError, ProviderResponseError
from app.models import AsrResponse
from app.services.asr_client import ASRClient

router = APIRouter(prefix="/api", tags=["语音识别"])


async def get_asr_client(settings: Settings = Depends(get_settings)) -> ASRClient:
    return ASRClient(settings)


@router.post("/asr", response_model=AsrResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    client: ASRClient = Depends(get_asr_client),
) -> AsrResponse:
    content = await audio.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="音频文件为空，请重新录制。")

    try:
        text = await client.transcribe(audio.filename or "speech.webm", audio.content_type or "", content)
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return AsrResponse(text=text)
