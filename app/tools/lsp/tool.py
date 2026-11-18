
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import url2pathname

from app.tools.base import BaseTool
from app.lsp import LSPClient

SUPPORTED_OPERATIONS = ["goToDefinition", "findReferences"]

class LspTool(BaseTool):
    name = "LSP"
    description = (
        "Provides language server operations such as finding symbol definitions "
        "and references in source files."
    )

    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": SUPPORTED_OPERATIONS,
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

    def _go_to_definition(
        self, path: Path, line: int, character: int
    ) -> str:
        uri = path.as_uri()

        self._open_document(path, uri)

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
            f"Defined in {path}:{start['line'] + 1}:{start['character'] + 1}"
        )

    def _find_references(
        self, path: Path, line: int, character: int
    ) -> str:
        uri = path.as_uri()

        self._open_document(path, uri)

        result = self.lsp_client.request(
            "textDocument/references",
            {
                "textDocument": {"uri": uri},
                "position": {
                    "line": line - 1,
                    "character": character - 1,
                },
                "context": {"includeDeclaration": True},
            },
        )

        if not result:
            return "No references found."

        references = []

        for location in result:
            reference_uri = location.get("uri")
            reference_range = location.get("range")

            if not reference_uri or not reference_range:
                continue

            reference_path = Path(
                url2pathname(urlparse(reference_uri).path)
            )
            start = reference_range["start"]

            references.append(
                f"{reference_path.name} at "
                f"{start['line'] + 1}:{start['character'] + 1}"
            )

        if not references:
            return "No references found."

        return "References found:\n" + "\n".join(references)

    def _open_document(self, path: Path, uri: str) -> None:
        language_id = self.lsp_client.extension_to_language.get(path.suffix)

        if language_id is None:
            raise ValueError(
                f"Unsupported file extension: {path.suffix}"
            )

        self.lsp_client.notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id,
                    "version": 1,
                    "text": path.read_text(encoding="utf-8"),
                }
            },
        )

    def execute(self, arguments: dict[str, Any]) -> str:
        operation = arguments.get("operation")

        if operation not in SUPPORTED_OPERATIONS:
            return "Unsupported LSP operation."

        if self.lsp_client is None:
            return "Error: LSP client is not configured."

        path = Path(arguments["filePath"]).expanduser().resolve()
        line = arguments["line"]
        character = arguments["character"]

        if not path.is_file():
            return f"Error: File not found: {path}"

        operations = {
            "goToDefinition": self._go_to_definition,
            "findReferences": self._find_references,
        }

        try:
            return operations[operation](path, line, character)
        except ValueError as error:
            return f"Error: {error}"
