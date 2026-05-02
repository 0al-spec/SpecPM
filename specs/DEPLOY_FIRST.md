# SpecPM Deploy-First Workflow

Status: Draft
Updated: 2026-04-28
Scope: current live development and static production deployment loop

## Purpose

SpecPM follows a deploy-first operating model: even the smallest useful
registry surface should be runnable as a live service and smoke-tested through
the same client contract that downstream consumers use.

The current deployable surface is intentionally narrow:

- a Docker-backed local public index service;
- a GitHub Pages static `/v0` registry;
- read-only `specpm remote` smoke checks.

This document does not introduce a remote mutation API, `specpm publish`,
authentication, package installation, archive download behavior, package
execution, or online intent-to-spec runtime.

## Current Local Deployment

The local live service is the Docker Compose `public-index` service:

```bash
make dev-up
```

It builds the `specpm:dev` image, starts the `public-index` container,
generates `.specpm/public-index` from `public-index/accepted-packages.yml`, and
serves the static registry at:

```text
http://localhost:8081/v0
```

Smoke the live service with the baseline registry check:

```bash
make dev-smoke
```

For full public alpha visibility, run:

```bash
make public-alpha-smoke
make public-alpha-report
```

`public-alpha-smoke` includes the baseline public index smoke checks and then
verifies alpha package, version, and capability visibility for the current seed
package set. `public-alpha-report` writes the same observation as reusable JSON
evidence under `.specpm/public-alpha-observation.json`. The smoke and report
targets read the registry through `specpm remote`:

```text
/v0/status
/v0/packages
/v0/capabilities/{capability_id}/packages
```

## Reloading Fresh Local Versions

The `public-index` service generates the static index at container startup.
After changing package manifests, accepted package sources, generator code, or
registry contract code, recreate the container:

```bash
make dev-reload
```

This force-recreates the Docker Compose service and then runs the same live
smoke checks. Use `make dev-reload` as the default local deploy gate for
registry-related changes.

Stop the local service with:

```bash
make dev-down
```

## Current Production Deployment

The current production-like public deployment is GitHub Pages:

```text
https://0al-spec.github.io/SpecPM
```

The Pages artifact contains both:

- DocC documentation under `/documentation/specpm/`;
- generated static registry metadata and archives under `/v0`;
- a static browser viewer under `/viewer/`.

Smoke the deployed registry with:

```bash
make pages-smoke
make pages-alpha-smoke
```

This command uses `specpm remote` against:

```text
https://0al-spec.github.io/SpecPM
```

## Fresh Version Deployment Strategy

Current public deployment is push-to-main static deployment:

1. Maintainers update `public-index/accepted-packages.yml` or package sources.
2. CI validates package shape and public index generation.
3. The GitHub Pages workflow builds DocC and generated `/v0` metadata.
4. GitHub Pages serves the new static artifact.
5. Operators run `make pages-alpha-smoke` after deployment when validating the
   public alpha manually. This includes the baseline `make pages-smoke` checks.
6. Operators run `make pages-alpha-report` when downstream tooling needs a
   reusable JSON observation artifact.

Future enterprise deployment work may introduce separate release channels,
private registry storage, authenticated promotion, staged rollout, and rollback
policy. Those are outside the current public static index contract.

The detailed deployment, rollback, backup, restore, and abuse-control runbook is
tracked in `specs/REGISTRY_OPERATIONS.md`.

## Backup Strategy

Current public registry state is source-controlled and reproducible:

- accepted package sources live in `public-index/accepted-packages.yml`;
- local package fixtures live in the repository;
- pinned remote package sources must include exact commit revisions;
- generated `/v0` artifacts are reproducible from source plus pinned revisions;
- Git history and GitHub Pages deployment history provide the first rollback
  mechanism.

Future backup work should define:

- artifact retention for generated `/v0` snapshots;
- offsite backup of accepted package manifests and generated archives;
- restore tests that regenerate a historical registry snapshot;
- enterprise backup policy for private package metadata, archives, audit logs,
  and namespace decisions.

The current restore procedure and future backup requirements are tracked in
`specs/REGISTRY_OPERATIONS.md`.

## Flood and DDoS Boundary

The current public deployment is static GitHub Pages hosting. It avoids custom
server-side compute on public requests, which reduces the immediate attack
surface for registry metadata reads.

Current mitigations:

- static files only for public `/v0` reads;
- no public mutation API;
- no package execution;
- issue-based public submissions instead of unauthenticated upload endpoints;
- GitHub Actions validation rather than request-time validation;
- exact metadata lookup instead of server-side semantic search.

Future protection work should define:

- GitHub Issue intake moderation and rate policy;
- submission validation concurrency limits;
- enterprise registry authentication and authorization;
- request throttling for any future online API;
- CDN/cache policy for public registry reads;
- abuse monitoring and alerting;
- separate controls for future intent-to-spec endpoints, because LLM-backed
  APIs have different cost and abuse characteristics.

The current abuse boundary and future DDoS control requirements are tracked in
`specs/REGISTRY_OPERATIONS.md`.

## Operator Rule

For registry-related changes, treat the local Docker service as the first live
deployment:

```bash
make dev-reload
make pages-smoke
```

If `make pages-smoke` cannot be run because a PR has not been deployed to
Pages, say that explicitly in the validation notes and rely on CI Pages build
checks until merge.
