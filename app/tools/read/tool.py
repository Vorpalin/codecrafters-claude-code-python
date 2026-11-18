from pathlib import Path
from typing import Any
from app.tools.base import BaseTool


class ReadTool(BaseTool):
    name = "Read"
    description = "Read and return the contents of a file"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to read",
            }
        },
        "required": ["file_path"],
    }

    def execute(self, arguments: dict[str, Any]) -> str:
        return Path(arguments["file_path"]).read_text()
