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
            "file_path": {"type": "string"},
            "content": {"type": "string"},
        },
    }

    def __init__(self, lsp_client=None, document_versions=None):
        self.lsp_client = lsp_client
        self.document_versions = (
            document_versions if document_versions is not None else {}
        )

    def execute(self, arguments: dict[str, Any]) -> str:
        path = Path(arguments["file_path"]).expanduser().resolve()
        content = arguments["content"]

        path.write_text(content, encoding="utf-8")

        if self.lsp_client is None:
            return content

        language_id = self.lsp_client.extension_to_language.get(path.suffix)
        if language_id is None:
            return content

        uri = path.as_uri()

        if uri in self.document_versions:
            version = self.document_versions[uri] + 1

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
        else:
            version = 1

            self.lsp_client.notify(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": language_id,
                        "version": version,
                        "text": content,
                    }
                },
            )

        self.document_versions[uri] = version

        return content
