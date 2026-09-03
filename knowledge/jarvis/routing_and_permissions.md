# JARVIS Routing and Permission Model

## 1. Purpose

JARVIS uses Python-enforced routing and permission policies.

The AI model may recommend an action, but it cannot authorize or execute the
action by itself.


## 2. Routing Principle

Preferred routing order:

Supported simple local operation
→ Native JARVIS Tool

General reasoning
→ Gemini

Knowledge question about indexed information
→ RAG + Gemini

Software-engineering task
→ Codex when available

Unsupported local operation
→ Reject or request an explicitly supported workflow


## 3. Python Enforcement

Routing rules must be enforced in Python.

System prompts may guide model behavior, but system prompts are not security
boundaries.

Before execution, Python must validate:

- tool name
- argument schema
- target resource
- path restrictions
- permission level
- confirmation requirements


## 4. Tool Allow-List

Gemini may only propose tools explicitly declared by JARVIS.

Unknown tools must be rejected.

Tool arguments must match the expected schema before entering the execution
layer.


## 5. Risk Levels

JARVIS should classify executable actions according to risk.

### LOW

Read-only or low-impact actions.

Examples:

- read system information
- read project information
- list files
- read files
- search files
- inspect Git status
- open an application

LOW-risk supported tools may normally execute directly.


### MEDIUM

Actions that change user or project state.

Examples:

- create file
- modify file
- rename file
- move file
- copy file
- change project configuration
- install supported software

MEDIUM-risk operations should require confirmation unless a future explicit
policy safely grants the operation.


### HIGH

Destructive, privileged, security-sensitive, or system-level operations.

Examples:

- delete important files
- administrative actions
- registry modification
- shutdown
- reboot
- security configuration changes
- destructive storage operations

HIGH-risk actions must never silently execute.


## 6. Confirmation Flow

When confirmation is required:

User request
↓
JARVIS creates pending action
↓
JARVIS explains the proposed operation
↓
User accepts or rejects
↓
PermissionManager validates again
↓
Approved action executes

Confirmation must apply to the stored action rather than allowing a new
unvalidated action to replace it.


## 7. Trust-Gated Privileged Mode

Future privileged execution should require both:

1. the computer is already unlocked by the authorized user;
2. the current speaker is verified as the authorized user's voice.

If either condition fails:

JARVIS remains in restricted mode.


## 8. Restricted Mode

Restricted mode should permit only low-risk capabilities.

Examples:

- simple conversation
- read-only information
- system status
- safe application launching
- non-sensitive knowledge retrieval

Privileged or destructive actions must remain blocked.


## 9. Voice Verification Limitation

Voice verification must not be the only authorization mechanism for destructive
or privileged actions.

It should act as one signal inside the broader permission system.


## 10. Secret Protection

The reasoning model and tools must not expose:

- API keys
- passwords
- authentication tokens
- secret configuration files
- private credentials

Secret-bearing files should be blocked from general file retrieval and AI tool
access.


## 11. Core Security Boundary

The required execution sequence is:

AI Proposal
↓
Schema Validation
↓
TaskRouter
↓
PermissionManager
↓
Confirmation when required
↓
Native Execution

No AI provider may bypass this chain.