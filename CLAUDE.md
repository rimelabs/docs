# Rime Docs — Claude Code Guide

This repo is the source for [docs.rime.ai](https://docs.rime.ai), built with [Mintlify](https://mintlify.com). Config lives in `docs.json`.

## Structure

```
docs/           # Guides, changelog, on-prem docs, integrations
api-reference/  # API reference (Mist v2, Mist v3, Arcana)
cli-reference/  # CLI reference
platform/       # Voice cloning, teams, speech QA
snippets/       # Reusable MDX snippets
```

## Common tasks

**Updating on-prem image tags:**
1. Update the version in `docs/on-prem/quickstart.mdx` under the "API service" section.
2. Add a corresponding `<Update>` entry at the top of `docs/changelog.mdx`.

**Adding a changelog entry:** Insert an `<Update label="YYYY-MM-DD">` block at the top of the updates list in `docs/changelog.mdx`.

**Local preview:**
```bash
npm i -g mintlify
mintlify dev
```
