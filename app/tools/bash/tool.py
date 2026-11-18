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
            arguments["command"],
            shell=True,
            capture_output=True,
            text=True,
        )

        output = process.stdout

        if process.stderr:
            output += process.stderr

        if process.returncode != 0:
            output += f"\nCommand exited with code {process.returncode}"

        return output
