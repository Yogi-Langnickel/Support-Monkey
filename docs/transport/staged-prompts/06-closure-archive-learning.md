# Stage 06: Closure, Archive, And Learning

Paste this when the incident is close to resolution, or include it during
activation if you want the assistant to know the full lifecycle upfront.

```text
When I confirm the incident is closed or ready to close, do not just stop.
Perform the closure process:

1. Ask for the final closure confirmation and closure timestamp.
2. Verify the resolution gate:
   - symptom understood
   - impact documented
   - timeline documented
   - owner/component identified or blocker recorded
   - technical evidence captured
   - resolution path/workaround documented
   - validation evidence captured
3. If the gate is incomplete, list the exact missing evidence and ask whether to
   close with a documented blocker, create a Problem Record candidate, or keep
   investigating.
4. Produce final copyable artifacts:
   - outcomes/final-summary.md
   - closure-worknote
   - caller/call-centre update draft
   - internal business/stakeholder update draft
   - outcomes/problem-record-candidate.md if recurrence, unknown root cause,
     workaround-only resolution, or permanent-fix ownership remains
5. Archive the incident in prompt-only mode by producing a copyable
   closed-incident-archive block containing:
   - incident number
   - opened/closed timestamps
   - duration if known
   - symptom
   - impact
   - evidence list
   - resolution path
   - whether a code fix was needed
   - fix branch or PR if created
   - no-code reason if the resolution was data, access, vendor, queue/cache,
     runtime, deployment, or operational
   - validation
   - blockers
   - follow-ups
6. Create learning-candidate.md:
   - mark it PENDING HUMAN REVIEW
   - remove secrets, customer data, internal URLs, hostnames, and account IDs
   - capture reusable symptoms, repo/service patterns, safe checks, Rovo queries,
     runbook links/titles, known workarounds, validation patterns, access
     blockers, data-issue patterns, and minimal-fix patterns
   - do not promote to durable memory until a senior reviews it
7. Create memory-candidate.md:
   - only general reusable engineering knowledge
   - no raw logs, secrets, customer identifiers, or unreviewed RCA claims
   - include evidence IDs that support the learning

The long-term goal is that Support-Monkey grows into a large internal
engineering knowledgebase, but every learning must be evidence-backed,
redacted, and human-reviewed before it becomes durable memory.
```
