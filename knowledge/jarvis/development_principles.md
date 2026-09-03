# JARVIS Development Principles

## 1. General Workflow

Prefer:

see → understand → implement → run → observe → adjust


## 2. Before Coding

Before modifying the project:

1. understand the requested outcome;
2. inspect the existing implementation;
3. identify the relevant files;
4. reuse existing patterns;
5. change the smallest reasonable set of files;
6. preserve currently working functionality.


## 3. Simplicity

Do not over-engineer.

Do not introduce abstractions, services, frameworks, or dependencies unless
they solve a current problem.

Prefer the simplest implementation that remains understandable and testable.


## 4. Separation of Responsibilities

Keep major responsibilities separated.

Routing policy
→ TaskRouter

Permission decisions
→ PermissionManager

Task lifecycle
→ TaskManager

Notifications
→ NotificationService

External AI integration
→ dedicated integration / adapter

Native computer capabilities
→ skills


## 5. Safety

Do not:

- remove routing guards
- weaken permission checks
- expose unrestricted shell access
- silently broaden filesystem access
- expose secrets to AI providers
- allow AI output to bypass validation


## 6. Native Tools

Native tools should:

- remain narrow
- validate input
- minimize side effects
- provide structured output
- fail safely
- remain testable


## 7. AI Integration

The model should handle reasoning.

Python should handle authority.

Never depend on prompt instructions alone for computer security.


## 8. Testing

After relevant changes:

- run syntax checks
- run affected tests
- test routing behavior
- test permission behavior
- test failure paths when practical

Routing and security changes require particular care.


## 9. Incremental Development

Prefer small working improvements over large speculative rewrites.

Preserve working modules unless a rewrite has a clear technical requirement.