# SpecPM Remote Registry API Contract

Status: Draft
Updated: 2026-04-25
Scope: post-MVP read-only registry contract

## Purpose

This document defines the first remote registry API contract for SpecPM.

The contract started docs/conformance-first. It describes stable JSON payloads
and static conformance fixtures before SpecPM implements a remote server,
`specpm publish`, authentication, signing, namespace governance, or remote
yanking workflows.

SpecPM remains local-first for the MVP. The remote registry API is a post-MVP
contract that downstream services and SpecPM read-only metadata clients can
implement.

The contract supports more than one deployment model. A public SpecPM Index may
serve generated static registry JSON through GitHub Pages after validating
community submissions through GitHub Issues and Actions. An enterprise remote
registry may implement the same read-only metadata surfaces behind private
auth, internal policy, audit, and private storage.

## Boundary

The remote registry API contract defines read-only discovery surfaces:

- registry status lookup;
- package index lookup;
- package metadata lookup;
- package version lookup;
- exact capability search;
- observed intent catalog lookup;
- exact intent search over explicitly declared `intentIds`;
- yanked and deprecated package version state;
- stable error payloads.

The contract does not define:

- remote registry server implementation;
- `specpm publish`;
- package upload flows;
- remote package yanking mutation flows;
- authentication or authorization;
- package signing, trust policy, revocation, or transparency logs;
- namespace governance;
- semantic search;
- dependency solving;
- package content execution.

Package content remains untrusted data. A registry may describe packages and
desired downstream outputs, but package content cannot command the host.

## Deployment Models

### Public Static Index

A public community index can be implemented without a custom registry server:

```text
GitHub Issue submission
        |
        v
GitHub Actions validation
        |
        v
Generated /v0 JSON
        |
        v
GitHub Pages static registry
```

This model is optimized for public packages, reviewable submissions, simple
operations, and compatibility with `specpm remote` metadata commands.
`specpm public-index generate` can produce the first static `/v0` tree from
already-local accepted package directories. It writes both `index.json` files
for review and JSON-body `index.html` files for static hosts that need directory
index files to serve extensionless endpoints.

The public static index should not define enterprise auth, private package
visibility, remote mutation APIs, or package archive install/cache behavior.

### Enterprise Registry

An enterprise registry can implement the same read-only API contract while
adding private operational controls:

- authentication and authorization;
- private package visibility;
- internal namespace ownership;
- audit logs;
- retention policy;
- private blob storage;
- signing and trust policy;
- approval workflows;
- integration with internal Git hosting and CI.

Enterprise registry behavior is useful for private deployments, but it should
remain a separate track from the public GitHub-backed index flow.

## Read-Only Client Surface

SpecPM may provide explicit read-only client commands for this contract:

```bash
specpm remote status --registry <url> [--json]
specpm remote packages --registry <url> [--json]
specpm remote package <package-id> --registry <url> [--json]
specpm remote version <package-id@version> --registry <url> [--json]
specpm remote search <capability-id> --registry <url> [--json]
specpm remote intents --registry <url> [--json]
specpm remote intent <intent-id> --registry <url> [--json]
specpm remote search-intent <intent-id> --registry <url> [--json]
```

These commands fetch metadata only. They do not download package archives,
install packages, mutate local project state, publish packages, authenticate,
sign packages, execute package content, or perform remote yanking workflows.

Remote client commands MUST validate package IDs, package refs, capability IDs,
registry URLs, timeouts, and response payload shape before returning a
successful machine-readable report.

Remote client commands MUST also validate response target consistency before
returning success:

- package metadata responses must match the requested `package_id`;
- package version responses must match the requested `package_id` and
  `version`;
- exact capability search responses must echo the requested `capability_id` and
  each result `matched_capability` must equal that capability ID.
- observed intent metadata responses must echo the requested `intent_id`.
- exact intent search responses must echo the requested `intent_id` and each
  result `matched_intent` must equal that intent ID.

## Transport

The initial transport model is HTTPS with JSON payloads.

Clients SHOULD send:

```text
Accept: application/json
```

Servers SHOULD return:

```text
Content-Type: application/json
```

All responses use UTF-8 encoded JSON objects. Arrays are emitted in
deterministic order where ordering affects client rendering or resolution.

## API Versioning

All payloads include:

```text
apiVersion: "specpm.registry/v0"
schemaVersion: 1
kind: string
```

`apiVersion` identifies the registry API family. `schemaVersion` identifies the
JSON payload shape within this draft family.

The public GitHub Pages deployment also publishes a static browser viewer for
these endpoints at `https://0al-spec.github.io/SpecPM/viewer/`. The viewer is
read-only and fetches the same generated JSON files; it is not a backend,
resolver, or publishing API.

## Endpoints

### Registry Root

```text
GET /v0
```

Returns the static registry entrypoint with registry summary counts and links to
the primary JSON metadata endpoints. This exists so browsers, documentation,
and downstream tools can open the `/v0` namespace directly instead of guessing
the first endpoint.

Response kind:

```text
RemoteRegistryRoot
```

### Registry Status

```text
GET /v0/status
```

Returns read-only registry discovery metadata for downstream observers such as
SpecGraph and ContextBuilder. This endpoint is for availability and capability
surface observation only; it is not a health check for package execution.

Response kind:

```text
RemoteRegistryStatus
```

### Package Index

```text
GET /v0/packages
```

Returns the deterministic package summary index visible through the registry.
This endpoint lets downstream observers discover which package IDs and versions
are currently exposed without guessing capability IDs first.

Response kind:

```text
RemotePackageIndex
```

### Package Metadata

```text
GET /v0/packages/{package_id}
```

Returns package-level metadata and available versions.

Response kind:

```text
RemotePackage
```

### Package Version

```text
GET /v0/packages/{package_id}/versions/{version}
```

Returns one package version entry, including capabilities, requirements, source
digest, lifecycle state, and download metadata.

Response kind:

```text
RemotePackageVersion
```

### Exact Capability Search

```text
GET /v0/capabilities/{capability_id}/packages
```

Returns package versions that provide the exact capability ID. This endpoint is
exact-match only. Fuzzy, keyword, and semantic search remain post-MVP and are
not part of normative resolution.

Response kind:

```text
RemoteCapabilitySearch
```

### Observed Intent Catalog

```text
GET /v0/intents
```

Returns the deterministic catalog of `intent.*` IDs observed in accepted
packages. The catalog is built from package metadata and BoundarySpec-backed
capability `intentIds`.

This endpoint is an authoring and discovery aid. It is not a canonical intent
dictionary, namespace governance decision, semantic authority, or package
selection mechanism.

Response kind:

```text
RemoteIntentIndex
```

### Observed Intent Metadata

```text
GET /v0/intents/{intent_id}
```

Returns observed metadata for one exact `intent.*` ID, including package IDs and
capabilities that declared the mapping.

Response kind:

```text
RemoteIntent
```

### Exact Intent Search

```text
GET /v0/intents/{intent_id}/packages
```

Returns package versions whose BoundarySpecs explicitly map at least one
provided capability to the exact canonical `intent.*` ID. This endpoint is
exact-match metadata lookup. It does not infer intent from package text, run
LLM extraction, use embeddings, perform vector search, or select packages
automatically.

Response kind:

```text
RemoteIntentSearch
```

## Common Types

### Package Identity

```text
PackageIdentity = {
  package_id: string,
  name: string,
  version?: string
}
```

### Registry Status

```text
RegistryStatus = {
  profile: "public_static_index" | "enterprise_registry" | string,
  api_version: "v0",
  read_only: boolean,
  authority: string,
  package_count: integer,
  version_count: integer,
  capability_count: integer,
  intent_count?: integer
}
```

For the local static public index, `authority` is `metadata_only`. It means the
registry can describe visible packages, but it cannot command the host and does
not imply artifact execution authority.

### Package Summary

```text
PackageSummary = {
  package_id: string,
  name: string,
  summary?: string,
  license?: string,
  latest_version?: string,
  capabilities: string[],
  intents?: string[],
  keywords?: string[],
  versions: {
    version: string,
    yanked: boolean,
    deprecated: boolean
  }[]
}
```

### Observed Intent Catalog

```text
ObservedIntentCatalog = {
  authority: "observed_metadata_only",
  canonical: false,
  description: string
}

ObservedIntentSummary = {
  intent_id: string,
  status: "observed",
  canonical: false,
  package_count: integer,
  version_count: integer,
  capability_count: integer,
  package_ids: string[],
  capabilities: string[]
}

RemoteIntentIndex = {
  apiVersion: "specpm.registry/v0",
  schemaVersion: 1,
  kind: "RemoteIntentIndex",
  status: "ok",
  catalog: ObservedIntentCatalog,
  intent_count: integer,
  intents: ObservedIntentSummary[]
}

RemoteIntent = {
  apiVersion: "specpm.registry/v0",
  schemaVersion: 1,
  kind: "RemoteIntent",
  status: "ok",
  catalog: ObservedIntentCatalog,
  intent: ObservedIntentSummary,
  packages: {
    package_id: string,
    version: string,
    name?: string,
    summary?: string,
    matched_capabilities: string[],
    provided_intents?: string[],
    provided_capabilities: string[],
    required_capabilities: string[],
    license?: string,
    yanked: boolean,
    deprecated: boolean
  }[]
}
```

Observed intent status means the ID appeared in accepted package metadata. It
does not make the ID canonical. Canonical meaning and lifecycle decisions remain
outside SpecPM's package-manager contract.

### Digest

```text
Digest = {
  algorithm: "sha256",
  value: string
}
```

### Version State

```text
VersionState = {
  yanked: boolean,
  yank_reason?: string,
  deprecated: boolean,
  deprecation_message?: string
}
```

Yanked versions remain visible for exact lookup and auditability. Future clients
MUST NOT select yanked versions by default unless an explicit override exists.

### Source

```text
Source = {
  kind: "archive",
  format: "specpm-tar-gzip-v0",
  digest: Digest,
  size: integer,
  url: string
}
```

`url` is package data. Downloading it is future client behavior and is outside
the current MVP implementation.

`size` is the archive size in bytes.

## Status Vocabularies

Remote registry payload status values are closed for this draft:

- `ok`
- `not_found`
- `invalid`

Version lifecycle booleans are explicit:

- `yanked`
- `deprecated`

## Error Payload

All non-success responses SHOULD use:

```text
RemoteRegistryError = {
  apiVersion: "specpm.registry/v0",
  schemaVersion: 1,
  kind: "RemoteRegistryError",
  status: "not_found" | "invalid",
  error: {
    code: string,
    message: string,
    target?: string
  }
}
```

Initial error codes:

- `package_not_found`
- `package_version_not_found`
- `capability_not_found`
- `intent_not_found`
- `invalid_package_id`
- `invalid_package_version`
- `invalid_capability_id`
- `invalid_intent_id`

## Conformance Fixtures

Static conformance fixtures live under:

```text
tests/fixtures/conformance/remote_registry/
tests/fixtures/conformance/enterprise_registry/
```

The suite manifest references those fixtures with `remote_registry_payload`
cases. These cases validate JSON shape only, including positive fixtures,
negative invalid-shape fixtures, and enterprise registry compatibility payloads
that reuse the same read-only metadata contract. They do not start a server,
perform HTTP requests, download package archives, or mutate registry state.
Client tests may use fixture-backed HTTP fetch stubs so the repository test
suite does not require a live registry service.

The initial fixture set covers registry status, package index, package
metadata, package version metadata, exact capability search, observed intent
catalog metadata, exact intent search, yanked version visibility, deprecated
version visibility, invalid count detection, not-found errors, and enterprise
registry status shape.

The suite also includes `public_registry_static_index` cases that generate a
static public `/v0` tree and verify the same endpoint payloads produced by
`specpm public-index generate`. Those cases validate generated JSON and
adjacent `index.html` payload bodies, but they still do not start a live
registry server or perform remote registry mutation.

## Security Considerations

Remote registry JSON is untrusted data.

Clients and downstream tools must not execute package content, package-provided
prompts, generation instructions, foreign artifacts, or downloaded archives as a
side effect of reading registry metadata.

The API contract intentionally omits signing and trust policy. Future signing
work must be introduced as a separate post-MVP track.

## Future Work

Future work may define:

- remote registry service behavior;
- `specpm publish`;
- upload and immutability rules;
- remote yanking governance;
- namespace ownership and dispute processes;
- authentication and authorization;
- package signing and transparency logs;
- client-side download and cache behavior;
- expanded conformance suites for real HTTP implementations.
