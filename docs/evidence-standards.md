# Evidence Standards

Support-Monkey uses a structured evidence ledger so incident conclusions can be
checked by the resolution gate instead of inferred from prose alone.

## Evidence Ledger Schema

Each evidence item should use these fields when available:

```json
{
  "id": "EV-001",
  "source": "CloudWatch",
  "type": "log",
  "strength": "hard",
  "reference": "checkout-service/2026-05-24T03:12:00Z",
  "confidence": "confirmed",
  "observedAt": "2026-05-24T03:12:00Z",
  "supports": ["timeline", "technical_evidence", "impact"],
  "validationPattern": "",
  "summary": "HTTP 502 spike begins at the same time callers report checkout failures."
}
```

Required evidence classes for the resolution gate are:

- `symptom`
- `impact`
- `timeline`
- `owner`
- `technical_evidence`
- `resolution_path`
- `validation`

Use `supports` to state which classes an evidence item satisfies. The CLI also
validates `supports` against the required resolution-gate classes. Metadata and
keywords in summaries do not satisfy the resolution gate by themselves; record
an evidence item with the relevant explicit classes.

Timeline and impact `evidenceId` / `evidenceIds` values must refer to IDs that
exist in the evidence ledger. Broken citations keep the resolution gate in
`needs_more_evidence`.

Evidence IDs must be unique. Duplicate IDs make citations ambiguous and keep
the resolution gate in `needs_more_evidence`.

## Evidence Strength

- `hard`: Logs, metrics, traces, deployment records, configuration records,
  repository diffs, synthetic checks, vendor payloads, interface contracts, or
  authoritative runbook ownership records.
- `soft`: Pasted chat, email, verbal reports, user reports, screenshots, or
  ticket text that reports symptoms without independent technical proof.
- `unknown`: Evidence strength has not been classified yet.

Soft evidence can prove that something was reported. It should not by itself
prove root cause, technical resolution, or permanent fix.

## Confidence Labels

- `confirmed`: Two independent hard evidence sources, or one authoritative hard
  source plus validation evidence.
- `likely`: One hard evidence source that is consistent with the timeline and
  has no strong contradiction.
- `possible`: A plausible hypothesis that has not been disproven but lacks
  direct hard evidence.
- `unknown`: Evidence is absent, insufficient, or materially conflicting.

## Timeline Standard

Use ISO 8601 timestamps for incident start, detection, mitigation, recovery, and
validation events. Every timeline entry should cite an evidence ID.

```json
{
  "occurredAt": "2026-05-24T03:12:00Z",
  "summary": "Checkout 502 rate exceeded alert threshold.",
  "evidenceId": "EV-001"
}
```

## Impact Standard

Prefer quantitative or bucketed impact over qualitative terms like "many users".

```json
{
  "scope": "multi_tenant",
  "depth": "partial_outage",
  "affectedUsersEstimate": 42,
  "evidenceIds": ["EV-002"]
}
```

Recommended `scope` values are `single_user`, `single_tenant`, `multi_tenant`,
`fleet_wide`, and `unknown`.

Recommended `depth` values are `latency_degradation`, `partial_outage`,
`total_outage`, `data_quality`, and `unknown`.

## Validation Patterns

- `synthetic`: A canary, curl, smoke test, or synthetic monitor proves the
  affected journey works after the change.
- `log_based`: The relevant error code, exception, or failed state disappears
  from logs for the agreed observation window.
- `metric_based`: Error rate, latency, queue depth, or another SLI returns to
  normal range for the agreed observation window.
- `deployment_based`: A fix, rollback, config change, or feature-flag change is
  verified in the expected environment.
- `user_based`: Reporter, customer, or business owner confirms the symptom is
  gone. Treat this as soft validation unless paired with hard evidence.

## ITIL/SRE Vocabulary

- `Incident`: A service interruption or degradation where the immediate goal is
  restoration.
- `Service Request`: A user request that is not a break/fix incident.
- `Problem Record`: A durable record for underlying cause, recurrence, or a
  known issue requiring permanent-fix ownership.
- `Known Error`: A problem with known symptoms, cause or suspected cause, and a
  documented workaround.
- `SLI`: A measured service indicator such as availability, latency, error
  rate, or saturation.
- `SLO`: The target threshold for an SLI.
