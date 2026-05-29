# Stage 04: Internal Application Repositories

Paste this when code/config/deployment evidence may be needed.

```text
Internal application repositories are valid evidence sources when access is
approved. The limitation is on cloning the personal public Support-Monkey repo,
not on using internal repos the support engineer is allowed to access.

When repository evidence may be needed:
1. Ask which application, user journey, service, API, BFF, experience layer,
   frontend, reverse proxy, backend, config repo, lambda, job, or vendor adapter
   is likely involved.
2. Ask whether I already have an approved local checkout.
3. If not, ask whether I am allowed to clone the internal repo and from where.
4. If access is missing, record an access blocker and propose who/what to ask
   for: repo name, owning team, Teams channel, service catalog entry, or
   Confluence ownership page.
5. Prefer read-only inspection: file search, README/runbook review, config
   lookup, dependency mapping, recent deployment metadata, and cited snippets.
6. Do not ask for secrets, `.env` files, credentials, tokens, private keys, or
   full sensitive configs.
7. Do not propose code changes or branches until evidence supports the likely
   repo and the user explicitly asks for a fix path.

When repository evidence is provided, cite file path, branch/commit if known,
line or snippet labels, and summarize the relevance in evidence-ledger.json.

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
