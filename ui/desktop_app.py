"""A local-only Windows desktop shell for the JARVIS product roadmap.

The UI is intentionally a presentation prototype. It does not call a reasoning
backend, TaskRouter, or any system tool. That boundary keeps the future API integration
safe: the UI can request an action, while JARVIS Core remains responsible for
policy, routing, and execution.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable


@dataclass(frozen=True)
class Theme:
    background: str = "#090D16"
    surface: str = "#101827"
    surface_raised: str = "#162238"
    surface_selected: str = "#1B3150"
    stroke: str = "#263650"
    text: str = "#F4F8FF"
    muted: str = "#A6B4CB"
    dim: str = "#71809A"
    accent: str = "#77B9FF"
    accent_soft: str = "#24496F"
    success: str = "#67D7B1"
    warning: str = "#FFCB78"
    danger: str = "#FF9A9E"


THEME = Theme()


class DesktopApp:
    """Navigation and presentation state for the JARVIS desktop shell."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.page = "Assistant"
        self.nav_buttons: dict[str, tk.Button] = {}
        self.toast_label: tk.Label | None = None
        self.reduce_transparency = tk.BooleanVar(value=False)
        self.reduce_motion = tk.BooleanVar(value=False)

        self.root.title("JARVIS — Local desktop assistant")
        self.root.geometry("1460x900")
        self.root.minsize(1080, 720)
        self.root.configure(bg=THEME.background)
        self.root.option_add("*Font", ("Segoe UI", 10))

        self._build_shell()
        self.show_page("Assistant")

    def _build_shell(self) -> None:
        self.shell = tk.Frame(self.root, bg=THEME.background)
        self.shell.pack(fill="both", expand=True, padx=18, pady=18)
        self.shell.grid_columnconfigure(1, weight=1, minsize=520)
        self.shell.grid_rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self.shell, bg=THEME.surface, width=222)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.sidebar.grid_propagate(False)

        self.main = tk.Frame(self.shell, bg=THEME.background)
        self.main.grid(row=0, column=1, sticky="nsew", padx=(0, 12))

        self.inspector = tk.Frame(self.shell, bg=THEME.surface, width=292)
        self.inspector.grid(row=0, column=2, sticky="nsew")
        self.inspector.grid_propagate(False)

        self._build_sidebar()

    def _build_sidebar(self) -> None:
        brand = tk.Frame(self.sidebar, bg=THEME.surface)
        brand.pack(fill="x", padx=18, pady=(22, 26))
        mark = tk.Canvas(brand, width=30, height=30, bg=THEME.surface, highlightthickness=0)
        mark.pack(side="left", padx=(0, 10))
        mark.create_oval(2, 2, 28, 28, fill=THEME.accent_soft, outline="")
        mark.create_oval(8, 8, 22, 22, fill=THEME.accent, outline="")
        tk.Label(
            brand,
            text="JARVIS",
            font=("Segoe UI Semibold", 15),
            fg=THEME.text,
            bg=THEME.surface,
        ).pack(side="left")

        tk.Label(
            self.sidebar,
            text="Local desktop assistant",
            font=("Segoe UI", 9),
            fg=THEME.muted,
            bg=THEME.surface,
        ).pack(anchor="w", padx=18, pady=(0, 12))

        for name in ("Assistant", "Tasks", "Device", "Settings"):
            button = tk.Button(
                self.sidebar,
                text=name,
                command=lambda current=name: self.show_page(current),
                anchor="w",
                relief="flat",
                bd=0,
                padx=16,
                pady=11,
                fg=THEME.muted,
                bg=THEME.surface,
                activeforeground=THEME.text,
                activebackground=THEME.surface_selected,
                highlightthickness=1,
                highlightbackground=THEME.surface,
                highlightcolor=THEME.accent,
                cursor="hand2",
            )
            button.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = button

        spacer = tk.Frame(self.sidebar, bg=THEME.surface)
        spacer.pack(fill="both", expand=True)

        preview = tk.Frame(self.sidebar, bg=THEME.surface_raised, highlightthickness=1)
        preview.configure(highlightbackground=THEME.stroke)
        preview.pack(fill="x", padx=14, pady=14)
        tk.Label(
            preview,
            text="Prototype mode",
            font=("Segoe UI Semibold", 10),
            fg=THEME.text,
            bg=THEME.surface_raised,
        ).pack(anchor="w", padx=12, pady=(12, 3))
        tk.Label(
            preview,
            text="The UI is not connected to JARVIS Core yet.",
            justify="left",
            wraplength=170,
            font=("Segoe UI", 9),
            fg=THEME.muted,
            bg=THEME.surface_raised,
        ).pack(anchor="w", padx=12, pady=(0, 12))

    def show_page(self, page: str) -> None:
        self.page = page
        for name, button in self.nav_buttons.items():
            selected = name == page
            button.configure(
                bg=THEME.surface_selected if selected else THEME.surface,
                fg=THEME.text if selected else THEME.muted,
            )

        self._clear(self.main)
        self._clear(self.inspector)
        if page == "Assistant":
            self._build_assistant()
        elif page == "Tasks":
            self._build_tasks()
        elif page == "Device":
            self._build_device()
        else:
            self._build_settings()
        self._build_inspector()

    def _build_assistant(self) -> None:
        frame = tk.Frame(self.main, bg=THEME.background)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=THEME.background)
        header.pack(fill="x", pady=(6, 20))
        tk.Label(
            header,
            text="Good evening, Zheng Gan.",
            font=("Segoe UI Semibold", 25),
            fg=THEME.text,
            bg=THEME.background,
        ).pack(side="left")
        self._status_badge(header, "Ready", THEME.success).pack(side="right", pady=5)

        tk.Label(
            frame,
            text="Ask JARVIS to inspect, plan, or manage a local task. Actions stay behind policy checks.",
            font=("Segoe UI", 10),
            fg=THEME.muted,
            bg=THEME.background,
        ).pack(anchor="w", pady=(0, 18))

        conversation = tk.Frame(frame, bg=THEME.surface, highlightthickness=1)
        conversation.configure(highlightbackground=THEME.stroke)
        conversation.pack(fill="both", expand=True)
        self.conversation = conversation
        self._message(conversation, "JARVIS", "Your local workspace is ready. What would you like to work on?", False)
        self._message(
            conversation,
            "System notice",
            "This desktop shell is in preview mode. Requests stay inside the interface until the future local API is connected.",
            True,
        )

        composer = tk.Frame(frame, bg=THEME.surface_raised, highlightthickness=1)
        composer.configure(highlightbackground=THEME.stroke)
        composer.pack(fill="x", pady=(14, 0))
        self.prompt = tk.Text(
            composer,
            height=3,
            wrap="word",
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            fg=THEME.text,
            insertbackground=THEME.text,
            bg=THEME.surface_raised,
            highlightthickness=1,
            highlightbackground=THEME.surface_raised,
            highlightcolor=THEME.accent,
        )
        self.prompt.pack(side="left", fill="both", expand=True)
        self.prompt.bind("<Control-Return>", lambda _event: self.submit_prompt())
        send = self._button(composer, "Send", self.submit_prompt, primary=True)
        send.pack(side="right", padx=12, pady=12)
        tk.Label(
            frame,
            text="Ctrl + Enter to send · Preview requests do not run tools",
            font=("Segoe UI", 9),
            fg=THEME.dim,
            bg=THEME.background,
        ).pack(anchor="w", pady=(7, 0))

    def _build_tasks(self) -> None:
        self._page_heading("Tasks", "Observe task progress without losing the permission context that created it.")
        timeline = tk.Frame(self.main, bg=THEME.surface, highlightthickness=1)
        timeline.configure(highlightbackground=THEME.stroke)
        timeline.pack(fill="both", expand=True)
        for title, detail, status, color in (
            ("No active work", "When JARVIS Core starts a managed task, it will appear here.", "Waiting", THEME.muted),
            ("Policy-aware lifecycle", "Queued → running → observing → completed or failed", "Designed", THEME.accent),
            ("Notifications", "Completion and failure notifications will be provided by the future local API.", "Planned", THEME.warning),
        ):
            row = tk.Frame(timeline, bg=THEME.surface)
            row.pack(fill="x", padx=22, pady=14)
            dot = tk.Canvas(row, width=18, height=18, bg=THEME.surface, highlightthickness=0)
            dot.create_oval(5, 5, 13, 13, fill=color, outline="")
            dot.pack(side="left", padx=(0, 14), pady=6)
            content = tk.Frame(row, bg=THEME.surface)
            content.pack(side="left", fill="x", expand=True)
            tk.Label(content, text=title, font=("Segoe UI Semibold", 11), fg=THEME.text, bg=THEME.surface).pack(anchor="w")
            tk.Label(content, text=detail, font=("Segoe UI", 9), fg=THEME.muted, bg=THEME.surface, wraplength=500, justify="left").pack(anchor="w", pady=(3, 0))
            self._status_badge(row, status, color).pack(side="right", padx=(12, 0))

    def _build_device(self) -> None:
        self._page_heading("Device", "A calm status surface for the planned desktop orb, voice session, and local runtime.")
        stage = tk.Frame(self.main, bg=THEME.surface, highlightthickness=1)
        stage.configure(highlightbackground=THEME.stroke)
        stage.pack(fill="both", expand=True)
        orb = tk.Canvas(stage, width=260, height=260, bg=THEME.surface, highlightthickness=0)
        orb.pack(pady=(60, 20))
        orb.create_oval(22, 22, 238, 238, fill="#102846", outline="")
        orb.create_oval(46, 46, 214, 214, fill="#174B76", outline="")
        orb.create_oval(72, 72, 188, 188, fill=THEME.accent, outline="")
        orb.create_oval(102, 84, 158, 140, fill="#D9EEFF", outline="")
        tk.Label(stage, text="Standing by", font=("Segoe UI Semibold", 17), fg=THEME.text, bg=THEME.surface).pack()
        tk.Label(stage, text="Voice, wake word, and desktop animation are planned. This visual does not listen or record audio.", wraplength=480, justify="center", font=("Segoe UI", 10), fg=THEME.muted, bg=THEME.surface).pack(pady=(8, 20))
        self._button(stage, "Preview a permission request", self.show_confirmation).pack()

    def _build_settings(self) -> None:
        self._page_heading("Settings", "Controls are visual placeholders until the local settings API is implemented.")
        content = tk.Frame(self.main, bg=THEME.background)
        content.pack(fill="both", expand=True)
        left = tk.Frame(content, bg=THEME.surface, highlightthickness=1)
        left.configure(highlightbackground=THEME.stroke)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        right = tk.Frame(content, bg=THEME.surface, highlightthickness=1)
        right.configure(highlightbackground=THEME.stroke)
        right.pack(side="left", fill="both", expand=True, padx=(7, 0))

        self._setting_select(left, "Reasoning backend", "Codex", ("Codex", "Choose later"))
        self._setting_select(left, "Routing mode", "automatic", ("manual", "ask", "automatic"))
        self._setting_select(left, "Notification channel", "desktop and terminal", ("desktop and terminal", "terminal only"))
        self._setting_toggle(right, "Reduce transparency", "Use stronger solid surfaces for easier reading.", self.reduce_transparency, self.apply_accessibility)
        self._setting_toggle(right, "Reduce motion", "Keep visual feedback calm and static.", self.reduce_motion, self.apply_accessibility)
        self._setting_toggle(right, "Voice session", "Planned — no microphone access is requested by this UI.", tk.BooleanVar(value=False), self._planned_control)

    def _build_inspector(self) -> None:
        header = tk.Frame(self.inspector, bg=THEME.surface)
        header.pack(fill="x", padx=18, pady=(24, 18))
        tk.Label(header, text="Local runtime", font=("Segoe UI Semibold", 15), fg=THEME.text, bg=THEME.surface).pack(anchor="w")
        tk.Label(header, text="UI preview · no core connection", font=("Segoe UI", 9), fg=THEME.muted, bg=THEME.surface).pack(anchor="w", pady=(4, 0))

        self._runtime_row("Brain", "Codex", "Planned connection", THEME.accent)
        self._runtime_row("Safety", "TaskRouter policy", "Core owns decisions", THEME.success)
        self._runtime_row("Tasks", "No active tasks", "Future API feed", THEME.muted)

        divider = tk.Frame(self.inspector, bg=THEME.stroke, height=1)
        divider.pack(fill="x", padx=18, pady=20)
        tk.Label(self.inspector, text="Safety first", font=("Segoe UI Semibold", 12), fg=THEME.text, bg=THEME.surface).pack(anchor="w", padx=18)
        tk.Label(self.inspector, text="The UI may request an action, but it must never become a bypass around policy checks, confirmations, or workspace validation.", justify="left", wraplength=242, font=("Segoe UI", 9), fg=THEME.muted, bg=THEME.surface).pack(anchor="w", padx=18, pady=(7, 14))
        self._button(self.inspector, "See permission preview", self.show_confirmation).pack(anchor="w", padx=18)

    def _page_heading(self, title: str, subtitle: str) -> None:
        tk.Label(self.main, text=title, font=("Segoe UI Semibold", 25), fg=THEME.text, bg=THEME.background).pack(anchor="w", pady=(6, 5))
        tk.Label(self.main, text=subtitle, font=("Segoe UI", 10), fg=THEME.muted, bg=THEME.background, wraplength=690, justify="left").pack(anchor="w", pady=(0, 20))

    def _message(self, parent: tk.Widget, sender: str, message: str, quiet: bool) -> None:
        wrap = tk.Frame(parent, bg=THEME.surface)
        wrap.pack(fill="x", padx=20, pady=(18 if len(parent.winfo_children()) == 1 else 8, 8))
        color = THEME.muted if quiet else THEME.accent
        tk.Label(wrap, text=sender, font=("Segoe UI Semibold", 9), fg=color, bg=THEME.surface).pack(anchor="w")
        tk.Label(wrap, text=message, font=("Segoe UI", 11), fg=THEME.text, bg=THEME.surface, wraplength=700, justify="left").pack(anchor="w", pady=(4, 0))

    def _runtime_row(self, title: str, value: str, caption: str, color: str) -> None:
        row = tk.Frame(self.inspector, bg=THEME.surface_raised, highlightthickness=1)
        row.configure(highlightbackground=THEME.stroke)
        row.pack(fill="x", padx=18, pady=5)
        dot = tk.Canvas(row, width=14, height=14, bg=THEME.surface_raised, highlightthickness=0)
        dot.create_oval(3, 3, 11, 11, fill=color, outline="")
        dot.grid(row=0, column=0, rowspan=2, padx=(11, 9), pady=13)
        tk.Label(row, text=title, font=("Segoe UI", 9), fg=THEME.muted, bg=THEME.surface_raised).grid(row=0, column=1, sticky="w", pady=(10, 0))
        tk.Label(row, text=value, font=("Segoe UI Semibold", 10), fg=THEME.text, bg=THEME.surface_raised).grid(row=1, column=1, sticky="w", pady=(0, 2))
        tk.Label(row, text=caption, font=("Segoe UI", 8), fg=THEME.dim, bg=THEME.surface_raised).grid(row=2, column=1, sticky="w", pady=(0, 10))

    def _setting_select(self, parent: tk.Widget, title: str, selected: str, values: tuple[str, ...]) -> None:
        block = tk.Frame(parent, bg=THEME.surface)
        block.pack(fill="x", padx=20, pady=18)
        tk.Label(block, text=title, font=("Segoe UI Semibold", 11), fg=THEME.text, bg=THEME.surface).pack(anchor="w")
        choice = ttk.Combobox(block, values=values, state="readonly", font=("Segoe UI", 10))
        choice.set(selected)
        choice.pack(fill="x", pady=(8, 0))
        choice.bind("<<ComboboxSelected>>", lambda _event: self._planned_control())

    def _setting_toggle(self, parent: tk.Widget, title: str, detail: str, variable: tk.BooleanVar, command: Callable[[], None]) -> None:
        block = tk.Frame(parent, bg=THEME.surface)
        block.pack(fill="x", padx=20, pady=18)
        switch = tk.Checkbutton(block, text=title, variable=variable, command=command, onvalue=True, offvalue=False, indicatoron=False, relief="flat", bd=0, padx=10, pady=7, fg=THEME.text, bg=THEME.surface_raised, activeforeground=THEME.text, activebackground=THEME.surface_selected, selectcolor=THEME.accent_soft, highlightthickness=1, highlightbackground=THEME.stroke, highlightcolor=THEME.accent, cursor="hand2")
        switch.pack(anchor="w")
        tk.Label(block, text=detail, font=("Segoe UI", 9), fg=THEME.muted, bg=THEME.surface, wraplength=280, justify="left").pack(anchor="w", pady=(8, 0))

    def _status_badge(self, parent: tk.Widget, text: str, color: str) -> tk.Label:
        return tk.Label(parent, text=f"  {text}  ", font=("Segoe UI Semibold", 8), fg=color, bg=THEME.surface_raised, padx=4, pady=4)

    def _button(self, parent: tk.Widget, text: str, command: Callable[[], None], primary: bool = False) -> tk.Button:
        return tk.Button(parent, text=text, command=command, relief="flat", bd=0, padx=14, pady=9, font=("Segoe UI Semibold", 9), fg=THEME.background if primary else THEME.text, bg=THEME.accent if primary else THEME.surface_raised, activeforeground=THEME.background if primary else THEME.text, activebackground="#9ACBFF" if primary else THEME.surface_selected, highlightthickness=1, highlightbackground=THEME.accent if primary else THEME.stroke, highlightcolor=THEME.accent, cursor="hand2")

    def submit_prompt(self) -> None:
        content = self.prompt.get("1.0", "end").strip()
        if not content:
            self.show_toast("Write a request before sending it.")
            self.prompt.focus_set()
            return
        self._message(self.conversation, "You", content, False)
        self._message(self.conversation, "JARVIS", "Preview received. When the local API is connected, this request will be sent through JARVIS Core and TaskRouter before any executor can run.", True)
        self.prompt.delete("1.0", "end")
        self.show_toast("Preview request added — no tool was executed.")

    def show_confirmation(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("JARVIS — permission preview")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=THEME.surface)
        dialog.resizable(False, False)
        box = tk.Frame(dialog, bg=THEME.surface, padx=28, pady=26)
        box.pack()
        tk.Label(box, text="Action needs your approval", font=("Segoe UI Semibold", 18), fg=THEME.text, bg=THEME.surface).pack(anchor="w")
        tk.Label(box, text="Illustrative only — this dialog cannot run an action.", font=("Segoe UI", 9), fg=THEME.warning, bg=THEME.surface).pack(anchor="w", pady=(6, 18))
        self._confirmation_detail(box, "Requested action", "Run a project test command")
        self._confirmation_detail(box, "Why confirmation", "It may start a local process and write temporary files.")
        self._confirmation_detail(box, "Policy owner", "TaskRouter and the future local API")
        actions = tk.Frame(box, bg=THEME.surface)
        actions.pack(fill="x", pady=(24, 0))
        self._button(actions, "Not now", dialog.destroy).pack(side="right")
        self._button(actions, "Approve preview", lambda: self._close_preview(dialog), primary=True).pack(side="right", padx=(0, 9))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def _confirmation_detail(self, parent: tk.Widget, label: str, value: str) -> None:
        row = tk.Frame(parent, bg=THEME.surface_raised, padx=12, pady=9)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, font=("Segoe UI", 9), fg=THEME.muted, bg=THEME.surface_raised).pack(anchor="w")
        tk.Label(row, text=value, font=("Segoe UI Semibold", 10), fg=THEME.text, bg=THEME.surface_raised, wraplength=410, justify="left").pack(anchor="w", pady=(2, 0))

    def _close_preview(self, dialog: tk.Toplevel) -> None:
        dialog.destroy()
        self.show_toast("Preview approval recorded locally — nothing was executed.")

    def _planned_control(self) -> None:
        self.show_toast("This control will save through the future local settings API.")

    def apply_accessibility(self) -> None:
        if self.reduce_transparency.get():
            self.root.configure(bg="#070A10")
            self.shell.configure(bg="#070A10")
        else:
            self.root.configure(bg=THEME.background)
            self.shell.configure(bg=THEME.background)
        motion = "Reduced-motion preference enabled." if self.reduce_motion.get() else "Visual motion preference reset."
        self.show_toast(motion)

    def show_toast(self, message: str) -> None:
        if self.toast_label is not None:
            self.toast_label.destroy()
        self.toast_label = tk.Label(self.root, text=message, font=("Segoe UI", 9), fg=THEME.text, bg=THEME.surface_raised, padx=14, pady=9, highlightthickness=1, highlightbackground=THEME.stroke)
        self.toast_label.place(relx=0.5, rely=1.0, anchor="s", y=-18)
        self.root.after(3200, self._clear_toast)

    def _clear_toast(self) -> None:
        if self.toast_label is not None:
            self.toast_label.destroy()
            self.toast_label = None

    @staticmethod
    def _clear(widget: tk.Widget) -> None:
        for child in widget.winfo_children():
            child.destroy()


def main() -> None:
    root = tk.Tk()
    DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
