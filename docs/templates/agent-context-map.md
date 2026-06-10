# Agent Context Map

Purpose: compact infrastructure memory for choosing the right application,
repository, runbook, dashboard, or owner before asking a junior for access.
Optimize this file for token efficiency and precise retrieval. Keep the
interactive human diagram in `support-docs/infrastructure-diagram.html`.

Rules:
- Read this file before asking which repository to inspect.
- Prefer existing node and edge IDs over creating duplicates.
- Cite evidence IDs for every confirmed or likely connection.
- Use `unknown` rather than guessing.
- Update this file when an incident proves, disproves, or refines a connection.
- Keep notes short. Put long explanations in incident artifacts or reference
  docs, not here.

Status values: `confirmed`, `likely`, `possible`, `unknown`, `stale`.

Line format:

```text
N|id|kind|owner|repo|path|status|evidence|tags
E|from|to|relation|direction|status|evidence|tags
R|symptom_or_keyword|target_ids|confidence|evidence|note
```

Fields:
- `N`: node. Use for apps, repos, services, queues, DBs, vendors, dashboards,
  runbooks, feature flags, jobs, lambdas, and teams.
- `E`: edge. Use for calls, publishes, consumes, owns, deploys, stores,
  authenticates, depends_on, monitors, alerts, documents, or escalates_to.
- `R`: routing hint. Use for incident symptoms or keywords that should point
  the assistant at likely nodes before asking for repo access.

Map:

```text
N|customer-portal|frontend|unknown|unknown|unknown|unknown|EV-TBD|sample
N|account-bff|api|unknown|unknown|unknown|unknown|EV-TBD|sample
N|vendor-adapter|integration|unknown|unknown|unknown|unknown|EV-TBD|sample
E|customer-portal|account-bff|calls|outbound|unknown|EV-TBD|sample
E|account-bff|vendor-adapter|calls|outbound|unknown|EV-TBD|sample
R|login timeout|customer-portal,account-bff|possible|EV-TBD|replace sample routing hint
```
