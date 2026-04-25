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

## Boundary

The remote registry API contract defines read-only discovery surfaces:

- package metadata lookup;
- package version lookup;
- exact capability search;
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

## Read-Only Client Surface

SpecPM may provide explicit read-only client commands for this contract:

```bash
specpm remote package <package-id> --registry <url> [--json]
specpm remote version <package-id@version> --registry <url> [--json]
specpm remote search <capability-id> --registry <url> [--json]
```

These commands fetch metadata only. They do not download package archives,
install packages, mutate local project state, publish packages, authenticate,
sign packages, execute package content, or perform remote yanking workflows.

Remote client commands MUST validate package IDs, package refs, capability IDs,
registry URLs, timeouts, and response payload shape before returning a
successful machine-readable report.

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

## Endpoints

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

## Common Types

### Package Identity

```text
PackageIdentity = {
  package_id: string,
  name: string,
  version?: string
}
```

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
- `invalid_package_id`
- `invalid_package_version`
- `invalid_capability_id`

## Conformance Fixtures

Static conformance fixtures live under:

```text
tests/fixtures/conformance/remote_registry/
```

The suite manifest references those fixtures with `remote_registry_payload`
cases. These cases validate JSON shape only. They do not start a server, perform
HTTP requests, download package archives, or mutate registry state. Client tests
may use fixture-backed HTTP fetch stubs so the repository test suite does not
require a live registry service.

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
