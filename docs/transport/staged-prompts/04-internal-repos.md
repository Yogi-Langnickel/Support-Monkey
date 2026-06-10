# Stage 04: Internal Application Repositories

Paste this when code/config/deployment evidence may be needed.

```text
Internal application repositories are valid evidence sources when access is
approved. The limitation is on cloning the personal public Support-Monkey repo,
not on using internal repos the support engineer is allowed to access.

When repository evidence may be needed:
1. Review `support-docs/agent-context-map.md` first if available. Use its node,
   edge, and routing hints to identify likely applications, repos, owners,
   runbooks, dashboards, and dependencies before asking the user.
2. If the map does not identify the likely context, ask which application, user
   journey, service, API, BFF, experience layer,
   frontend, reverse proxy, backend, config repo, lambda, job, or vendor adapter
   is likely involved. Do not proceed with code reasoning until the needed repo
   or code path is known, or a blocker is recorded.
3. Ask whether I already have an approved local checkout.
4. If not, ask whether I am allowed to clone the internal repo and from where.
5. If access is missing, record an access blocker and propose who/what to ask
   for: repo name, owning team, Teams channel, service catalog entry, or
   Confluence ownership page.
6. Prefer read-only inspection: file search, README/runbook review, config
   lookup, dependency mapping, recent deployment metadata, and cited snippets.
7. Do not ask for secrets, `.env` files, credentials, tokens, private keys, or
   full sensitive configs.
8. Do not propose code changes or branches until evidence supports the likely
   repo and the user explicitly asks for a fix path.

If the incident cannot be understood without code, ask directly:

```text
Which approved internal repository, local checkout path, service catalog entry,
or runbook should I inspect for this incident?
```

If the answer is unknown, record `repo/code path unknown` in
`Facts/context-map.md` and make finding the owner/repo the next small action.

When repository evidence is provided, cite file path, branch/commit if known,
line or snippet labels, and summarize the relevance in evidence-ledger.json.
Also update `support-docs/agent-context-map.md` and
`support-docs/infrastructure-diagram.html` when the evidence confirms,
disproves, or refines an application, repository, owner, dependency, dashboard,
runbook, vendor, queue, database, or information-flow connection.

Bonus fix-branch path:
- Only use this path when evidence shows the incident likely needs a code or
  config fix. Many incidents are data, access, vendor, queue/cache, runtime,
  deployment, or operational issues and should not create code churn.
- Ask the user to confirm the affected internal repo, approved access, target
  base branch, and permission to create a branch.
- Create or propose a branch named `<IncidentNumber>-fix` from the confirmed
  base branch, normally `master`, `main`, or the active release branch.
- Keep changes surgical: no unrelated refactors, no broad formatting, no
  dependency churn, and no speculative fixes.
- Record why a code fix is needed, what non-code paths were ruled out, the
  files touched, tests or validation run, rollback notes, and any PR/link in
  the incident artifacts.
- If a fix is not available, provide a concise workaround, data repair path,
  Problem Record candidate, vendor escalation, or ownership handoff instead.
```
