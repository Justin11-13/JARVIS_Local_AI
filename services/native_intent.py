"""Deterministic mapping for a small allowlist of native chat requests.

This is deliberately not an LLM or command parser.  A request must match one
of the narrow patterns below before JARVIS calls an existing native tool.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class NativeIntent:
    """A safe native tool call resolved from one known user-facing phrase."""

    function_name: str
    arguments: dict[str, str]
    description: str


def resolve_native_intent(user_input: str) -> NativeIntent | None:
    """Return a known-safe native action, or None when the phrase is ambiguous."""
    normalized = " ".join(user_input.strip().split())
    lowered = normalized.lower().rstrip("。！？!?.")

    if _is_system_status_request(lowered):
        return NativeIntent(
            function_name="get_system_info",
            arguments={},
            description="读取本机 CPU 与内存使用情况。",
        )

    if lowered in {
        "列出项目",
        "列出我的项目",
        "我的项目",
        "我有哪些项目",
        "我有哪些 project",
        "显示项目",
        "显示所有项目",
        "list projects",
        "show projects",
        "show my projects",
        "what projects do i have",
        "what are my projects",
    }:
        return NativeIntent(
            function_name="list_projects",
            arguments={},
            description="列出已注册的开发项目。",
        )

    git_status_match = re.fullmatch(
        r"(?:查看|检查|显示|check|show)\s+(.+?)\s*(?:的\s*)?(?:git\s*status|git状态)",
        lowered,
        flags=re.IGNORECASE,
    )
    if git_status_match:
        return NativeIntent(
            function_name="git_status",
            arguments={"project_name": git_status_match.group(1).strip()},
            description="读取已注册项目的 Git 状态。",
        )

    app_name = _extract_app_name(lowered)
    if app_name:
        return NativeIntent(
            function_name="open_app",
            arguments={"app": app_name},
            description=f"打开已发现的 Windows 应用：{app_name}。",
        )

    return None


def _is_system_status_request(text: str) -> bool:
    has_cpu = "cpu" in text or "处理器" in text
    has_memory = "ram" in text or "内存" in text or "memory" in text
    chinese_status_words = {"多少", "用量", "使用率", "状态", "现在", "用了"}
    english_status_words = {"usage", "status", "current", "show", "check", "how much"}

    if not (has_cpu or has_memory):
        return False

    # Prefer a missed telemetry shortcut to treating a general definition
    # question as permission to inspect the user's computer.
    if text.startswith(("what is ", "what are ")):
        return False

    if any(word in text for word in chinese_status_words):
        return True

    # English definition questions such as "What is RAM?" must not read local
    # telemetry.  Require an explicit device/status cue instead.
    english_device_cues = {"my ", "system", "computer", "usage", "status", "current"}
    return (
        any(word in text for word in english_status_words)
        and any(cue in text for cue in english_device_cues)
    )


def _extract_app_name(text: str) -> str | None:
    match = re.fullmatch(
        r"(?:请|帮我|please|can you)?\s*(?:打开|启动|open|launch)\s+(.+)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    app_name = match.group(1).strip()
    # Compound requests must not silently execute only their first clause.
    blocked_fragments = {"然后", "再", "并且", "and then", " then ", ";", "；"}
    if not app_name or any(fragment in app_name for fragment in blocked_fragments):
        return None

    return app_name
