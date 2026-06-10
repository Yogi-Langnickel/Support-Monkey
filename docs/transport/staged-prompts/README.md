# Staged Activation Prompts

Use these when a single large prompt is awkward in the enterprise AI assistant.
Paste them in order as needed.

1. `00-core-activation.md`
2. `01-case-artifacts.md`
3. `02-evidence-gate.md`
4. `03-rovo-bridge.md`
5. `04-internal-repos.md`
6. `05-incident-start.md`
7. `06-closure-archive-learning.md`
8. `07-incident-coordinator.md`
9. `08-junior-chaos-control.md`

Default investigation set:

- `00-core-activation.md`
- `01-case-artifacts.md`
- `02-evidence-gate.md`
- `03-rovo-bridge.md`
- `04-internal-repos.md`
- `06-closure-archive-learning.md`
- `07-incident-coordinator.md`
- `08-junior-chaos-control.md`
- `05-incident-start.md`

`03-rovo-bridge.md` and `04-internal-repos.md` are part of the normal
investigation setup because Confluence/Rovo research and internal repo
discovery are common support paths. Prompt 04 also includes the optional
`<IncidentNumber>-fix` branch path when a minimal code or config fix is
evidence-backed and approved.
Add or pre-load `06-closure-archive-learning.md` so the assistant knows how to
close, archive, create learning candidates, and prepare reviewed memory.
Add `07-incident-coordinator.md` when you want Support-Monkey to maintain an
incident-command state, context map, decision log, handoff pack, and escalation
review while guiding juniors.
Add `08-junior-chaos-control.md` when the main risk is messy junior input:
fragmented ticket notes, vague assumptions, weak evidence, premature RCA, or
copy-pasted worknotes that need structure before they enter ServiceNow.

Suggested junior instruction:

```text
Create your workspace folder.
Paste prompt 00. Wait for the assistant to finish.
Paste prompt 01. Wait for the assistant to finish.
Paste prompt 02. Wait for the assistant to finish.
Paste prompt 03. Wait for the assistant to finish.
Paste prompt 04. Wait for the assistant to finish.
Paste prompt 06. Wait for the assistant to finish.
Paste prompt 07. Wait for the assistant to finish.
Paste prompt 08. Wait for the assistant to finish.
Paste prompt 05. Wait for the assistant to ask for the incident.
Then say: I have a new incident INC001234.
```

Paste prompt 07 during setup when you want coordinator behavior active from
the start.
Paste prompt 08 during setup when Support-Monkey is primarily guiding juniors
through chaotic or low-quality incident input.
