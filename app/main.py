import argparse
from openai import OpenAI
from app.agent import Agent
from app.config import Settings
from app.skills import SkillService
from app.tools import BashTool, LspTool, ReadTool, SkillTool, ToolRegistry, WriteTool


def build_agent(client: OpenAI) -> tuple[Agent, SkillService]:
    skills = SkillService()
    registry = ToolRegistry([ReadTool(), LspTool(), WriteTool(), BashTool(), SkillTool(skills)])
    agent = Agent(client, registry)
    skills.set_subagent_runner(agent.run)
    return agent, skills


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", required=True)
    args = parser.parse_args()
    settings = Settings.from_environment()
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)
    agent, skills = build_agent(client)
    descriptions = skills.get_skills()
    messages = [
        {"role": "system", "content": "You have access to the following skills:\n\n" + "\n".join(descriptions) + "\n\nIf a skill matches the user's request, call the Skill tool with its name and follow the instructions it returns."},
        {"role": "user", "content": skills.get_content(args.p)},
    ]
    agent.run(messages)


if __name__ == "__main__":
    main()
