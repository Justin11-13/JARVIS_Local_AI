from ollama import chat

from skills.files import (
    list_files,
    read_file,
    search_files,
)
from skills.git import (
    git_status,
)
from skills.project import (
    get_project_info,
    list_projects,
    open_project,
)
from skills.system import (
    get_system_info,
    open_app,
)

MODEL = "qwen3:8b"


SYSTEM_PROMPT = """
You are JARVIS, a local Windows AI assistant.

Rules:
- Reply mainly in Chinese.
- Complete every part of the user's request.
- A single request may require multiple tool calls.
- Continue using tools until the entire request is completed.
- Use open_app when the user asks to open an installed Windows application.
- The open_app tool automatically searches the Windows application registry, so do not assume an application is unsupported before calling the tool.
- Use get_system_info when the user asks about CPU or RAM.
- Use list_projects when the user asks what projects exist.
- Use get_project_info when the user asks about a registered project.
- Use open_project when the user asks to open a registered project.
- Use git_status when the user asks about the Git status of a project.
- Never invent project paths.
- Never invent Git information.
- Never claim that an action succeeded unless a tool confirmed it.
- Never invent tools.
- Keep responses concise.
- Use list_files when the user asks what files or folders exist in a project.
- Use read_file when the user asks to inspect or read a project file.
- Use search_files when the user asks to find code, text, classes, functions, routes, models, or keywords inside a project.
- File tools are read-only. Do not claim to modify files.
- When referring to the root folder of a project, use "." as relative_path, not "/" or an absolute path.
"""


AVAILABLE_TOOLS = {
    "open_app": open_app,
    "get_system_info": get_system_info,
    "list_projects": list_projects,
    "get_project_info": get_project_info,
    "open_project": open_project,
    "git_status": git_status,
    "list_files": list_files,
    "read_file": read_file,
    "search_files": search_files,
}


TOOLS = [
    open_app,
    get_system_info,
    list_projects,
    get_project_info,
    open_project,
    git_status,
    list_files,
    read_file,
    search_files,
]


def execute_tool(tool_call):
    function_name = tool_call.function.name
    arguments = tool_call.function.arguments

    function_to_call = AVAILABLE_TOOLS.get(function_name)

    print(f"\n[JARVIS Tool] {function_name}({arguments})")

    if not function_to_call:
        return f"Tool '{function_name}' is not available."

    try:
        return function_to_call(**arguments)

    except Exception as error:
        return f"Tool '{function_name}' failed: {error}"


def run_jarvis():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    print()
    print("=" * 60)
    print("JARVIS Local v0.4")
    print(f"Model: {MODEL}")
    print("输入 exit 退出")
    print("=" * 60)

    while True:
        user_input = input("\nYou > ").strip()

        if not user_input:
            continue

        if user_input.lower() in [
            "exit",
            "quit",
            "bye",
        ]:
            print("\nJARVIS > Goodbye.")
            break

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        try:
            # JARVIS Agent Loop
            for step in range(10):
                response = chat(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS,
                    think=False,
                )

                messages.append(response.message)

                tool_calls = response.message.tool_calls

                # 没有新的 Tool Call = 整个任务完成
                if not tool_calls:
                    print(
                        "\nJARVIS >",
                        response.message.content,
                    )
                    break

                # 执行这一轮的所有 Tools
                for tool_call in tool_calls:
                    result = execute_tool(tool_call)

                    print(
                        "[Tool Result]",
                        result,
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "content": str(result),
                            "tool_name": (tool_call.function.name),
                        }
                    )

            else:
                print("\nJARVIS > 任务执行步骤超过限制，已停止。")

        except Exception as error:
            print(
                "\n[JARVIS Error]",
                error,
            )


if __name__ == "__main__":
    run_jarvis()
