"""Gemini cloud adapter with a deliberately small JARVIS tool boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from services.byok_config import load_byok_config
from services.jarvis_system_prompt import JARVIS_SYSTEM_PROMPT


ROOT_DIR = Path(__file__).resolve().parents[2]


class GeminiAdapter:
    """Send user requests to Gemini; Python retains all execution authority."""

    API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    MAX_LOCAL_TOOL_CALLS = 20

    LOCAL_TOOL_LIMITS = {
        "simple": 5,
        "standard": 20,
        "heavy": 50,
    }
    SYSTEM_INSTRUCTION = JARVIS_SYSTEM_PROMPT

    # These are the current native JARVIS tools. Python validates every model
    # proposal before it reaches the registry; Gemini never gets direct access
    # to Windows, a shell, or the filesystem.
    LOCAL_TOOL_DECLARATIONS = [
        {
            "name": "open_app",
            "description": "Open one discovered Windows application by name.",
            "parameters": {
                "type": "object",
                "properties": {"app": {"type": "string", "description": "Application name."}},
                "required": ["app"],
            },
        },
        {
            "name": "get_system_info",
            "description": "Read current local CPU and memory usage.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "list_projects",
            "description": "List development projects already registered locally.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_project_info",
            "description": "Read metadata for one already registered project by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Exact registered project name.",
                    }
                },
                "required": ["project_name"],
            },
        },
        {
            "name": "open_project",
            "description": "Open one registered project in Visual Studio Code.",
            "parameters": {
                "type": "object",
                "properties": {"project_name": {"type": "string", "description": "Registered project name."}},
                "required": ["project_name"],
            },
        },
        {
            "name": "git_status",
            "description": "Read Git branch and changed-file status for one registered project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Exact registered project name.",
                    }
                },
                "required": ["project_name"],
            },
        },
        {
            "name": "list_files",
            "description": "List files and folders in a registered project. Paths are project-relative.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Registered project name."},
                    "relative_path": {"type": "string", "description": "Optional project-relative folder; defaults to dot."},
                },
                "required": ["project_name"],
            },
        },
        {
            "name": "read_file",
            "description": "Read a small text file in a registered project. Paths are project-relative.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Registered project name."},
                    "relative_path": {"type": "string", "description": "Required project-relative file path."},
                },
                "required": ["project_name", "relative_path"],
            },
        },
        {
            "name": "search_files",
            "description": "Search text files in a registered project. Paths are project-relative.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Registered project name."},
                    "keyword": {"type": "string", "description": "Text to search for."},
                    "relative_path": {"type": "string", "description": "Optional project-relative folder; defaults to dot."},
                },
                "required": ["project_name", "keyword"],
            },
        },
        {
            "name": "refresh_project_registry",
            "description": "Refresh the registered project list only when the user explicitly asked to scan, discover, or refresh projects.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_battery_status",
            "description": "Read local battery percentage, charging state, and remaining time when available.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_network_status",
            "description": "Read active local network interface names and IPv4 addresses.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "list_running_processes",
            "description": "List running local process names and PIDs for diagnostics.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "adjust_volume",
            "description": "Raise or lower Windows master volume using a small, medium, or large adjustment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"]},
                    "amount": {"type": "string", "enum": ["small", "medium", "large"]},
                },
                "required": ["direction"],
            },
        },
        {
            "name": "toggle_mute",
            "description": "Toggle Windows master mute.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "media_control",
            "description": "Control the active media app.",
            "parameters": {
                "type": "object",
                "properties": {"action": {"type": "string", "enum": ["play_pause", "next", "previous", "stop"]}},
                "required": ["action"],
            },
        },
        {
            "name": "open_known_folder",
            "description": "Open a standard user folder in Windows Explorer.",
            "parameters": {
                "type": "object",
                "properties": {"folder": {"type": "string", "enum": ["desktop", "documents", "downloads", "pictures", "music", "videos"]}},
                "required": ["folder"],
            },
        },
        {
            "name": "open_windows_setting",
            "description": "Open a fixed Windows Settings page.",
            "parameters": {
                "type": "object",
                "properties": {"setting": {"type": "string", "enum": ["display", "sound", "wifi", "bluetooth", "power", "notifications", "privacy"]}},
                "required": ["setting"],
            },
        },
        {
            "name": "lock_computer",
            "description": "Lock the current Windows session without closing applications. This requires confirmation.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "shutdown_computer",
            "description": "Shut down Windows. This is high risk and requires one user confirmation.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "restart_computer",
            "description": "Restart Windows. This is high risk and requires one user confirmation.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "sleep_computer",
            "description": "Put Windows to sleep. This is high risk and requires one user confirmation.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "search_obsidian_notes",
            "description": "Search notes in configured Obsidian vaults. This is read-only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "vault_id": {"type": "string", "description": "Optional configured vault ID."},
                },
                "required": ["keyword"],
            },
        },
        {
            "name": "read_obsidian_note",
            "description": "Read shared note text using the vault ID and path returned by search. Reports truncation; refuses local-only/excluded notes.",
            "parameters": {
                "type": "object",
                "properties": {"vault_id": {"type": "string"}, "relative_path": {"type": "string"}},
                "required": ["vault_id", "relative_path"],
            },
        },
        {
            "name": "open_obsidian_note",
            "description": "Open an existing note in its configured Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {"vault_id": {"type": "string"}, "relative_path": {"type": "string"}},
                "required": ["vault_id", "relative_path"],
            },
        },
        {
            "name": "create_obsidian_note",
            "description": "Create a new Markdown note after user confirmation. Never overwrites an existing note.",
            "parameters": {
                "type": "object",
                "properties": {"vault_id": {"type": "string"}, "relative_path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["vault_id", "relative_path", "content"],
            },
        },
        {
            "name": "append_obsidian_note",
            "description": "Append text to an existing Markdown note after user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {"vault_id": {"type": "string"}, "relative_path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["vault_id", "relative_path", "content"],
            },
        },
        {
            "name": "update_obsidian_note",
            "description": "Replace one exact passage in an existing Obsidian note after showing a preview and receiving confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vault_id": {"type": "string"}, "relative_path": {"type": "string"},
                    "expected_text": {"type": "string"}, "replacement_text": {"type": "string"},
                },
                "required": ["vault_id", "relative_path", "expected_text", "replacement_text"],
            },
        },
    ]

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enabled: bool | None = None,
        timeout: int = 30,
    ):
        load_dotenv(ROOT_DIR / ".env")
        byok_config = load_byok_config()
        # Explicit constructor values are useful for tests and keep this adapter
        # independently testable; normal runtime selection comes from .env.
        uses_environment_selection = api_key is None and model is None and enabled is None
        self.provider = byok_config.provider if uses_environment_selection else "gemini"
        self.configuration_error = byok_config.error if uses_environment_selection else None
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model = model if model is not None else byok_config.model
        configured_enabled = byok_config.enabled
        self.enabled = configured_enabled if enabled is None else enabled
        self.timeout = timeout

    def is_configured(self) -> bool:
        return (
            self.configuration_error is None
            and self.provider == "gemini"
            and self.enabled
            and bool(self.api_key.strip())
            and self._is_valid_model_name()
        )

    def generate_response(
        self,
        user_message: str,
        execute_tool: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
        memory_contents: list[dict] | None = None,
    ) -> dict:
        """Return Gemini text, optionally completing a bounded local-tool sequence.

        ``execute_tool`` belongs to JARVIS's API/router layer.  Gemini can only
        propose a declared function; it never receives a callable capability.
        """
        if not self.is_configured():
            return {
                "success": False,
                "status": "unavailable",
                "result": "",
                "error": "Gemini is not configured. Add a valid local API key and enable Gemini.",
            }

        initial_contents = list(memory_contents or []) + [{"role": "user", "parts": [{"text": user_message}]}]
        payload = {
            "system_instruction": {"parts": [{"text": self.SYSTEM_INSTRUCTION}]},
            "contents": initial_contents,
        }

        if execute_tool:
            payload["tools"] = [{"functionDeclarations": self.LOCAL_TOOL_DECLARATIONS}]

        body, error = self._send(payload)
        if error:
            return error

        if execute_tool:
            tool_calls: list[str] = []
            conversation_contents = initial_contents.copy()

            while function_call := self._extract_function_call(body):
                if len(tool_calls) >= self.MAX_LOCAL_TOOL_CALLS:
                    return self._error(
                        "failed",
                        f"Gemini requested more than {self.MAX_LOCAL_TOOL_CALLS} local tools for one message.",
                    )

                function_name = function_call["name"]
                tool_result = execute_tool(function_name, function_call["args"])
                tool_calls.append(function_name)
                if tool_result.get("status") == "awaiting_confirmation":
                    return self._awaiting_confirmation(
                        tool_result.get("message", "This action is waiting for confirmation."),
                        tool_calls,
                    )
                candidate_content = self._first_candidate_content(body)
                if not candidate_content:
                    return self._error("failed", "Gemini returned an invalid tool request.")

                conversation_contents.extend(
                    [
                        candidate_content,
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "functionResponse": self._function_response(
                                        function_name,
                                        tool_result,
                                    )
                                }
                            ],
                        },
                    ]
                )
                body, error = self._send(
                    {
                        "system_instruction": {"parts": [{"text": self.SYSTEM_INSTRUCTION}]},
                        "contents": conversation_contents,
                        "tools": [{"functionDeclarations": self.LOCAL_TOOL_DECLARATIONS}],
                    }
                )
                if error:
                    return error

            if tool_calls:
                text = self._extract_text(body)
                if not text:
                    return self._error("failed", "Gemini returned no final text after local tool results.")
                return self._success(text, tool_calls=tool_calls)

        text = self._extract_text(body)
        if not text:
            return self._error("failed", "Gemini returned no text response.")

        return self._success(text)

    def _send(self, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Perform one API request without exposing the request URL or API key."""
        url = self.API_URL_TEMPLATE.format(model=self.model)
        request = Request(
            f"{url}?key={self.api_key}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8")), None
        except HTTPError as error:
            detail = ''
            try:
                from services.jarvis_memory import JarvisMemory
                detail = JarvisMemory._safe_text(json.loads(error.read()).get('error', {}).get('message', ''))[:1000]
                detail = detail.replace(self.api_key, '[redacted]') if self.api_key else detail
            except (ValueError, OSError, UnicodeDecodeError):
                pass
            return None, self._error("failed", f"Gemini rejected the request (HTTP {error.code}). {detail}".strip())
        except URLError:
            return None, self._error("unavailable", "Gemini could not be reached. Check the network connection.")
        except TimeoutError:
            return None, self._error("timeout", f"Gemini did not respond within {self.timeout} seconds.")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None, self._error("failed", "Gemini returned an unreadable response.")

    def generate_json(self, instruction: str, data: dict, schema: dict) -> dict:
        if not self.is_configured():
            raise ValueError('Gemini is not configured')
        # Gemini's constrained decoder accepts a smaller schema than Pydantic.
        # Keep the wire schema shallow; the full constraints are enforced locally.
        def wire(node):
            if '$ref' in node:
                return wire(schema['$defs'][node['$ref'].split('/')[-1]])
            result = {key: node[key] for key in ('type', 'enum', 'required', 'minimum', 'maximum') if key in node}
            if 'properties' in node:
                result['properties'] = {key: wire(value) for key, value in node['properties'].items()}
            if 'items' in node:
                result['items'] = wire(node['items'])
            return result
        body, error = self._send({
            'system_instruction': {'parts': [{'text': instruction}]},
            'contents': [{'role': 'user', 'parts': [{'text': json.dumps(data, ensure_ascii=False)}]}],
            'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': wire(schema)},
        })
        if error:
            raise ValueError(error['error'])
        return json.loads(self._extract_text(body))

    def _success(self, text: str, tool_calls: list[str] | None = None) -> dict:
        return {
            "success": True,
            "status": "completed",
            "result": text,
            "error": "",
            "provider": "gemini",
            "model": self.model,
            "tool_calls": tool_calls or [],
        }

    def _awaiting_confirmation(self, message: str, tool_calls: list[str]) -> dict:
        return {
            "success": True,
            "status": "awaiting_confirmation",
            "result": message,
            "error": "",
            "provider": "gemini",
            "model": self.model,
            "tool_calls": tool_calls,
        }

    def _is_valid_model_name(self) -> bool:
        return bool(self.model) and all(character.isalnum() or character in {"-", ".", "_"} for character in self.model)

    @staticmethod
    def _extract_text(body: dict) -> str:
        candidates = body.get("candidates", [])
        if not candidates:
            return ""

        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts).strip()

    @staticmethod
    def _first_candidate_content(body: dict) -> dict:
        candidates = body.get("candidates", [])
        if not candidates:
            return {}
        content = candidates[0].get("content", {})
        return content if isinstance(content, dict) else {}

    @classmethod
    def _extract_function_call(cls, body: dict) -> dict[str, Any] | None:
        """Extract one declared tool proposal; Python validates it again later."""
        for part in cls._first_candidate_content(body).get("parts", []):
            function_call = part.get("functionCall")
            if not isinstance(function_call, dict):
                continue
            name = function_call.get("name")
            arguments = function_call.get("args", {})
            if isinstance(name, str) and isinstance(arguments, dict):
                return {"name": name, "args": arguments, "id": function_call.get("id")}
        return None

    @staticmethod
    def _tool_result_for_model(tool_result: dict[str, Any]) -> dict[str, Any]:
        """Send a compact, non-secret execution result back for explanation."""
        return {
            "success": bool(tool_result.get("success")),
            "status": str(tool_result.get("status", "failed")),
            "result": str(tool_result.get("result", ""))[:8_000],
            "error": str(tool_result.get("error", ""))[:1_000],
        }

    @classmethod
    def _function_response(cls, function_name: str, tool_result: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": function_name,
            "response": {"result": cls._tool_result_for_model(tool_result)},
        }

    @staticmethod
    def _error(status: str, error: str) -> dict:
        return {"success": False, "status": status, "result": "", "error": error}
