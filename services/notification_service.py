class NotificationService:
    def notify_task_status(
        self,
        status: str,
        title: str = "",
        result: str = "",
        error: str = "",
    ) -> str:
        if status == "completed":
            message = "任务已完成。"

        elif status == "completed_with_warnings":
            message = "任务已完成，但有需要注意的问题。"

        elif status == "failed":
            message = "任务执行失败。"

        elif status == "timeout":
            message = "任务执行超时。"

        elif status == "cancelled":
            message = "任务已取消。"

        elif status == "validation_failed":
            message = "任务无法开始，请检查任务参数。"

        else:
            message = f"任务状态已更新：{status}"

        if title:
            clean_title = title.rstrip("。.!！?？:：")
            message = f"{clean_title}：{message}"

        return message