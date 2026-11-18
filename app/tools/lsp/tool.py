import subprocess
from typing import Any
from app.tools.base import BaseTool

class LspTool(BaseTool):
    name = "LSP"
    description = "Returns the file, line, and character where a symbol is defined."
    parameters = {"type": "object",
      "properties": {
        "operation": {
          "type": "string",
          "enum": ["goToDefinition"]
        },
        "filePath": {
          "type": "string",
          "description": "Absolute path, or a path relative to the agent's current working directory."
        },
        "line": {
          "type": "integer",
          "minimum": 1,
          "description": "1-based line number of the symbol."
        },
        "character": {
          "type": "integer",
          "minimum": 1,
          "description": "1-based character offset in UTF-16 code units (same as character count for ASCII)."
        }
      },
      "required": ["operation", "filePath", "line", "character"]
    }

    def execute(self, arguments: dict[str, Any]) -> str:
        operation = arguments.get("operation", "")
        filePath = arguments.get("filePath", "")
        line = arguments.get("line", 1)
        character = arguments.get("character")

        if operation == "goToDefinition":
            return f"Defined in {filePath}{line}:{character}"
        
        return "LSP is not implemented yet"
