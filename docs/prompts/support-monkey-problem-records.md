# Support-Monkey Problem Records Prompt

Use this prompt when incidents repeat, a workaround exists without a permanent
fix, ownership is unclear, or the same defect keeps returning under different
symptoms.

In IT service management, a Problem Record tracks the underlying cause or
suspected cause behind one or more incidents. It is separate from an Incident:
the Incident restores service; the Problem Record drives root-cause analysis,
known-error management, permanent fix planning, and recurrence prevention.

## When To Recommend A Problem Record

Recommend a Problem Record candidate when any of these are true:

- two or more incidents show the same symptom, component, error signature, or
  workaround,
- the incident is resolved by workaround only,
- the root cause is unknown after service restoration,
- a vendor/interface issue recurs,
- a monitoring gap allowed repeated impact,
- product ownership is needed for a permanent fix,
- manual operational effort repeats,
- the issue has material customer, revenue, compliance, or support-load impact.

Do not force a Problem Record for a one-off incident with clear cause, permanent
fix, and low recurrence risk.

## Problem Record Candidate Template

```md
# Problem Record Candidate

Status: DRAFT - HUMAN REVIEW REQUIRED

## Problem Statement

## Linked Incidents

## Known Symptoms

## Affected Services / Components

## Impact Pattern

## Current Workaround

## Known Error / Leading Hypothesis

## Evidence

## Recurrence Signals

## Root Cause Status

## Permanent Fix Options

## Risk If Not Fixed

## Recommended Owner

## Next Investigation Actions

## Acceptance Criteria For Closure

## Open Questions
```

## Evidence Requirements

For each Problem Record candidate, cite:

- linked incident IDs or user-provided case labels,
- common symptoms,
- timestamps or recurrence windows,
- logs/errors/metrics,
- workaround evidence,
- impacted service/component,
- customer or operational impact if known.

If the only evidence is "this feels familiar", mark the candidate as low
confidence and ask for prior incident references, logs, or examples.

## Known Error Handling

If a likely cause and workaround are known, create a `Known Error` section:

- known trigger,
- known affected versions/components,
- safe workaround,
- workaround validation,
- customer/internal wording,
- permanent fix owner,
- monitoring or detection signal.

## Outputs

Produce:

```md
## Problem Record Recommendation

## Linked Evidence

## Recurrence Pattern

## Known Error / Hypothesis

## Workaround

## Business / Support Impact

## Permanent Fix Options

## Proposed Owner And Priority

## Next Checks

## Draft Problem Record
```

## Guardrails

- A Problem Record is not proof of root cause.
- Keep incident restoration separate from permanent-fix investigation.
- Do not blame a team or vendor without evidence.
- Do not expose sensitive incident data in reusable known-error text.
- Prefer a Problem Record over repeated ad hoc Jira tickets when the recurrence
  pattern is clear but the permanent fix is not.
