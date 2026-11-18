from typing import Any
from app.skills import SkillService
from app.tools.base import BaseTool


class SkillTool(BaseTool):
    name = "Skill"
    description = "Load a skill's instructions into the conversation"
    parameters = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string", "description": "The name of the skill to use"},
            "args": {
                "type": "string",
                "description": "Optional arguments for the skill",
            },
        },
    }

    def __init__(self, skill_service: SkillService | None = None) -> None:
        self.skill_service = skill_service or SkillService()

    def execute(self, arguments: dict[str, Any]) -> str:
        return self.skill_service.load_skill(
            arguments["name"], arguments.get("args", "")
        )
