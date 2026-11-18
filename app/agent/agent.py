from typing import Any
from openai import OpenAI
from app.tools import ToolRegistry

class Agent:
    def __init__(self, client: OpenAI, registry: ToolRegistry) -> None:
        self.client = client
        self.registry = registry

    def run(self, messages: list[Any]) -> str:
        while True:
            response = self.client.chat.completions.create(model="anthropic/claude-haiku-4.5", messages=messages, tools=self.registry.get_schemas())
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
                try:
                    result = self.registry.execute(tool_call.function.name, tool_call.function.arguments)
                except Exception as error:
                    result = f"Error: {error}"
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
