import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str

    @classmethod
    def from_environment(cls) -> "Settings":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        return cls(api_key, os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
