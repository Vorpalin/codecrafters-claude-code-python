from typing import Any

from openai import OpenAI

from app.tools import ToolRegistry
from app.lsp import LSPDiagnostics


class Agent:
    def __init__(
        self,
        client: OpenAI,
        registry: ToolRegistry,
        diagnostics: LSPDiagnostics | None = None,
    ) -> None:
        self.client = client
        self.registry = registry
        self.diagnostics = diagnostics

    def _collect_diagnostics(self, pending: list[str]) -> None:
        if self.diagnostics is None:
            return

        diagnostic_text = self.diagnostics.poll()
        if diagnostic_text:
            pending.append(diagnostic_text)

    def _append_diagnostics(
        self,
        messages: list[Any],
        pending: list[str],
        tool_names: dict[str, str],
    ) -> None:
        if not pending:
            return

        diagnostic_text = "\n\n".join(pending)
        pending.clear()

        for message in reversed(messages):
            if not isinstance(message, dict):
                continue

            if message.get("role") != "tool":
                continue

            tool_name = tool_names.get(message.get("tool_call_id"))

            if tool_name == "Write":
                continue

            message["content"] += "\n\n" + diagnostic_text
            return

        pending.append(diagnostic_text)

    def run(self, messages: list[Any]) -> str:
        tool_names: dict[str, str] = {}
        pending_diagnostics: list[str] = []

        while True:
            # Collect notifications before every model request.
            self._collect_diagnostics(pending_diagnostics)
            self._append_diagnostics(
                messages,
                pending_diagnostics,
                tool_names,
            )

            response = self.client.chat.completions.create(
                model="anthropic/claude-haiku-4.5",
                messages=messages,
                tools=self.registry.get_schemas(),
            )

            if not response.choices:
                raise RuntimeError("no choices in response")

            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            tool_calls = assistant_message.tool_calls

            if not tool_calls:
                return assistant_message.content or ""

            for tool_call in tool_calls:
                if tool_call.function is None:
                    continue

                tool_name = tool_call.function.name
                tool_names[tool_call.id] = tool_name

                try:
                    result = self.registry.execute(
                        tool_name,
                        tool_call.function.arguments,
                    )
                except Exception as error:
                    result = f"Error: {error}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

                self._collect_diagnostics(pending_diagnostics)
