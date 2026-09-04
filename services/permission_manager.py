"""Central permission decisions for all JARVIS actions."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ActionRequest:
    """A minimal, audit-safe description of an action before it can run."""

    executor: str
    action: str
    purpose: str
    data_scope: str = "local"


@dataclass(frozen=True)
class PermissionDecision:
    """The outcome TaskRouter must enforce before execution."""

    request: ActionRequest
    risk: str
    requires_confirmation: bool
    audit_summary: str
    confirmation_count: int = 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["request"] = asdict(self.request)
        return data


class PermissionManager:
    """Classify actions without granting a model direct execution authority."""

    READ_ONLY_NATIVE_ACTIONS = {
        "get_system_info", "list_projects", "get_project_info", "git_status", "list_files",
        "read_file", "search_files", "get_battery_status", "get_network_status",
        "list_running_processes",
        "search_obsidian_notes",
    }
    EXPLICIT_LOCAL_ACTIONS = {
        "open_app", "open_project", "refresh_project_registry", "adjust_volume", "toggle_mute",
        "media_control", "open_known_folder", "open_windows_setting",
        "open_obsidian_note",
    }
    CONFIRMATION_REQUIRED_ACTIONS = {
        "write_file", "edit_file", "delete_file", "install_software", "admin_command", "git_commit",
        "git_push", "browser_submit", "lock_computer", "shutdown_computer", "restart_computer",
        "sleep_computer",
        "create_obsidian_note", "append_obsidian_note", "update_obsidian_note",
    }
    HIGH_RISK_ACTIONS = {
        "delete_file", "admin_command", "shutdown_computer", "restart_computer", "sleep_computer",
    }
    EXTERNAL_EXECUTORS = {"chatgpt_ui", "codex", "gemini"}

    def evaluate(self, request: ActionRequest) -> PermissionDecision:
        if request.executor == "gemini" and request.action == "generate_response":
            return PermissionDecision(
                request=request,
                risk="low",
                requires_confirmation=False,
                audit_summary="Allowed user-authored text submission to the configured Gemini provider.",
            )

        if request.executor in self.EXTERNAL_EXECUTORS:
            return self._confirmation_decision(request, risk="medium")

        if request.action in self.CONFIRMATION_REQUIRED_ACTIONS:
            risk = "high" if request.action in self.HIGH_RISK_ACTIONS else "medium"
            return self._confirmation_decision(request, risk=risk)

        if request.action in self.READ_ONLY_NATIVE_ACTIONS:
            return PermissionDecision(
                request=request,
                risk="low",
                requires_confirmation=False,
                audit_summary=f"Allowed read-only native action: {request.action}.",
            )

        if request.action in self.EXPLICIT_LOCAL_ACTIONS:
            return PermissionDecision(
                request=request,
                risk="low",
                requires_confirmation=False,
                audit_summary=f"Allowed explicit local action: {request.action}.",
            )

        return PermissionDecision(
            request=request,
            risk="high",
            requires_confirmation=True,
            audit_summary=f"Confirmation required for unrecognised action: {request.action}.",
            confirmation_count=1,
        )

    @staticmethod
    def _confirmation_decision(request: ActionRequest, risk: str) -> PermissionDecision:
        destination = "external executor" if request.executor != "native" else "native executor"
        return PermissionDecision(
            request=request,
            risk=risk,
            requires_confirmation=True,
            audit_summary=f"Confirmation required before {request.action} runs through the {destination}.",
            confirmation_count=1,
        )
