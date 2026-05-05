# 0003 SpecPM API Versioning Decision

Status: Accepted for documentation. Deferred for runtime expansion.

## Decision

SpecPM has multiple versioned surfaces. They must be treated separately:

- package document schema: `apiVersion: specpm.dev/v0.1`;
- remote/static registry metadata API: `apiVersion: specpm.registry/v0`;
- public registry URL prefix: `/v0`;
- package archive format: `specpm-tar-gzip-v0`;
- local lock/index schema versions;
- CLI and Python JSON report contracts documented in `specs/JSON_CONTRACTS.md`;
- conformance suite names such as `specpm-conformance-v0`.

The package document schema version and the registry API version are not the
same contract. A package can use `specpm.dev/v0.1` while being served through
the `/v0` registry API.

## Versioning Rules

### Package Document Schema

`specpm.dev/v0.1` covers `specpm.yaml` and `BoundarySpec` document shape.

Compatible changes may add optional fields only after documentation and
validation behavior are explicit.

Breaking package document changes require a new package schema API version, for
example `specpm.dev/v0.2` or `specpm.dev/v1`.

### Registry API

`specpm.registry/v0` covers read-only registry metadata payloads and the public
`/v0` endpoint family.

The `/v0` family should remain backward-compatible during public alpha. Breaking
endpoint or payload changes require a new endpoint family such as `/v1`.

Each registry payload also includes `schemaVersion`. That value identifies the
machine-readable payload shape inside the registry API family. It should change
when consumers need to distinguish a new shape, even if the endpoint family
remains `/v0`.

### CLI and Python JSON Reports

CLI and Python JSON reports are viewer-facing contracts. Their stability rules
are documented in `specs/JSON_CONTRACTS.md`.

Existing top-level fields should not be renamed or removed without an explicit
Workplan entry, fixture update, and migration note. Additive optional fields
are allowed when tests and documentation are updated.

### Archive Format

`specpm-tar-gzip-v0` is an archive format contract. It should not be reused for
a different archive layout, timestamp policy, compression policy, or included
file selection rule.

## Non-Goals

This decision does not implement:

- multi-version package schema loading;
- `/v1` registry endpoints;
- content negotiation;
- remote registry mutation APIs;
- package migration tooling;
- deprecation automation.

## Consequences

SpecPM can evolve package documents, registry metadata, archives, and CLI JSON
reports without conflating those surfaces.

Downstream consumers such as SpecGraph, ContextBuilder, SpecNode, and the public
registry viewer can reason about compatibility from the exact surface they
consume.
