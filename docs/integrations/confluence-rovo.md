# Confluence And Rovo Integration

Support-Monkey should use Confluence and Rovo as internal knowledge sources for
runbooks, ownership, known errors, monitoring, dependencies, workarounds, and
validation guidance.

## Recommended Path

For the Monday pilot, do not integrate directly. Use:

```sh
support-monkey rovo-questions cases/<IncidentNumber>
```

Paste the generated questions into Rovo Chat in Confluence or Jira. Record useful
cited answers with:

```sh
support-monkey add-evidence cases/<IncidentNumber> \
  --source Confluence \
  --type runbook \
  --strength hard \
  --reference "<page title or URL>" \
  --summary "<short cited finding>" \
  --supports owner
```

This keeps the workflow reliable on a Windows plus Ubuntu WSL setup and avoids
credential setup during the first junior test.

## API Options

There are three likely integration levels:

1. Confluence REST search with an Atlassian API token.
   This is the simplest programmatic route. It can search/read pages the token
   owner can access, then Support-Monkey can summarize cited page results.

2. Rovo through Atlassian/Forge.
   Forge supports Rovo agents and a bridge API that can open the Rovo chat panel
   with a prompt from a Forge app. This is useful inside Atlassian UI flows, not
   a simple local CLI API key integration.

3. Rovo plus MCP/admin-managed integrations.
   Some Rovo integrations require site-admin setup in Atlassian Admin Hub. Treat
   this as a later enterprise integration, not Monday pilot work.

## Guardrails

- Do not store API tokens in the repo.
- Prefer environment variables or an approved local secret store.
- Use a least-privilege service account if workplace policy allows it.
- Treat Rovo answers as soft until they include cited pages or are backed by
  monitoring, repo, runbook, or ticket evidence.
- Record only page titles, URLs, and concise summaries in the case unless a
  runbook excerpt is necessary.
