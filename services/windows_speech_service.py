"""Reliable local English speech for the Windows JARVIS desktop app."""

from __future__ import annotations

import base64
import os
import subprocess
import sys
from threading import Lock
from typing import Any

if sys.platform == "win32":
    import winreg


class WindowsSpeechError(RuntimeError):
    """A safe, user-facing local speech failure."""


class WindowsSpeechService:
    """Follow the current Windows voice and speed without a Flutter plugin."""

    _settings_key = r"Software\Microsoft\Speech_OneCore\Settings\TextToSpeech"

    _script = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType=WindowsRuntime]
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesisStream, Windows.Media.SpeechSynthesis, ContentType=WindowsRuntime]
$settings = Get-ItemProperty 'HKCU:\Software\Microsoft\Speech_OneCore\Settings\TextToSpeech'
$voiceAttributes = Get-ItemProperty (('Registry::' + $settings.Voice) + '\Attributes')
$speaker = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::new()
try {
  $voice = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices |
    Where-Object DisplayName -eq $voiceAttributes.Name |
    Select-Object -First 1
  if ($null -eq $voice) { throw 'Selected OneCore voice unavailable.' }
  $speaker.Voice = $voice
  $speed = [Math]::Max(-10, [Math]::Min(10, [int]$settings.Speed))
  $speaker.Options.SpeakingRate = [Math]::Pow(1.1, $speed)
  $operation = $speaker.SynthesizeTextToStreamAsync($env:JARVIS_SPEECH_TEXT)
  $asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object {
      $_.Name -eq 'AsTask' -and
      $_.IsGenericMethod -and
      $_.GetGenericArguments().Count -eq 1 -and
      $_.GetParameters().Count -eq 1
    } |
    Select-Object -First 1
  $task = $asTask.MakeGenericMethod(
    [Windows.Media.SpeechSynthesis.SpeechSynthesisStream]
  ).Invoke($null, @($operation))
  $task.Wait()
  $stream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($task.Result)
  $player = [System.Media.SoundPlayer]::new($stream)
  $player.PlaySync()
} finally {
  if ($player) { $player.Dispose() }
  if ($stream) { $stream.Dispose() }
  $speaker.Dispose()
}
""".strip()

    def __init__(self) -> None:
        self._lock = Lock()
        self._process: subprocess.Popen[bytes] | None = None

    def speak(self, text: str) -> None:
        if sys.platform != "win32":
            raise WindowsSpeechError("Windows system voice is only available on Windows.")

        encoded_script = base64.b64encode(self._script.encode("utf-16-le")).decode("ascii")
        environment = os.environ.copy()
        environment["JARVIS_SPEECH_TEXT"] = text

        with self._lock:
            self._stop_locked()
            process = subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    encoded_script,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._process = process

        _, stderr = process.communicate()
        with self._lock:
            if self._process is process:
                self._process = None

        if process.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            if "OneCore voice unavailable" in detail:
                raise WindowsSpeechError(
                    "The voice selected in Windows is unavailable. Choose another Windows voice and try again."
                )
            raise WindowsSpeechError("Windows system voice could not start.")

    def settings(self) -> dict[str, Any]:
        """Read the current user-level Windows Speech settings without caching."""
        if sys.platform != "win32":
            raise WindowsSpeechError("Windows speech settings are only available on Windows.")

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._settings_key) as settings_key:
                voice_path = str(winreg.QueryValueEx(settings_key, "Voice")[0])
                speed = int(winreg.QueryValueEx(settings_key, "Speed")[0])

            prefix = "HKEY_LOCAL_MACHINE\\"
            if not voice_path.startswith(prefix):
                raise OSError("Unexpected Windows voice token path.")
            token_path = voice_path[len(prefix) :]
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                token_path + r"\Attributes",
            ) as attributes_key:
                voice_name = str(winreg.QueryValueEx(attributes_key, "Name")[0])
        except (OSError, ValueError, TypeError) as error:
            raise WindowsSpeechError("Windows speech settings could not be read.") from error

        return {
            "voice": voice_name,
            "speed": max(-10, min(10, speed)),
            "source": "Windows Speech settings",
        }

    def stop(self) -> None:
        with self._lock:
            self._stop_locked()

    def _stop_locked(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            self._process = None
            return
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        self._process = None
