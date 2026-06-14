import json
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field

from app.config import Settings
from app.errors import ProviderConfigurationError, ProviderResponseError
from app.models import Action, DrawingCommand, InterpretResponse


SYSTEM_PROMPT = """你负责把语音识别文本转换为 SVG 绘图指令。
只返回一个 JSON 对象，格式如下：
{"commands":[...],"reply":"给用户看的简短中文回复"}。

支持的 action：
- add：必须包含 id、tag、attrs，可选 text
- modify：必须包含 id、attrs，可选 text
- delete：必须包含 id
- clear：不需要 id
- export：不需要 id

attrs 必须是属性列表，不是对象字典。示例：
{"action":"add","id":"el_1","tag":"circle","attrs":[{"name":"cx","value":480},{"name":"cy","value":270},{"name":"r","value":80},{"name":"fill","value":"red"}],"text":null}

允许的 SVG 标签：circle、rect、ellipse、line、polyline、polygon、path、text。
请使用稳定 id，例如 el_1。根据当前元素列表解析“刚才那个”“红色圆形”等指代。
尽量把坐标保持在 0..960 x 0..540 的 viewBox 内。
reply 必须使用中文。
不要输出标记文本、脚本、事件处理属性、style 属性、链接、外部引用或 markdown。
"""


class LLMAttribute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=64)
    value: str | float | int


class LLMCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Action
    id: str | None = Field(default=None, max_length=64)
    tag: str | None = Field(default=None, max_length=32)
    attrs: list[LLMAttribute] = Field(default_factory=list, max_length=40)
    text: str | None = Field(default=None, max_length=240)


class LLMInterpretResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commands: list[LLMCommand] = Field(default_factory=list, max_length=100)
    reply: str = Field(default="", max_length=500)


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def interpret(self, text: str, elements: list[dict[str, Any]]) -> InterpretResponse:
        try:
            self.settings.ensure_llm_configured()
        except RuntimeError as exc:
            raise ProviderConfigurationError(str(exc)) from exc

        model = init_chat_model(
            model=self.settings.llm_model,
            model_provider="openai",
            api_key=self.settings.llm_api_key,
            base_url=self.settings.normalized_llm_base_url,
            temperature=0,
            timeout=self.settings.llm_timeout_seconds,
        )
        structured_model = model.with_structured_output(
            LLMInterpretResponse,
            method=self.settings.llm_structured_output_method,
        )

        try:
            result = await structured_model.ainvoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(
                        content=json.dumps(
                            {"transcript": text, "elements": elements},
                            ensure_ascii=False,
                        )
                    ),
                ]
            )
            return convert_llm_response(result)
        except Exception as exc:
            raise ProviderResponseError("无法解析大模型返回的绘图指令。") from exc


def convert_llm_response(result: LLMInterpretResponse | dict[str, Any]) -> InterpretResponse:
    if isinstance(result, dict):
        result = LLMInterpretResponse.model_validate(result)
    if not isinstance(result, LLMInterpretResponse):
        raise ProviderResponseError("大模型结构化输出类型异常。")

    commands = [
        DrawingCommand(
            action=command.action,
            id=command.id,
            tag=command.tag,
            attrs={attribute.name: attribute.value for attribute in command.attrs},
            text=command.text,
        )
        for command in result.commands
    ]
    return InterpretResponse(commands=commands, reply=result.reply, warnings=[])
