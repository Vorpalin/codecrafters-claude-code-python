import argparse
from openai import OpenAI
from app.agent import Agent
from app.config import Settings
from app.lsp import LSPDiagnostics, LSPClient
from app.skills import SkillService
from app.tools import BashTool, LspTool, ReadTool, SkillTool, ToolRegistry, WriteTool


def build_agent(
    client: OpenAI,
    lsp_client: LSPClient | None = None,
) -> tuple[Agent, SkillService]:
    skills = SkillService()
    document_versions: dict[str, int] = {}

    registry = ToolRegistry(
        [
            ReadTool(),
            LspTool(lsp_client, document_versions),
            WriteTool(lsp_client, document_versions),
            BashTool(),
            SkillTool(skills),
        ]
    )

    diagnostics = LSPDiagnostics(lsp_client, document_versions)

    agent = Agent(client, registry, diagnostics)

    return agent, skills


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", required=True)
    args = parser.parse_args()

    settings = Settings.from_environment()
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)

    lsp_client = LSPClient.from_environment()

    agent, skills = build_agent(client, lsp_client)
    descriptions = skills.get_skills()
    messages = [
        {
            "role": "system",
            "content": "You have access to the following skills:\n\n"
            + "\n".join(descriptions)
            + "\n\nIf a skill matches the user's request, call the Skill tool with its name and follow the instructions it returns.",
        },
        {"role": "user", "content": skills.get_content(args.p)},
    ]

    print(agent.run(messages))


if __name__ == "__main__":
    main()
