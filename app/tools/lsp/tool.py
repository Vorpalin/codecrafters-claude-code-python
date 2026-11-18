
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import url2pathname

from app.tools.base import BaseTool
from app.lsp import LSPClient


class LspTool(BaseTool):
    name = "LSP"
    description = (
        "Finds the definition of a symbol in a source file. "
        "Returns the file path and position of the definition."
    )

    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["goToDefinition"],
            },
            "filePath": {
                "type": "string",
                "description": "Absolute path, or a path relative to the agent's current working directory.",
            },
            "line": {
                "type": "integer",
                "minimum": 1,
                "description": "1-based line number of the symbol.",
            },
            "character": {
                "type": "integer",
                "minimum": 1,
                "description": "1-based character offset in UTF-16 code units.",
            },
        },
        "required": ["operation", "filePath", "line", "character"],
    }

    def __init__(self, lsp_client: LSPClient | None = None) -> None:
        self.lsp_client = lsp_client or LSPClient.from_environment()

    def execute(self, arguments: dict[str, Any]) -> str:
        if arguments.get("operation") != "goToDefinition":
            return "Unsupported LSP operation."

        if self.lsp_client is None:
            return "Error: LSP client is not configured."

        path = Path(arguments["filePath"]).expanduser().resolve()
        line = arguments["line"]
        character = arguments["character"]

        if not path.is_file():
            return f"Error: File not found: {path}"

        language_id = self.lsp_client.extension_to_language.get(path.suffix)
        if language_id is None:
            return f"Error: Unsupported file extension: {path.suffix}"

        source = path.read_text(encoding="utf-8")
        uri = path.as_uri()

        self.lsp_client.notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id,
                    "version": 1,
                    "text": source,
                }
            },
        )

        result = self.lsp_client.request(
            "textDocument/definition",
            {
                "textDocument": {"uri": uri},
                "position": {
                    "line": line - 1,
                    "character": character - 1,
                },
            },
        )

        if not result:
            return "No definition found."

        # Support both Location and LocationLink responses.
        location = result[0] if isinstance(result, list) else result

        target_uri = location.get("uri") or location.get("targetUri")
        target_range = (
            location.get("range")
            or location.get("targetSelectionRange")
        )

        if not target_uri or not target_range:
            return "Error: Invalid LSP definition response."

        target_path = Path(
            url2pathname(urlparse(target_uri).path)
        )

        start = target_range["start"]

        return (
            "Definition found:\n"
            f"File: {target_path}\n"
            f"Line: {start['line'] + 1}\n"
            f"Character: {start['character'] + 1}"
        )
