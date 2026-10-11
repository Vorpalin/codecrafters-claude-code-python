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
 }
]

def get_skills():
    path = ".claude/skills/"
    res = []
    for (folder, folders_in, files_in) in os.walk(path):
        for folder_in in folders_in:
            with open(f"{folder}{folder_in}/SKILL.md") as file:
                lines = file.readlines()
                name = lines[1].replace("name: ", "").replace("\n", "")
                description = lines[2].replace("description: ", "").replace("\n", "")
                res.append("- " + name + ": " + description)
    return res

def get_content(content: str):
    if content[0] != '/':
        return content
    else:
        content = content[1:]
        cmd = content.split(' ')
        cmd = list(filter(lambda a: a != '', cmd))
        length = len(cmd)

        res = ""

        if not length:
            return res

        with open(f".claude/skills/{cmd[0]}/SKILL.md") as file:
            lines = file.readlines()
            res = "\n".join(lines[5:])
            for i in range(length - 1):
                res.replace(f"${i}", cmd[i+1])
        return res

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    skills = get_skills()
    prompt=[
            { "role": "system", "content": "You have access to the following skills:\n\n" + "\n".join(skills)},
            {"role": "user", "content": get_content(args.p)}
    ]

    messages = prompt

    while True:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=TOOLS
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        #print("Logs from your program will appear here!", file=sys.stderr)

        messages.append(chat.choices[0].message)
        tool_calls = chat.choices[0].message.tool_calls

        if tool_calls == None or len(tool_calls) == 0:
            print(chat.choices[0].message.content)
            break

        for tool in tool_calls:

            if tool.function != None:

                result = ""
                tool_name = tool.function.name

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

                    command = tool_args["command"].split(" ")
                    p = subprocess.run(command, capture_output=True)

                    if p.returncode == 0:
                        result = p.stdout.decode()
                    else:
                        result = p.stderr.decode()

                message = {
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "content": result
                }

                messages.append(message)


if __name__ == "__main__":
    main()
