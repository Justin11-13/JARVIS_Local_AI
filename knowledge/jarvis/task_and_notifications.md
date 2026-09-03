# JARVIS Task and Notification System

## 1. Task Manager

The Task Manager tracks work performed or coordinated by JARVIS.

Current implementation:

services/task_manager.py


## 2. Task Record

Managed tasks should support:

- id
- title
- agent
- status
- created_at
- started_at
- completed_at
- date
- duration_seconds
- result
- error


## 3. Task Status

Supported task states should include:

- queued
- running
- waiting_approval
- completed
- completed_with_warnings
- failed
- cancelled


## 4. Task Lifecycle

Typical lifecycle:

Task Created
↓
Queued
↓
Running
↓
Completed

A task requiring permission may instead enter:

waiting_approval

before execution.


## 5. Task History

JARVIS should preserve enough task information to allow the user to understand:

- what was requested
- what executed it
- when it started
- when it finished
- how long it took
- whether it succeeded
- what result was produced
- what error occurred


## 6. Notification System

Current implementation:

services/notification_service.py

Current output:

Terminal notification

Example:

[JARVIS Notification] 任务已完成。


## 7. Future Notification Channels

Future notification outputs may include:

- Windows toast
- desktop notification
- system tray
- desktop pet / orb
- voice
- task history UI


## 8. Notification Principle

Notifications should report meaningful task events without overwhelming the
user.

Typical events include:

- task completed
- task failed
- confirmation required
- long-running task finished
- important warning