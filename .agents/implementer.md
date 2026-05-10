# Implementer responsibilities

This file is **instructions to you**, an implementing agent in this repository — whether you are the primary
agent or a subagent that writes or edits files. Read it in full and adopt every rule below as a responsibility
you carry for the entire run.

## Always verify your work before considering a change complete.

Project-defined verification commands and pass criteria are in
[`policy/verification-gates.md`](../policy/verification-gates.md). The inspection step below applies on top.

### Run IDE inspections on every changed file.

When the JetBrains IDE MCP is exposed in this session, run `get_file_problems` with `errorsOnly: false` on
every file you touched before declaring the task complete. The schema is registered as a *deferred* tool — its
name appears in the session's deferred-tools `<system-reminder>` but calling it directly fails until the schema
is loaded. Discover it via `ToolSearch{query: "get_file_problems"}`, then load the schema with
`ToolSearch{query: "select:<full-name>"}`. If a reported "build problem" is contradicted by a clean local
build, the IDE's index is stale — re-sync the project (or the affected module) and re-run the inspection
against a current index.

**Before every reply that follows a file edit, run `get_file_problems` on each file you touched.**
