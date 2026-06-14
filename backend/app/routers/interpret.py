from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.errors import ProviderConfigurationError, ProviderResponseError
from app.models import InterpretRequest, InterpretResponse
from app.services.llm_client import LLMClient
from app.services.svg_sanitizer import sanitize_commands

router = APIRouter(prefix="/api", tags=["指令理解"])


async def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    return LLMClient(settings)


@router.post("/interpret", response_model=InterpretResponse)
async def interpret_command(
    request: InterpretRequest,
    client: LLMClient = Depends(get_llm_client),
) -> InterpretResponse:
    try:
        payload = await client.interpret(
            request.text,
            [element.model_dump() for element in request.elements],
        )
        interpreted = InterpretResponse.model_validate(payload)
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="大模型返回的绘图指令格式无效。") from exc

    commands, warnings = sanitize_commands(interpreted.commands, request.elements)
    return InterpretResponse(commands=commands, reply=interpreted.reply, warnings=warnings)
