# Rime Docs: Contributor Guide

This repository is the source for [docs.rime.ai](https://docs.rime.ai), built with [Mintlify](https://mintlify.com). Site configuration lives in `docs.json`.

## Structure

```text
docs/           # Guides, changelog, on-prem docs, integrations
api-reference/  # HTTP and WebSocket API reference
cli-reference/  # Rime CLI reference
mcp-reference/  # Hosted MCP server reference
platform/       # Voice cloning, teams, pronunciation
snippets/       # Reusable MDX snippets
```

## Editorial standard

Write for a developer who needs to make a decision or complete a task.

- Lead with the result, recommendation, constraint, or irreversible consequence. Put background and rationale afterward.
- Never use an em dash (`U+2014`) in documentation. Rewrite the sentence or use a period, colon, comma, semicolon, or parentheses as grammar requires.
- Use specific, confident language. Remove throat-clearing such as “This guide will,” “In today's world,” and “Whether you are.”
- Prefer verifiable technical facts over promotional adjectives. Do not call a feature seamless, powerful, lifelike, enterprise-grade, or state-of-the-art without evidence that belongs on the page.
- State prerequisites, credential boundaries, unsupported configurations, and security consequences before the steps they affect.
- Keep the most useful path prominent. Present alternatives only after the default recommendation is clear.
- Use headings that name the decision or task. Avoid generic endings such as “Next steps,” “Conclusion,” and “Keep building.”
- Preserve technical meaning when editing punctuation. Never apply a blind character replacement without reviewing every changed sentence, table cell, code caption, and link anchor.
- Keep prose concise, but do not make it abrupt. Vary sentence length and use contractions when they sound natural.

## Documentation conventions

- Keep Rime API credentials on the server. Browser examples must call an application backend or a server-side WebSocket bridge.
- Do not describe a general official Rime npm or PyPI SDK. Application code calls the HTTP and WebSocket APIs with standard clients.
- Treat HTTP and persistent WebSockets as the primary application transports. SSE is specific to Mist v2.
- Prefer Mintlify's `Columns` component for new card layouts. Do not introduce new `CardGroup` usage.
- Preserve published routes unless a redirect and migration plan are part of the change.

## Common tasks

**Updating on-prem image tags:**

1. Update the version in `docs/on-prem/quickstart.mdx` under the API or model image section.
2. Add a corresponding `<Update>` entry at the top of `docs/changelog.mdx`.

**Adding a changelog entry:**

Insert an `<Update label="YYYY-MM-DD">` block at the top of the updates list in `docs/changelog.mdx`.

**Local preview:**

```bash
npm i -g mintlify
mintlify dev
```

Before committing, inspect the complete diff, run `git diff --check`, confirm `docs.json` parses, scan tracked prose for `U+2014`, and run Mintlify validation and broken-link checks.
