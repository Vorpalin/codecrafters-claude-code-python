from pathlib import Path
from typing import Any
from app.tools.base import BaseTool

class WriteTool(BaseTool):
    name = "Write"
    description = "Write content to a file"
    parameters = {"type": "object", "required": ["file_path", "content"], "properties": {"file_path": {"type": "string", "description": "The path of the file to write to"}, "content": {"type": "string", "description": "The content to write to the file"}}}

    def execute(self, arguments: dict[str, Any]) -> str:
        content = arguments["content"]
        Path(arguments["file_path"]).write_text(content)
        return content
