import pytest

from app.models import DrawingCommand, DrawingElement
from app.services.svg_sanitizer import SanitizerError, sanitize_attrs, sanitize_command, sanitize_commands


def test_sanitize_add_circle_command() -> None:
    command = DrawingCommand(
        action="add",
        id="el_1",
        tag="circle",
        attrs={"cx": 100, "cy": "120", "r": 40, "fill": "red"},
    )

    sanitized = sanitize_command(command)

    assert sanitized.tag == "circle"
    assert sanitized.attrs["cx"] == 100.0
    assert sanitized.attrs["fill"] == "red"


def test_rejects_script_tag() -> None:
    command = DrawingCommand(action="add", id="el_1", tag="script", attrs={})

    with pytest.raises(SanitizerError):
        sanitize_command(command)


def test_rejects_event_handler_attr() -> None:
    with pytest.raises(SanitizerError):
        sanitize_attrs({"onload": "alert(1)"}, "circle")


def test_rejects_url_color() -> None:
    with pytest.raises(SanitizerError):
        sanitize_attrs({"fill": "url(http://example.test/a.svg)"}, "rect")


def test_sanitize_commands_skips_invalid_and_keeps_valid() -> None:
    commands = [
        DrawingCommand(action="add", id="el_1", tag="circle", attrs={"cx": 10, "cy": 10, "r": 5}),
        DrawingCommand(action="add", id="bad", tag="foreignObject", attrs={}),
        DrawingCommand(action="delete", id="el_1"),
    ]

    sanitized, warnings = sanitize_commands(commands)

    assert [command.action for command in sanitized] == ["add", "delete"]
    assert len(warnings) == 1


def test_modify_uses_target_tag_attribute_allowlist() -> None:
    element = DrawingElement(id="el_1", tag="circle", attrs={"cx": 10, "cy": 10, "r": 5})
    command = DrawingCommand(action="modify", id="el_1", attrs={"r": 12})

    sanitized = sanitize_command(command, {"el_1": element})

    assert sanitized.attrs["r"] == 12.0
