from pathlib import Path
from typing import Any

from app.tools.base import BaseTool
from app.lsp import LSPClient


class WriteTool(BaseTool):
    name = "Write"
    description = "Write content to a file"

    parameters = {
        "type": "object",
        "required": ["file_path", "content"],
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path of the file to write to",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
    }

    def __init__(
        self,
        lsp_client: LSPClient | None = None,
        document_versions: dict[str, int] | None = None,
    ) -> None:
        self.lsp_client = lsp_client
        self.document_versions = (
            document_versions if document_versions is not None else {}
        )

    def execute(self, arguments: dict[str, Any]) -> str:
        path = Path(arguments["file_path"]).expanduser().resolve()
        content = arguments["content"]

        # Save the file before notifying the language server.
        path.write_text(content, encoding="utf-8")

        if self.lsp_client is None:
            return content

        if path.suffix not in self.lsp_client.extension_to_language:
            return content

        uri = path.as_uri()
        version = self.document_versions.get(uri, 0) + 1

        self.lsp_client.notify(
            "textDocument/didChange",
            {
                "textDocument": {
                    "uri": uri,
                    "version": version,
                },
                "contentChanges": [{"text": content}],
            },
        )

        self.document_versions[uri] = version

        return content
