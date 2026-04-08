# Rime Docs

Source for [docs.rime.ai](https://docs.rime.ai), built with [Mintlify](https://mintlify.com).

## Structure

```
docs/           # Main documentation pages (guides, changelog, on-prem, integrations)
api-reference/  # API reference pages (Mist v2, Mist v3, Arcana)
cli-reference/  # CLI reference pages
platform/       # Platform pages (voice cloning, teams, speech QA)
snippets/       # Reusable MDX snippets
```

Navigation and site config live in `docs.json`.

## Local development

```bash
npm i -g mintlify
mintlify dev
```

The preview runs at `http://localhost:3000`.

## Deployment

Pushing to `main` automatically deploys to [docs.rime.ai](https://docs.rime.ai) via the Mintlify GitHub app.
