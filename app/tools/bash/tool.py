import subprocess
from typing import Any
from app.tools.base import BaseTool


class BashTool(BaseTool):
    name = "Bash"
    description = "Execute a shell command"
    parameters = {
        "type": "object",
        "required": ["command"],
        "properties": {
            "command": {"type": "string", "description": "The command to execute"}
        },
    }

    def execute(self, arguments: dict[str, Any]) -> str:
        process = subprocess.run(
            arguments["command"], shell=True, capture_output=True, text=True
        )
        return process.stdout if process.returncode == 0 else process.stderr
