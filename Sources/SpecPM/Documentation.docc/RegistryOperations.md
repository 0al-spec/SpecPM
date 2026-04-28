# Registry Operations

SpecPM's current public registry is intentionally static. Fresh package
metadata is promoted through reviewed source changes, generated into `/v0`
JSON, and deployed through GitHub Pages.

## Fresh Deploys

Public static index deployment follows this path:

```text
reviewed source change
        |
        v
CI validation and public-index generation
        |
        v
merge to main
        |
        v
GitHub Pages static /v0 deployment
        |
        v
make pages-smoke
```

Before merge, registry-related changes should be checked against the live local
Docker service:

```bash
make dev-reload
```

After deployment, verify the public registry:

```bash
make pages-smoke
```

## Backup and Restore

Current public registry state is reproducible from:

- Git history;
- `public-index/accepted-packages.yml`;
- repository-local package directories;
- pinned public Git source revisions;
- generated GitHub Pages artifacts;
- GitHub Issues and workflow artifacts for review history.

Restore is Git-based: return to a known-good source state, regenerate static
metadata, redeploy through GitHub Pages, and verify with `make pages-smoke`.

## Abuse and DDoS Boundary

The public registry avoids request-time compute. Public `/v0` reads are static
files, package validation runs in GitHub Actions, and there is no unauthenticated
upload or mutation endpoint.

Future mutable registries or online intent-to-spec APIs need separate
production controls:

- authentication and authorization;
- rate limits and quotas;
- CDN or WAF policy;
- bounded validation concurrency;
- circuit breakers;
- LLM token and cost budgets;
- audit logging;
- monitoring and alerting.

Intent-to-spec endpoints belong in ContextBuilder, SpecGraph, or a downstream
resolver. They are not current SpecPM core behavior.

## Source Contract

The detailed runbook is maintained in `specs/REGISTRY_OPERATIONS.md`.
