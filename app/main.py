import argparse
import os
import sys
import json
import subprocess

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

TOOLS = [
  {
    "type": "function",
    "function": {
        "name": "Read",
        "description": "Read and return the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read"
                }
            },
            "required": ["file_path"]
         }
    }
  },
  {
    "type": "function",
    "function": {
        "name": "Write",
        "description": "Write content to a file",
        "parameters": {
            "type": "object",
            "required": ["file_path", "content"],
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path of the file to write to"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            }
        }
    }
 },
 {
    "type": "function",
    "function": {
        "name": "Bash",
        "description": "Execute a shell command",
        "parameters": {
            "type": "object",
            "required": ["command"],
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute"
                }
            }
        }
    }
 },
 {
    "type": "function",
    "function": {
      "name": "Skill",
      "description": "Load a skill's instructions into the conversation",
      "parameters": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": { "type": "string", "description": "The name of the skill to use" },
          "args": { "type": "string", "description": "Optional arguments for the skill" }
        }
      }
    }
  }
]

def get_skills():
    path = ".claude/skills"
    res = []

    if not os.path.isdir(path):
        return res

    for folder_in in os.listdir(path):
        skill_file = skill_file = os.path.join(path, folder_in, "SKILL.md")
        if not os.path.isfile(skill_file):
            continue
        with open(skill_file) as file:
            lines = file.readlines()
            name = lines[1].replace("name: ", "").replace("\n", "")
            description = lines[2].replace("description: ", "").replace("\n", "")
            res.append("- " + name + ": " + description)
    return res

def parse_skill(path):
    with open(f"{path}/SKILL.md") as f:
        text = f.read()

    params = {}
    body = text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.strip().splitlines():
            if ":" in line:
                field, content = line.split(":", 1)
                params[field.strip()] = content.strip()

    return params, body

def get_content(content: str, client):
    if content[0] != '/':
        return content
    else:
        cmd = content.split(' ')
        cmd = list(filter(lambda a: a != '', cmd))
        length = len(cmd)

        res = ""

        if not length:
            return res

        nb_cmd = 1

        while (nb_cmd < length and cmd[nb_cmd][0] == '/'):
            nb_cmd += 1

        for i in range(nb_cmd):
            value = cmd[i][1:]
            path = f".claude/skills/{value}"
            meta, body = parse_skill(path)
            cur = f"Skill: {value} (located at {path})\nPaths in the instructions below are relative to that folder.\n\n"
            cur += body
            for j in range(length - nb_cmd):
                cur = cur.replace(f"${j}", cmd[j+nb_cmd])
                cur = cur.replace(f"$ARGUMENTS[{j}]", cmd[j+nb_cmd])
            if meta.get("context") == "fork":
                sub_messages = [{"role": "user", "content": cur}]
                answer = run_agent(client, sub_messages)
                cur = f"<skill name=\"{value}\">\nResult from subagent:\n{answer}\n</skill>"
            if res:
                res += "\n"
            res += cur

        if length != nb_cmd:
            args = cmd[nb_cmd:]
            res = res.replace("$ARGUMENTS", " ".join(args))

        return res

def run_agent(client, messages):
    while True:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=TOOLS
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")


        messages.append(chat.choices[0].message)
        tool_calls = chat.choices[0].message.tool_calls

        if tool_calls == None or len(tool_calls) == 0:
            print(chat.choices[0].message.content)
            break

        for tool in tool_calls:

            if tool.function != None:

                result = ""
                tool_name = tool.function.name
                try:
                    if tool_name == "Read":
                        tool_args = json.loads(tool.function.arguments)

                        with open(tool_args["file_path"]) as f:
                            lines = f.readlines()
                            result = "\n".join(lines)

                    elif tool_name == "Write":
                        tool_args = json.loads(tool.function.arguments)

                        with open(tool_args["file_path"], "w") as f:
                            result = tool_args["content"]
                            f.write(result)

                    elif tool_name == "Bash":
                        tool_args = json.loads(tool.function.arguments)

                        p = subprocess.run(tool_args["command"], shell=True, capture_output=True, text=True)

                        if p.returncode == 0:
                            result = p.stdout
                        else:
                            result = p.stderr

                    elif tool_name == "Skill":
                        tool_args = json.loads(tool.function.arguments)

                        skill_call = "/" + tool_args["name"] + " " + tool_args["args"]
                        result = get_content(skill_call)
                except Exception as e:
                    result = f"Error: {e}"

                message = {
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "content": result
                }

                messages.append(message)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    skills = get_skills()
    prompt=[
            {"role": "system", "content": "You have access to the following skills:\n\n" + "\n".join(skills) + "\n\nIf a skill matches the user's request, call the Skill tool with its name and follow the instructions it returns."},
            {"role": "user", "content": get_content(args.p, client)}
    ]

    messages = prompt

    run_agent(client, messages)


if __name__ == "__main__":
    main()
