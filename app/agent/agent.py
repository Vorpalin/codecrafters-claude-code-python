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

    def _append_diagnostics(self, messages, diagnostics, tool_names):
        if not diagnostics:
            return

        # Preserve Write's original success result.
        for message in reversed(messages):
            if (
                isinstance(message, dict)
                and message.get("role") == "tool"
                and message.get("_tool_name") != "Write"
            ):
                message["content"] += "\n\n" + diagnostics
                return

        messages.append(
            {
                "role": "user",
                "content": diagnostics,
            }
        )

    def run(self, messages: list[Any]) -> str:
        tool_names = {}

        while True:
            if self.diagnostics is not None:
                diagnostic_text = self.diagnostics.poll()
                self._append_diagnostics(messages, diagnostic_text, tool_names)

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

                try:
                    result = self.registry.execute(
                        tool_name,
                        tool_call.function.arguments,
                    )
                except Exception as error:
                    result = f"Error: {error}"

                tool_result = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }

                tool_names[tool_call.id] = tool_name
                messages.append(tool_result)
