from services.agents.open_interpreter import OpenInterpreterAdapter


adapter = OpenInterpreterAdapter()

print("Available:", adapter.is_available())

result = adapter.run_task(
    task="List the files in this directory. Do not modify anything.",
    workspace=r"C:\Users\ongzh\OI-Test",
    skip_git_repo_check=True,
)

print("\nStatus:", result["status"])
print("\nSuccess:", result["success"])
print("\nResult:")
print(result["result"])

if result["error"]:
    print("\nError:")
    print(result["error"])