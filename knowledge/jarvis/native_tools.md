# JARVIS Native Tools

## 1. Purpose

Native tools provide controlled local computer capabilities without exposing an
unrestricted shell to the AI model.

Native tools should be preferred whenever a requested operation already has a
safe and deterministic JARVIS implementation.


## 2. Windows Applications

Current capabilities include:

- discover installed applications
- exact application matching
- partial matching
- fuzzy matching
- open installed applications

Application discovery may use supported Windows application sources such as the
Start Menu and system application registration information.


## 3. System Monitoring

Current system capabilities include:

- CPU usage
- physical memory usage
- supported NVIDIA GPU monitoring

System monitoring is exposed through the local API.

CPU and memory monitoring use psutil where appropriate.


## 4. Project Registry

JARVIS can discover development projects from explicitly configured project
roots.

Supported project detection includes:

- Laravel / PHP
- Django / Python
- Node.js
- Maven
- Gradle
- Git repositories

Current project operations include:

- list projects
- get project information
- refresh project registry
- open registered project in VS Code

Project discovery must remain restricted to configured roots.


## 5. Git Tools

Current Git capabilities include:

- read Git status for registered projects

Future Git operations should be implemented as explicit functions rather than
through unrestricted shell access.


## 6. File Tools

Current native file operations are read-only and restricted to registered
projects.

Supported functions include:

- list files
- read files
- search files

Native project file tools must not modify files unless a separate explicitly
authorized write capability is introduced.


## 7. Path Rules

Registered project operations must remain scoped to the selected project.

Project root should use:

.

as the relative project path.

Arbitrary Windows absolute paths must not be accepted as project-relative paths.


## 8. Native Tool Design Rules

Each native tool should:

- perform one clearly defined capability
- validate its arguments
- minimize permissions
- return structured results
- avoid hidden side effects
- fail safely
- remain independently testable

An unrestricted command executor must not be treated as a normal native tool.