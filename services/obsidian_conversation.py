"""Small, session-local note workflow; all I/O stays behind the tool policy."""

from __future__ import annotations

import re


class ObsidianConversation:
    def __init__(self):
        self.clear()

    def clear(self):
        self.candidates = []
        self.selected = None
        self.action = "read"
        self.awaiting_selection = False
        self.idle_turns = 0

    def observe(self, name, arguments, result):
        if not result.get("success") or result.get("status") != "completed":
            return
        if name == "search_obsidian_notes":
            self.action = "read"
            self.candidates = []
            self.selected = None
            for line in str(result.get("result", "")).splitlines():
                vault, separator, path = line.partition(":")
                if separator and vault and path.lower().endswith(".md"):
                    self.candidates.append({"vault_id": vault, "relative_path": path})
            self.candidates = self.candidates[:20]
            if len(self.candidates) == 1:
                self.selected = self.candidates[0]
            self.awaiting_selection = len(self.candidates) > 1
            self.idle_turns = 0
        elif name in {"read_obsidian_note", "open_obsidian_note"}:
            self.awaiting_selection = False
            self.selected = {key: arguments[key] for key in ("vault_id", "relative_path")}
            if self.selected not in self.candidates:
                self.candidates = [self.selected]
            self.idle_turns = 0

    def choices(self):
        lines = [f"{i}. {note['relative_path']} ({note['vault_id']})" for i, note in enumerate(self.candidates, 1)]
        return "找到以下笔记，请回复编号选择：\n" + "\n".join(lines)

    @staticmethod
    def lookup_request(text):
        match = re.fullmatch(
            r"(?:请|帮我|请帮我)?\s*(找|查找|搜索|打开|读取)\s*(.+?(?:教程|笔记|学习资料|指南))"
            r"|(?:please\s+)?(find|search for|open|read)\s+(?:the\s+|my\s+)?(.+?\b(?:tutorials?|notes?|guides?))",
            text, re.IGNORECASE,
        )
        if not match:
            return None
        verb, topic = (match[1], match[2]) if match[1] else (match[3].lower(), match[4])
        # Only a narrow content request is handled here; never drop a second action.
        if re.search(r"然后|并且|再|[;；]|\band\b|\bthen\b", topic, re.IGNORECASE):
            return None
        keyword = re.sub(r"(?:的)?(?:学习资料|教程|笔记|指南)$|\b(?:tutorials?|notes?|guides?)$", "", topic, flags=re.IGNORECASE).strip()
        return (keyword or topic, "open" if verb in {"打开", "open"} else "read")

    def handle(self, user_input, execute):
        text = user_input.strip().rstrip("。！？!?.").strip()
        lookup = self.lookup_request(text)
        if lookup:
            return self.search(*lookup, execute=execute)
        if text.lower() in {"取消", "算了", "cancel", "forget it"} and self.candidates:
            self.clear()
            return {"reply": "已取消笔记选择。", "tools": []}
        choice = re.fullmatch(r"(?:第\s*)?(\d+|[一二三四五六七八九十])\s*(?:个|篇)?", text)
        if choice and self.candidates:
            value = choice[1]
            index = int(value) if value.isdigit() else "一二三四五六七八九十".index(value) + 1
            if not 1 <= index <= len(self.candidates):
                return {"reply": self.choices(), "tools": []}
            self.selected = self.candidates[index - 1]
            self.awaiting_selection = False
            return self.use_selected(self.action, execute)
        followups = {
            "读一下": "read", "读取": "read", "读取一下": "read", "你不能读取": "read",
            "读它": "read", "read it": "read", "read that": "read",
            "打开它": "open", "打开这篇": "open", "open it": "open",
            "继续解释": "explain", "解释一下": "explain", "总结一下": "explain",
            "continue explaining": "explain", "summarize it": "explain", "explain it": "explain",
        }
        action = followups.get(text.lower())
        if action:
            if action == "explain" and not self.candidates:
                return None
            self.idle_turns = 0
            self.action = action
            if not self.selected:
                return {"reply": self.choices() if self.candidates else "目前没有确定的笔记。请告诉我笔记名称或要查找的主题。", "tools": []}
            return self.use_selected(action, execute)
        self.idle_turns += 1
        if self.idle_turns >= 6:
            self.clear()
        return None

    def search(self, keyword, action, execute, force_choice=False):
        self.clear()
        self.action = action
        arguments = {"keyword": keyword}
        result = execute("search_obsidian_notes", arguments)
        self.observe("search_obsidian_notes", arguments, result)
        self.action = action
        tools = [result]
        retry_notice = ""
        if not result.get("success"):
            return {"reply": result.get("error") or "笔记搜索失败。", "tools": [result]}
        # One narrower keyword retry; do not broaden indefinitely or invent web results.
        shorter = keyword.split()[0]
        if not self.candidates and shorter != keyword and len(shorter) >= 2:
            force_choice = True
            retry_notice = f"原关键词没有匹配，已改用“{shorter}”搜索。\n"
            arguments = {"keyword": shorter}
            result = execute("search_obsidian_notes", arguments)
            tools.append(result)
            self.observe("search_obsidian_notes", arguments, result)
            self.action = action
            if not result.get("success"):
                return {"reply": result.get("error") or "笔记搜索重试失败。", "tools": tools}
        if not self.candidates:
            return {"reply": f"没有找到与“{keyword}”匹配的共享笔记。可以换一个主题词，或提供笔记名称。", "tools": tools}
        if len(self.candidates) > 1 or force_choice:
            self.selected = None
            self.awaiting_selection = True
            return {"reply": retry_notice + self.choices(), "tools": tools}
        answer = self.use_selected(action, execute)
        answer["tools"] = tools + answer["tools"]
        return answer

    def use_selected(self, action, execute):
        name = "open_obsidian_note" if action == "open" else "read_obsidian_note"
        target = dict(self.selected)
        result = execute(name, target)
        self.observe(name, target, result)
        if not result.get("success"):
            # A stale/moved note gets one bounded search, never an automatic alternate open.
            topic = target["relative_path"].rsplit("/", 1)[-1].removesuffix(".md")
            answer = self.search(topic, action, execute, force_choice=True)
            answer["reply"] = f"原笔记操作失败：{result.get('error') or '无法访问'}\n" + answer["reply"]
            answer["tools"].insert(0, result)
            return answer
        if action == "explain":
            return {"context": str(result.get("result", "")), "tools": [result]}
        return {"reply": str(result.get("result", "")), "tools": [result]}
