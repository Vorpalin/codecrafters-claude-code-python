from collections.abc import Callable
from app.skills.loader import SkillLoader


class SkillService:
    def __init__(self, loader: SkillLoader | None = None) -> None:
        self.loader = loader or SkillLoader()
        self._subagent_runner: Callable[[list[dict[str, str]]], object] | None = None

    def set_subagent_runner(
        self, runner: Callable[[list[dict[str, str]]], object]
    ) -> None:
        self._subagent_runner = runner

    def get_skills(self) -> list[str]:
        return [
            f"- {name}: {description}"
            for name, description in self.loader.list_skills()
        ]

    def parse_skill(self, name: str) -> tuple[dict[str, str], str]:
        return self.loader.load(name)

    def get_content(self, content: str) -> str:
        if not content or not content.startswith("/"):
            return content
        command = content.split()
        if not command:
            return ""
        skill_count = 1
        while skill_count < len(command) and command[skill_count].startswith("/"):
            skill_count += 1
        resolved = []
        for index in range(skill_count):
            name = command[index][1:]
            metadata, body = self.parse_skill(name)
            skill_text = (
                f"Skill: {name} (located at {self.loader.skills_directory / name})\n"
                "Paths in the instructions below are relative to that folder.\n\n"
                + body
            )
            arguments = command[skill_count:]
            for argument_index, argument in enumerate(arguments):
                skill_text = skill_text.replace("$" + str(argument_index), argument)
                skill_text = skill_text.replace(
                    f"$ARGUMENTS[{argument_index}]", argument
                )

            if metadata.get("context") == "fork":
                if self._subagent_runner is None:
                    raise RuntimeError("Subagent runner is not configured")

                skill_text = str(
                    self._subagent_runner([{"role": "user", "content": skill_text}])
                )
            resolved.append(skill_text)
        result = "\n".join(part for part in resolved if part)
        if len(command) != skill_count:
            result = result.replace("$ARGUMENTS", " ".join(command[skill_count:]))
        return result

    def load_skill(self, name: str, arguments: str = "") -> str:
        return self.get_content(f"/{name}" + (f" {arguments}" if arguments else ""))
