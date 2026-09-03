# JARVIS AI and Specialist Integrations

## 1. Integration Principle

JARVIS may integrate external AI providers or specialist agents when they add
useful capabilities.

External integrations remain subordinate to JARVIS routing, permission, and
execution policy.


## 2. Gemini

Gemini is the current primary AI reasoning backend.

JARVIS uses Gemini through user-provided API credentials.

Gemini is responsible for:

- natural-language understanding
- general reasoning
- intent interpretation
- response generation
- proposing declared JARVIS tools

Gemini does not receive unrestricted local computer access.


## 3. Gemini Tool Proposal Boundary

Gemini may only propose declared JARVIS functions.

Python validates:

- function name
- argument structure
- requested target
- permission requirements

before execution.

Gemini itself never executes Windows commands.


## 4. Codex

Codex is intended to act as the software-engineering specialist.

Suitable tasks include:

- repository-wide code changes
- multi-file implementation
- refactoring
- debugging
- test-and-fix workflows
- large feature implementation
- codebase inspection

JARVIS remains the coordinator.


## 5. Codex Routing

Preferred routing:

Project inspection
→ Native project tools

General reasoning
→ Gemini

Software-engineering implementation
→ Codex

Computer operation
→ Native JARVIS tools


## 6. Future Specialist Agents

Additional specialist integrations may be introduced when they provide a clear
benefit.

Every specialist must have:

- a defined responsibility
- a bounded interface
- explicit routing rules
- permission enforcement
- failure handling

Specialists must not receive unrestricted authority simply because they are
connected to JARVIS.


## 7. Optional Integration Principle

External integrations should remain optional where practical.

Failure or absence of one integration should not unnecessarily break unrelated
JARVIS native capabilities.