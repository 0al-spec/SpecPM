# SpecPM Registry Operations Runbook

Status: Draft
Updated: 2026-04-28
Scope: public static index operations and future enterprise/online service
boundaries

## Purpose

This runbook defines the current operational model for deploying fresh SpecPM
registry metadata, restoring registry state, and limiting abuse risk.

The current production-like public registry is static GitHub Pages hosting.
SpecPM does not currently run a mutable public registry backend, upload API,
package publish service, package install service, or online intent-to-spec API.

## Current Surfaces

Current live surfaces:

- local Docker Compose public index at `http://localhost:8081/v0`;
- GitHub Pages static public index at `https://0al-spec.github.io/SpecPM/v0`;
- GitHub Issue forms for public package submission, removal requests, and
  namespace claims;
- GitHub Actions workflows for validation, DocC, static `/v0` generation, and
  read-only summary artifacts.

Current public request handling is static-file based. Public registry reads do
not execute package content, run server-side package validation, call an LLM, or
mutate registry state.

## Fresh Version Deployment

### Public Static Index

Fresh public versions are deployed through reviewed source changes:

1. Maintainers update repository-local packages or
   `public-index/accepted-packages.yml`.
2. Remote accepted sources must stay pinned to exact 40-character commit
   revisions.
3. Pull request CI validates package shape, source pinning, public index
   generation, DocC, tests, and formatting.
4. After merge to `main`, the GitHub Pages workflow builds DocC and generated
   `/v0` metadata into one static artifact.
5. Operators verify the deployed registry with:

```bash
make pages-smoke
```

Local registry-related changes should be checked before merge with:

```bash
make dev-reload
```

### Rollback

Current rollback is Git-based:

1. Identify the last known-good commit or accepted manifest state.
2. Revert or supersede the bad package source/manifest change.
3. Regenerate and redeploy the GitHub Pages artifact from `main`.
4. Run `make pages-smoke`.
5. If downstream systems observed the bad snapshot, record the incident in the
   relevant issue or pull request.

This rollback model works because public `/v0` metadata is reproducible from
repository state plus pinned public source revisions.

### Future Enterprise Deployment

Enterprise registry deployments may need:

- staged environments such as dev, staging, and production;
- immutable generated artifacts with versioned promotion records;
- private object storage for archives and registry metadata;
- authenticated deployment promotion;
- rollback to named registry snapshots;
- audit trails for deploy, restore, removal, and yanking decisions;
- compatibility smoke tests for internal SpecGraph and ContextBuilder
  consumers.

These features are not part of the public static index MVP contract.

## Backup and Restore

### Current Backup Sources

Current public registry state is backed by reproducible source inputs:

- Git history for SpecPM;
- `public-index/accepted-packages.yml`;
- repository-local package directories;
- pinned public Git repository URLs, refs, revisions, and package paths;
- generated GitHub Pages deployment artifacts;
- GitHub Issues and workflow artifacts for submission, removal, namespace, and
  decision history.

### Restore Procedure

To restore a public static registry snapshot:

1. Choose the target SpecPM commit and accepted package manifest state.
2. Check out that commit.
3. Rebuild the local static index:

```bash
make public-index-generate
```

4. Smoke the local live service:

```bash
make dev-reload
```

5. Promote the restored state through a reviewed pull request and GitHub Pages
   deployment.
6. Verify the deployed state:

```bash
make pages-smoke
```

### Future Backup Requirements

Future enterprise or non-static services should define:

- retention period for generated registry snapshots;
- offsite backup of package metadata, deterministic archives, accepted source
  manifests, namespace decisions, audit logs, and policy records;
- restore tests that rebuild a historical `/v0` snapshot and compare package
  counts, version counts, package IDs, archive digests, and status payloads;
- recovery-time and recovery-point objectives;
- separate backup policy for private package archives and customer data.

## Flood, DDoS, and Abuse Controls

### Current Public Static Index

The public static index reduces flood and DDoS risk by avoiding request-time
compute:

- registry reads are static files served by GitHub Pages;
- there is no unauthenticated upload endpoint;
- there is no remote mutation API;
- package validation runs in GitHub Actions, not on public read requests;
- package content is never executed;
- exact capability lookup is static metadata lookup, not server-side semantic
  search.

Abuse risk currently concentrates around GitHub Issues and Actions. Current
controls should stay conservative:

- issue forms collect public URLs and acknowledgements, not credentials;
- maintainers review accepted manifest changes;
- workflows use minimal permissions for the task;
- namespace claim automation does not decide ownership;
- decision summary workflows are read-only.

### Future Online APIs

Any future mutable registry, enterprise service, or intent-to-spec API needs a
separate abuse model before production exposure.

Minimum future controls should include:

- authentication and tenant-aware authorization;
- request rate limits and per-tenant quotas;
- CDN or WAF policy for public read-heavy endpoints;
- bounded validation concurrency and queue depth;
- circuit breakers for expensive downstream services;
- explicit LLM token and cost budgets for intent-to-spec endpoints;
- prompt-injection and package-content trust boundaries;
- audit logs for mutation, publish, removal, yanking, restore, and generation
  actions;
- monitoring and alerting for request spikes, failed validations, queue
  backlog, error rates, and cost anomalies.

Intent-to-spec endpoints are especially sensitive because they may involve LLMs,
embedding generation, vector search, or RAG. That functionality belongs in
ContextBuilder, SpecGraph, or a downstream resolver, not in current SpecPM core.

## Operational Boundaries

This runbook does not add:

- `specpm publish`;
- remote registry mutation APIs;
- authenticated enterprise registry implementation;
- package archive download or install behavior;
- package signing or trust-web enforcement;
- online intent-to-spec runtime;
- DDoS enforcement code;
- backup automation;
- restore automation.

Package content remains untrusted data. Package content can describe desired
outputs. Package content cannot command the host.
