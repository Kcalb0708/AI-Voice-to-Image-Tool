from app.services.llm_client import LLMInterpretResponse, convert_llm_response


def test_convert_llm_attribute_list_to_public_command_attrs() -> None:
    response = LLMInterpretResponse.model_validate(
        {
            "commands": [
                {
                    "action": "add",
                    "id": "el_1",
                    "tag": "circle",
                    "attrs": [
                        {"name": "cx", "value": 480},
                        {"name": "cy", "value": 270},
                        {"name": "r", "value": 80},
                        {"name": "fill", "value": "red"},
                    ],
                    "text": None,
                }
            ],
            "reply": "已添加红色圆形。",
        }
    )

    converted = convert_llm_response(response)

    assert converted.commands[0].attrs == {"cx": 480, "cy": 270, "r": 80, "fill": "red"}
    assert converted.reply == "已添加红色圆形。"
