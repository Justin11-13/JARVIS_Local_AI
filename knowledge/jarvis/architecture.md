# JARVIS Architecture

## 1. Architecture Overview

JARVIS uses a layered assistant architecture in which AI reasoning is separated
from local execution.

Target high-level flow:

User Text / Voice
        ↓
JARVIS Core
        ↓
Input Understanding
        ↓
Task Router
        ↓
┌───────────────────────────────┐
│ Native Tools                  │
│ Gemini Reasoning              │
│ RAG Knowledge Retrieval       │
│ Long-Term Memory              │
│ Codex                         │
│ Future Specialist Agents      │
└───────────────────────────────┘
        ↓
Permission Manager
        ↓
Task Manager
        ↓
Execution / Response
        ↓
Notification System


## 2. JARVIS Core

JARVIS Core is the central coordinator.

Its responsibilities include:

- receiving user requests
- maintaining conversation state
- selecting the appropriate route
- coordinating reasoning and tools
- enforcing execution boundaries
- recording managed tasks
- returning results to the user

The Core must not become a collection of unrelated implementation logic.

Specialized responsibilities should remain inside services and tools.


## 3. Reasoning Layer

Gemini is the primary reasoning model when AI interpretation or general
reasoning is required.

Gemini may:

- understand natural-language requests
- classify intent
- reason about tasks
- propose declared JARVIS tools
- generate natural-language responses

Gemini must not:

- execute commands directly
- bypass Python policy
- access arbitrary local files
- receive unrestricted Windows control
- retrieve secrets such as API keys


## 4. Execution Layer

Supported computer actions should be implemented as native JARVIS tools.

Native tools may use:

- Python
- Windows APIs
- carefully bounded PowerShell
- application-specific interfaces

Tools should expose narrow, explicit functions instead of unrestricted command
execution.


## 5. Specialist Layer

Specialized agents may be integrated for tasks that benefit from dedicated
capabilities.

Planned specialist:

Codex
→ software-engineering and repository work

Future specialists may be added without changing the core execution boundary.


## 6. Knowledge Layer

JARVIS should use two different persistent information systems.

RAG Knowledge Base:
- project documentation
- technical notes
- reference material
- structured JARVIS knowledge
- user-added knowledge sources

Long-Term Memory:
- stable user preferences
- important previous decisions
- persistent interaction context
- relevant personal assistant state

RAG and long-term memory must remain separate responsibilities.


## 7. Current Runtime Flow

Current desktop/API request flow:

User
↓
Flutter Desktop UI
↓
FastAPI
↓
Local intent resolver or Gemini
↓
Declared tool proposal
↓
Python validation
↓
TaskRouter
↓
PermissionManager
↓
Approved native tool
↓
Task result
↓
Desktop chat response


## 8. Project Structure

Approximate architecture:

JARVIS/
├── app/
├── config/
├── desktop_ui/
├── knowledge/
├── memory/
├── services/
├── skills/
├── tests/
├── ui/
├── AGENTS.md
├── README.md
└── requirements.txt

Key responsibilities:

app/
→ runtime and API coordination

services/
→ routing, permissions, tasks, notifications, integrations

skills/
→ native JARVIS capabilities

knowledge/
→ RAG knowledge sources

memory/
→ persistent JARVIS memory

tests/
→ automated tests


## 9. Architecture Boundary

Reasoning and execution must remain separated.

AI:
understand → reason → propose

Python:
validate → authorize → execute

This boundary is a core JARVIS security requirement.

## 10. RAG Architecture

JARVIS uses local semantic retrieval...