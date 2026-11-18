from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname


class LSPDiagnostics:
    def __init__(self, lsp_client, document_versions):
        self.lsp_client = lsp_client
        self.document_versions = document_versions
        self.cursor = 0
        self.last_reported = {}

    def poll(self) -> str:
        if self.lsp_client is None:
            return ""

        response = self.lsp_client.notifications(
            after=self.cursor,
            timeout_ms=0,
        )

        self.cursor = response.get("cursor", self.cursor)

        latest_reports = {}

        for notification in response.get("notifications", []):
            if notification.get("method") != "textDocument/publishDiagnostics":
                continue

            params = notification.get("params", {})
            uri = params.get("uri")

            if not uri:
                continue

            version = params.get("version")

            if version is not None:
                expected = self.document_versions.get(uri)
                if version != expected:
                    continue

            latest_reports[uri] = params.get("diagnostics", [])

        output = []

        for uri, diagnostics in latest_reports.items():
            parsed_uri = urlparse(uri)
            path = Path(url2pathname(parsed_uri.path))

            try:
                relative_path = path.relative_to(Path.cwd())
            except ValueError:
                relative_path = path

            current = set()
            new_diagnostics = []

            for diagnostic in diagnostics:
                start = diagnostic.get("range", {}).get("start", {})
                message = diagnostic.get("message", "")

                line = start.get("line", 0)
                character = start.get("character", 0)

                key = (
                    message,
                    diagnostic.get("severity"),
                    line,
                    character,
                )

                current.add(key)

                if key not in self.last_reported.get(uri, set()):
                    new_diagnostics.append(
                        f"  [Line {line + 1}:{character + 1}] {message}"
                    )

            self.last_reported[uri] = current

            if new_diagnostics:
                output.append(f"{relative_path}:\n" + "\n".join(new_diagnostics))

        if not output:
            return ""

        return (
            "<new-diagnostics>The following new diagnostic issues "
            "were detected:\n\n" + "\n\n".join(output) + "</new-diagnostics>"
        )
