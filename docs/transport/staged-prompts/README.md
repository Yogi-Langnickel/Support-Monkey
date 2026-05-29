# Staged Activation Prompts

Use these when a single large prompt is awkward in the enterprise AI assistant.
Paste them in order as needed.

1. `00-core-activation.md`
2. `01-case-artifacts.md`
3. `02-evidence-gate.md`
4. `03-rovo-bridge.md`
5. `04-internal-repos.md`
6. `05-monday-start.md`
7. `06-closure-archive-learning.md`

Minimum Monday set:

- `00-core-activation.md`
- `01-case-artifacts.md`
- `02-evidence-gate.md`
- `06-closure-archive-learning.md`
- `05-monday-start.md`

Add `03-rovo-bridge.md` when Confluence/Rovo is needed.
Add `04-internal-repos.md` when the incident points to code, configuration,
deployment, ownership, or dependency evidence in an internal application repo.
Prompt 04 also includes the optional `<IncidentNumber>-fix` branch path when a
minimal code or config fix is evidence-backed and approved.
Add or pre-load `06-closure-archive-learning.md` so the assistant knows how to
close, archive, create learning candidates, and prepare reviewed memory.

Suggested junior instruction:

```text
Create your workspace folder.
Paste prompt 00. Wait for the assistant to finish.
Paste prompt 01. Wait for the assistant to finish.
Paste prompt 02. Wait for the assistant to finish.
Paste prompt 06. Wait for the assistant to finish.
Paste prompt 05. Wait for the assistant to ask for the incident.
Then say: I have a new incident INC001234.
```

Paste prompt 03 later when Rovo/Confluence is needed.
Paste prompt 04 later when the incident points to an internal app/repo.
