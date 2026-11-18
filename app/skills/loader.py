from pathlib import Path

class SkillLoader:
    def __init__(self, skills_directory: str | Path = ".claude/skills") -> None:
        self.skills_directory = Path(skills_directory)

    def list_skills(self) -> list[tuple[str, str]]:
        if not self.skills_directory.is_dir():
            return []
        result = []
        for path in sorted(self.skills_directory.glob("*/SKILL.md")):
            metadata, _ = self.parse_file(path)
            result.append((metadata.get("name", path.parent.name), metadata.get("description", "")))
        return result

    def load(self, name: str) -> tuple[dict[str, str], str]:
        path = self.skills_directory / name / "SKILL.md"
        if not path.is_file():
            raise FileNotFoundError(f"Skill not found: {name}")
        return self.parse_file(path)

    @staticmethod
    def parse_file(path: Path) -> tuple[dict[str, str], str]:
        text = path.read_text()
        metadata: dict[str, str] = {}
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) == 3:
                _, frontmatter, body = parts
                for line in frontmatter.strip().splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip().strip("\"'")
        return metadata, body.lstrip("\n")
