import re
from html import escape
from typing import Any

from app.models import DrawingCommand, DrawingElement


ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
POINTS_RE = re.compile(r"^-?\d+(\.\d+)?([,\s]+-?\d+(\.\d+)?)+([,\s]+-?\d+(\.\d+)?)*$")
PATH_RE = re.compile(r"^[MmZzLlHhVvCcSsQqTtAa0-9,\.\-\+\s]+$")
COLOR_RE = re.compile(
    r"^(#[0-9a-fA-F]{3,8}|[a-zA-Z]+|rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}(\s*,\s*(0|1|0?\.\d+))?\s*\))$"
)

ALLOWED_TAGS: set[str] = {
    "circle",
    "rect",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "path",
    "text",
}

COMMON_ATTRS: set[str] = {
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "opacity",
}

TAG_ATTRS: dict[str, set[str]] = {
    "circle": {"cx", "cy", "r"},
    "rect": {"x", "y", "width", "height", "rx", "ry"},
    "ellipse": {"cx", "cy", "rx", "ry"},
    "line": {"x1", "y1", "x2", "y2"},
    "polyline": {"points"},
    "polygon": {"points"},
    "path": {"d"},
    "text": {"x", "y", "font-size", "text-anchor", "dominant-baseline"},
}

ALL_ALLOWED_ATTRS = COMMON_ATTRS | set().union(*TAG_ATTRS.values())


class SanitizerError(ValueError):
    """Raised when SVG command content is not allowed."""


def sanitize_element_id(value: str | None) -> str:
    if not value or not ID_RE.fullmatch(value):
        raise SanitizerError("图形 id 无效")
    return value


def sanitize_tag(value: str | None) -> str:
    if not value or value not in ALLOWED_TAGS:
        raise SanitizerError("不支持的 SVG 标签")
    return value


def sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return escape(stripped[:240], quote=False)


def sanitize_attrs(attrs: dict[str, Any], tag: str | None = None) -> dict[str, str | float]:
    allowed = (TAG_ATTRS[tag] | COMMON_ATTRS) if tag else ALL_ALLOWED_ATTRS
    sanitized: dict[str, str | float] = {}

    for raw_key, raw_value in attrs.items():
        key = str(raw_key).strip()
        if key not in allowed:
            raise SanitizerError(f"不支持的 SVG 属性：{key}")
        if key.startswith("on") or key in {"style", "href", "xlink:href", "xmlns"}:
            raise SanitizerError(f"不安全的 SVG 属性：{key}")
        if raw_value is None:
            continue
        sanitized[key] = sanitize_attr_value(key, raw_value)

    return sanitized


def sanitize_attr_value(key: str, value: Any) -> str | float:
    raw = str(value).strip()
    if not raw:
        raise SanitizerError(f"{key} 的值为空")
    lowered = raw.lower()
    if any(token in lowered for token in ("javascript:", "data:", "url(", "<", ">")):
        raise SanitizerError(f"{key} 的值不安全")

    if key in {"fill", "stroke"}:
        if raw.lower() == "none" or COLOR_RE.fullmatch(raw):
            return raw
        raise SanitizerError(f"{key} 的颜色值无效")

    if key == "opacity":
        numeric = parse_number(raw, key)
        if 0 <= numeric <= 1:
            return numeric
        raise SanitizerError("opacity 必须在 0 到 1 之间")

    if key in {"stroke-linecap", "stroke-linejoin"}:
        allowed_values = {"butt", "round", "square", "miter", "bevel"}
        if raw in allowed_values:
            return raw
        raise SanitizerError(f"{key} 的值无效")

    if key == "points":
        if POINTS_RE.fullmatch(raw):
            return raw
        raise SanitizerError("points 值无效")

    if key == "d":
        if PATH_RE.fullmatch(raw):
            return raw
        raise SanitizerError("path 值无效")

    if key in {"text-anchor", "dominant-baseline"}:
        allowed_values = {"start", "middle", "end", "hanging", "central", "auto"}
        if raw in allowed_values:
            return raw
        raise SanitizerError(f"{key} 的值无效")

    numeric = parse_number(raw, key)
    if -10000 <= numeric <= 10000:
        return numeric
    raise SanitizerError(f"{key} 的值超出范围")


def parse_number(raw: str, key: str) -> float:
    if not NUMBER_RE.fullmatch(raw):
        raise SanitizerError(f"{key} 应为数字")
    return float(raw)


def sanitize_command(
    command: DrawingCommand,
    elements_by_id: dict[str, DrawingElement] | None = None,
) -> DrawingCommand:
    if command.action in {"clear", "export"}:
        return DrawingCommand(action=command.action)

    element_id = sanitize_element_id(command.id)

    if command.action == "delete":
        return DrawingCommand(action="delete", id=element_id)

    if command.action == "add":
        tag = sanitize_tag(command.tag)
        attrs = sanitize_attrs(command.attrs, tag)
        return DrawingCommand(
            action="add",
            id=element_id,
            tag=tag,
            attrs=attrs,
            text=sanitize_text(command.text),
        )

    target_tag = None
    if elements_by_id and element_id in elements_by_id:
        target_tag = sanitize_tag(elements_by_id[element_id].tag)
    attrs = sanitize_attrs(command.attrs, target_tag)
    return DrawingCommand(
        action="modify",
        id=element_id,
        attrs=attrs,
        text=sanitize_text(command.text),
    )


def sanitize_commands(
    commands: list[DrawingCommand],
    elements: list[DrawingElement] | None = None,
) -> tuple[list[DrawingCommand], list[str]]:
    elements_by_id = {element.id: element for element in elements or []}
    sanitized: list[DrawingCommand] = []
    warnings: list[str] = []

    for index, command in enumerate(commands):
        try:
            sanitized.append(sanitize_command(command, elements_by_id))
        except SanitizerError as exc:
            warnings.append(f"第 {index + 1} 条指令已跳过：{exc}")

    return sanitized, warnings
