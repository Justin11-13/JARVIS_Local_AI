"""Fixed, local Windows assistant tools.

These functions intentionally expose named actions rather than a general shell.
TaskRouter decides whether the user must confirm an action before it is called.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
from pathlib import Path

import psutil


VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002

VOLUME_AMOUNTS = {"small": 1, "medium": 3, "large": 6}
MEDIA_KEYS = {
    "play_pause": VK_MEDIA_PLAY_PAUSE,
    "next": VK_MEDIA_NEXT_TRACK,
    "previous": VK_MEDIA_PREV_TRACK,
    "stop": VK_MEDIA_STOP,
}
KNOWN_FOLDERS = {
    "desktop": "Desktop",
    "documents": "Documents",
    "downloads": "Downloads",
    "pictures": "Pictures",
    "music": "Music",
    "videos": "Videos",
}
WINDOWS_SETTINGS = {
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "wifi": "ms-settings:network-wifi",
    "bluetooth": "ms-settings:bluetooth",
    "power": "ms-settings:powersleep",
    "notifications": "ms-settings:notifications",
    "privacy": "ms-settings:privacy",
}


def _require_windows() -> str | None:
    if os.name != "nt":
        return "This tool is only available on Windows."
    return None


def _send_virtual_key(key: int) -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(key, 0, 0, 0)
    user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)


def get_battery_status() -> str:
    """Return battery level and charging state when the device has a battery."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery was detected. This computer may be using desktop power."

    state = "charging" if battery.power_plugged else "on battery"
    remaining = "unknown" if battery.secsleft in {psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN} else f"{battery.secsleft // 60} minutes remaining"
    return f"Battery: {battery.percent:.0f}%, {state}, {remaining}."


def get_network_status() -> str:
    """Summarize active, non-loopback local network interfaces."""
    interfaces = []
    stats = psutil.net_if_stats()
    addresses = psutil.net_if_addrs()
    for name, records in addresses.items():
        if name.lower().startswith("loopback") or name.lower() == "lo":
            continue
        if not stats.get(name) or not stats[name].isup:
            continue
        ipv4 = next((record.address for record in records if record.family.name == "AF_INET"), None)
        if ipv4:
            interfaces.append(f"{name}: {ipv4}")

    return "Active network interfaces: " + ", ".join(interfaces) if interfaces else "No active network interface was found."


def list_running_processes() -> str:
    """List up to 80 visible process names and PIDs for local diagnostics."""
    processes = []
    for process in psutil.process_iter(["pid", "name"]):
        try:
            name = process.info.get("name") or "Unknown"
            processes.append((name.lower(), process.info["pid"], name))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort()
    preview = [f"{name} (PID {pid})" for _, pid, name in processes[:80]]
    if not preview:
        return "No running processes could be listed."
    suffix = " (showing first 80)" if len(processes) > 80 else ""
    return "Running processes" + suffix + ": " + ", ".join(preview)


def adjust_volume(direction: str, amount: str = "medium") -> str:
    """Raise or lower master volume using standard Windows media keys."""
    unavailable = _require_windows()
    if unavailable:
        return unavailable
    direction = direction.strip().lower()
    amount = amount.strip().lower()
    if direction not in {"up", "down"}:
        return "Volume direction must be 'up' or 'down'."
    steps = VOLUME_AMOUNTS.get(amount)
    if steps is None:
        return "Volume amount must be small, medium, or large."

    key = VK_VOLUME_UP if direction == "up" else VK_VOLUME_DOWN
    for _ in range(steps):
        _send_virtual_key(key)
    return f"Volume moved {direction} by a {amount} amount."


def toggle_mute() -> str:
    """Toggle the Windows master mute state."""
    unavailable = _require_windows()
    if unavailable:
        return unavailable
    _send_virtual_key(VK_VOLUME_MUTE)
    return "Master mute was toggled."


def media_control(action: str) -> str:
    """Send one standard media key to the active media application."""
    unavailable = _require_windows()
    if unavailable:
        return unavailable
    action = action.strip().lower()
    key = MEDIA_KEYS.get(action)
    if key is None:
        return "Media action must be play_pause, next, previous, or stop."
    _send_virtual_key(key)
    return f"Sent media action: {action}."


def lock_computer() -> str:
    """Lock the current Windows session without closing applications."""
    unavailable = _require_windows()
    if unavailable:
        return unavailable
    if not ctypes.windll.user32.LockWorkStation():
        return "Windows could not lock the workstation."
    return "The workstation was locked."


def open_known_folder(folder: str) -> str:
    """Open a small allowlist of user folders in Windows Explorer."""
    unavailable = _require_windows()
    if unavailable:
        return unavailable
    folder = folder.strip().lower()
    folder_name = KNOWN_FOLDERS.get(folder)
    if folder_name is None:
        return "Folder must be desktop, documents, downloads, pictures, music, or videos."
    target = Path.home() / folder_name
    if not target.exists():
        return f"The {folder} folder does not exist."
    os.startfile(str(target))
    return f"Opened {folder}."


def open_windows_setting(setting: str) -> str:
    """Open a fixed Windows Settings page through its documented URI."""
    unavailable = _require_windows()
    if unavailable:
        return unavailable
    setting = setting.strip().lower()
    uri = WINDOWS_SETTINGS.get(setting)
    if uri is None:
        return "Setting must be display, sound, wifi, bluetooth, power, notifications, or privacy."
    os.startfile(uri)
    return f"Opened Windows {setting} settings."


def shutdown_computer() -> str:
    """Shut down Windows immediately. TaskRouter requires two confirmations."""
    return _power_action(["shutdown", "/s", "/t", "0"], "Windows is shutting down.")


def restart_computer() -> str:
    """Restart Windows immediately. TaskRouter requires two confirmations."""
    return _power_action(["shutdown", "/r", "/t", "0"], "Windows is restarting.")


def sleep_computer() -> str:
    """Put Windows to sleep. TaskRouter requires two confirmations."""
    return _power_action(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
        "Windows is entering sleep mode.",
    )


def _power_action(command: list[str], success_message: str) -> str:
    unavailable = _require_windows()
    if unavailable:
        return unavailable
    try:
        subprocess.Popen(command)
    except OSError as error:
        return f"Windows power action failed: {error}"
    return success_message
