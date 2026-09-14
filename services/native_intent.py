"""Bounded native-intent resolution and model-proposal parsing.

The first route remains deterministic: a request must match one of the narrow
patterns below before JARVIS calls an existing native tool.  Managed Luna may
also return a machine-readable *proposal* for an allowlisted tool when Core
explicitly asks for one.  The proposal is untrusted data; Core validates it,
applies permissions, and owns the confirmation/execution decision.
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
import json
import re
from typing import Iterable


@dataclass(frozen=True)
class NativeIntent:
    """A safe native tool call resolved from one known user-facing phrase."""

    function_name: str
    arguments: dict[str, str]
    description: str


@dataclass(frozen=True)
class NativeIntentProposal:
    """An untrusted candidate returned by the managed model for Core review."""

    function_name: str
    arguments: dict[str, str]
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return {
            "function_name": self.function_name,
            "arguments": dict(self.arguments),
            "confidence": self.confidence,
        }


INTENT_PROPOSAL_START = "[JARVIS_INTENT]"
INTENT_PROPOSAL_END = "[/JARVIS_INTENT]"
_INTENT_PROPOSAL_PATTERN = re.compile(
    re.escape(INTENT_PROPOSAL_START)
    + r"(.*?)"
    + re.escape(INTENT_PROPOSAL_END),
    flags=re.DOTALL,
)
_MIN_PROPOSAL_CONFIDENCE = 0.75

# This map covers every currently registered native tool.  It is only a
# bounded *proposal gate*: matching a phrase never selects or executes a
# function.  Luna still has to return a strict marker, and Core still applies
# the catalog/schema/path/permission checks before anything can run.
NATIVE_INTENT_FUZZY_ALIASES: dict[str, tuple[str, ...]] = {
    "open_app": (
        "open",
        "launch",
        "打开",
        "start app",
        "open app",
        "launch app",
        "run app",
        "打开应用",
        "启动应用",
        "打开软件",
        "启动软件",
    ),
    "get_system_info": (
        "system info",
        "system status",
        "system usage",
        "hardware status",
        "cpu",
        "memory",
        "ram",
        "cpu 使用",
        "内存",
        "系统信息",
        "系统状态",
    ),
    "list_projects": (
        "list projects",
        "show projects",
        "my projects",
        "project list",
        "项目",
        "项目列表",
        "我的项目",
    ),
    "get_project_info": (
        "project info",
        "project details",
        "about project",
        "details of project",
        "项目信息",
        "项目详情",
    ),
    "open_project": (
        "open project",
        "launch project",
        "project in vscode",
        "在 vscode 打开项目",
        "打开项目",
    ),
    "git_status": (
        "git status",
        "repository status",
        "repo status",
        "working tree status",
        "changes in project",
        "git状态",
        "仓库状态",
        "代码变更",
    ),
    "list_files": (
        "list files",
        "show files",
        "folder contents",
        "directory listing",
        "files in project",
        "文件列表",
        "文件夹内容",
        "目录内容",
    ),
    "read_file": (
        "read file",
        "view file",
        "show file contents",
        "open file contents",
        "读取文件",
        "查看文件",
        "文件内容",
    ),
    "search_files": (
        "search files",
        "find in files",
        "search project files",
        "grep files",
        "查找文件",
        "搜索文件",
        "文件中搜索",
    ),
    "refresh_project_registry": (
        "scan projects",
        "discover projects",
        "refresh projects",
        "rescan projects",
        "project registry",
        "扫描项目",
        "发现项目",
        "刷新项目",
        "项目注册表",
    ),
    "get_battery_status": (
        "battery status",
        "battery level",
        "charge level",
        "power remaining",
        "battery",
        "电池状态",
        "电池电量",
        "剩余电量",
    ),
    "get_network_status": (
        "network status",
        "wifi status",
        "internet interfaces",
        "network interfaces",
        "network",
        "网络状态",
        "网络连接",
        "wifi状态",
    ),
    "list_running_processes": (
        "running processes",
        "process list",
        "task manager",
        "running apps",
        "processes",
        "进程列表",
        "运行中的进程",
        "任务管理器",
    ),
    "adjust_volume": (
        "adjust volume",
        "volume up",
        "volume down",
        "make it louder",
        "make it quieter",
        "raise volume",
        "lower volume",
        "调高音量",
        "调低音量",
        "音量",
    ),
    "toggle_mute": (
        "mute",
        "unmute",
        "toggle mute",
        "静音",
        "取消静音",
    ),
    "media_control": (
        "play music",
        "pause music",
        "next track",
        "previous track",
        "stop music",
        "media control",
        "播放音乐",
        "暂停音乐",
        "下一首",
        "上一首",
        "停止音乐",
    ),
    "open_known_folder": (
        "open folder",
        "open desktop",
        "open documents",
        "open downloads",
        "open pictures",
        "open music folder",
        "open videos",
        "打开文件夹",
        "打开桌面",
        "打开文档",
        "打开下载",
    ),
    "open_windows_setting": (
        "windows settings",
        "open settings",
        "display settings",
        "sound settings",
        "wifi settings",
        "bluetooth settings",
        "power settings",
        "privacy settings",
        "打开设置",
        "显示设置",
        "声音设置",
        "电源设置",
    ),
    "lock_computer": (
        "lock computer",
        "lock screen",
        "lock workstation",
        "锁定电脑",
        "锁屏",
    ),
    "shutdown_computer": (
        "shutdown",
        "shut down",
        "turn off",
        "power down",
        "关机",
        "关闭电脑",
    ),
    "restart_computer": (
        "restart",
        "reboot",
        "restart computer",
        "重新启动",
        "重启",
    ),
    "sleep_computer": (
        "sleep computer",
        "put computer to sleep",
        "sleep mode",
        "休眠",
        "睡眠电脑",
    ),
    "search_obsidian_notes": (
        "search obsidian",
        "search notes",
        "find note",
        "obsidian notes",
        "搜索 obsidian",
        "搜索笔记",
        "查找笔记",
    ),
    "open_obsidian_note": (
        "open obsidian note",
        "open note",
        "view note",
        "打开 obsidian 笔记",
        "打开笔记",
        "查看笔记",
    ),
    "create_obsidian_note": (
        "create obsidian note",
        "new note",
        "create note",
        "make a note",
        "新建笔记",
        "创建笔记",
    ),
    "append_obsidian_note": (
        "append to note",
        "add to note",
        "write to note",
        "append note",
        "追加笔记",
        "在笔记中添加",
        "添加到笔记",
    ),
    "update_obsidian_note": (
        "update note",
        "edit note",
        "replace note text",
        "modify note",
        "更新笔记",
        "修改笔记",
        "替换笔记内容",
    ),
}

_NATIVE_PROPOSAL_CUES = tuple(
    alias
    for aliases in NATIVE_INTENT_FUZZY_ALIASES.values()
    for alias in aliases
)
_FUZZY_ALIAS_THRESHOLD = 0.84


def _normalize_proposal_text(value: str) -> str:
    value = re.sub(r"[^\w\s]+", " ", value.casefold())
    return " ".join(value.split())


def _fuzzy_alias_matches(normalized: str, alias: str) -> bool:
    if alias in normalized:
        return True

    alias_tokens = alias.split()
    input_tokens = normalized.split()
    if not alias_tokens or not input_tokens:
        return False

    window_sizes = {len(alias_tokens)}
    if len(alias_tokens) > 1:
        window_sizes.add(len(alias_tokens) + 1)
    for window_size in window_sizes:
        if window_size > len(input_tokens):
            continue
        for start in range(len(input_tokens) - window_size + 1):
            candidate = " ".join(input_tokens[start : start + window_size])
            score = SequenceMatcher(None, alias, candidate).ratio()
            if score >= _FUZZY_ALIAS_THRESHOLD:
                return True
    return False


def should_request_native_intent_proposal(user_input: str) -> bool:
    """Return whether this bounded request merits an optional Luna proposal."""
    if not isinstance(user_input, str):
        return False
    normalized = _normalize_proposal_text(user_input.strip())
    if not normalized or len(normalized) > 500:
        return False
    return any(_fuzzy_alias_matches(normalized, alias) for alias in _NATIVE_PROPOSAL_CUES)


def parse_native_intent_proposal(
    text: str,
    allowed_tools: Iterable[str],
) -> tuple[str, NativeIntentProposal | None]:
    """Strip one strict proposal marker and return a safe candidate if valid.

    Marker syntax is intentionally narrow.  Invalid, duplicated, oversized, or
    low-confidence markers become a normal text response with no candidate;
    they are never interpreted as a tool call.
    """
    if not isinstance(text, str):
        return "", None

    matches = list(_INTENT_PROPOSAL_PATTERN.finditer(text))
    cleaned = _INTENT_PROPOSAL_PATTERN.sub("", text)
    # Do not leak an incomplete protocol marker into the user-facing reply.
    cleaned = cleaned.replace(INTENT_PROPOSAL_START, "").replace(INTENT_PROPOSAL_END, "").strip()
    if len(matches) != 1:
        return cleaned, None

    payload_text = matches[0].group(1).strip()
    if len(payload_text) > 4_000:
        return cleaned, None
    try:
        payload = json.loads(payload_text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return cleaned, None

    if not isinstance(payload, dict):
        return cleaned, None
    if set(payload) != {"tool", "arguments", "confidence"}:
        return cleaned, None

    function_name = payload.get("tool")
    arguments = payload.get("arguments")
    confidence = payload.get("confidence")
    allowed = {value for value in allowed_tools if isinstance(value, str)}
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError, OverflowError):
        return cleaned, None
    if (
        not isinstance(function_name, str)
        or function_name not in allowed
        or not isinstance(arguments, dict)
        or isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence_value <= 1
        or confidence_value < _MIN_PROPOSAL_CONFIDENCE
    ):
        return cleaned, None

    normalized_arguments: dict[str, str] = {}
    if len(arguments) > 24:
        return cleaned, None
    for key, value in arguments.items():
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.strip()
            or len(value) > 12_000
        ):
            return cleaned, None
        normalized_arguments[key.strip()] = value.strip()

    return cleaned, NativeIntentProposal(
        function_name=function_name,
        arguments=normalized_arguments,
        confidence=confidence_value,
    )


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

    power_action = _resolve_power_action(lowered)
    if power_action:
        return NativeIntent(
            function_name=power_action,
            arguments={},
            description="此系统操作需要通过 JARVIS Core 确认。",
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


def _resolve_power_action(text: str) -> str | None:
    """Match only explicit, bounded power requests to existing native tools."""
    known_phrases = {
        "shutdown_computer": {
            "shut down my computer",
            "please shut down my computer",
            # Keep common English variants on the same bounded, exact-match
            # path.  They still require the existing native confirmation;
            # this is not model-side command inference.
            "shutdown my computer",
            "shutdown the computer",
            "shutdown computer",
            "shutdown my pc",
            "shutdown the pc",
            "shutdown pc",
            "shut down the computer",
            "shut down computer",
            "shut down my pc",
            "shut down the pc",
            "shut down pc",
            "please shut down the computer",
            "please shut down computer",
            "please shut down my pc",
            "please shut down the pc",
            "please shut down pc",
            "关机",
            "帮我关机",
            "请帮我关机",
            "关闭电脑",
            "关闭我的电脑",
            "帮我关闭电脑",
            "请关闭电脑",
        },
        "restart_computer": {
            "restart my computer",
            "please restart my computer",
            "重启电脑",
            "帮我重启电脑",
            "请帮我重启电脑",
        },
        "sleep_computer": {
            "put my computer to sleep",
            "please put my computer to sleep",
            "sleep my computer",
            "sleep the computer",
            "please sleep the computer",
            "让电脑休眠",
            "让我的电脑休眠",
            "帮我睡眠电脑",
            "请让电脑休眠",
        },
    }
    return next(
        (
            function_name
            for function_name, phrases in known_phrases.items()
            if text in phrases
        ),
        None,
    )


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
        # Chinese users commonly omit the space between the verb and an app
        # name (for example, "打开Google Classroom"). Keep English verbs
        # space-delimited so we do not turn an arbitrary "open..." token into
        # an app request.
        r"(?:请|帮我|please|can you)?\s*(?:(?:打开|启动)\s*(?=\S)|(?:open|launch)\s+)(.+)",
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
