from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """Common interface for all callable tools."""
    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    def execute(self, arguments: dict[str, Any]) -> str:
        """Execute the tool and return its textual result."""

    def to_openai_schema(self) -> dict[str, Any]:
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": self.parameters}}
