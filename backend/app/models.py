from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Action = Literal["add", "modify", "delete", "clear", "export"]


class DrawingElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=64)
    tag: str = Field(min_length=1, max_length=32)
    attrs: dict[str, Any] = Field(default_factory=dict)
    text: str | None = Field(default=None, max_length=240)


class DrawingCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Action
    id: str | None = Field(default=None, max_length=64)
    tag: str | None = Field(default=None, max_length=32)
    attrs: dict[str, Any] = Field(default_factory=dict)
    text: str | None = Field(default=None, max_length=240)

    @field_validator("id", "tag")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "DrawingCommand":
        if self.action == "add":
            if not self.id:
                raise ValueError("新增指令必须包含 id")
            if not self.tag:
                raise ValueError("新增指令必须包含 tag")
        if self.action in {"modify", "delete"} and not self.id:
            raise ValueError(f"{self.action} 指令必须包含 id")
        return self


class AsrResponse(BaseModel):
    text: str


class InterpretRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=2000)
    elements: list[DrawingElement] = Field(default_factory=list, max_length=200)


class InterpretResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commands: list[DrawingCommand] = Field(default_factory=list, max_length=100)
    reply: str = Field(default="", max_length=500)
    warnings: list[str] = Field(default_factory=list, max_length=100)
