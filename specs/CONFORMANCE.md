# SpecPM Conformance Artifacts

Status: Draft
Updated: 2026-04-25
Scope: local SpecPM package-manager behavior and post-MVP registry contract payloads

## Purpose

SpecPM conformance artifacts provide a small, portable test corpus for
implementations and downstream SpecGraph tooling. They describe expected
outcomes for package validation, local registry lifecycle behavior, static
remote registry contract payloads, and fixture-backed read-only client behavior
without requiring a remote registry service, package signing, semantic search,
graph reasoning, artifact generation, or agent runtime behavior.

The current suite lives at:

```text
tests/fixtures/conformance/specpm-conformance-v0.json
```

Fixture packages live under:

```text
tests/fixtures/conformance/packages/
```

## Suite Format

The suite file is JSON so non-Python implementations can consume it directly:

```json
{
  "schemaVersion": 1,
  "suite": "specpm-local-conformance-v0",
  "cases": []
}
```

Each case has:

```json
{
  "id": "validate.valid_email_tools",
  "kind": "validate_package",
  "expected": {}
}
```

Paths in the suite are repository-relative. Package content is test data only
and must not be executed.

## Case Kinds

### `validate_package`

Runs package validation against a package directory and checks stable outcome
fields:

- `status`
- `capabilities`
- `error_codes`
- `warning_codes`

### `registry_lifecycle`

Exercises the local file-backed registry lifecycle:

1. index a package;
2. yank the indexed package with a local reason;
3. confirm exact search still returns the package with `yanked: true`;
4. confirm `specpm add` rejects the yanked package;
5. unyank the package;
6. confirm `specpm add` can select it again.

### `remote_registry_payload`

Loads a static JSON fixture for the post-MVP remote registry API contract and
checks stable payload shape fields:

- `apiVersion`
- `schemaVersion`
- `kind`
- `status`
- registry status fields where applicable
- package index counts where applicable
- package identity fields where applicable
- exact capability query fields where applicable
- yanked/deprecated lifecycle state where applicable
- error payload fields where applicable

This case kind does not start a registry server, perform HTTP requests,
download archives, or mutate registry state.

Read-only client tests may reuse these payload fixtures behind HTTP fetch stubs.
Those tests verify endpoint construction, response shape validation, and stable
client reports without requiring a live registry service.

## Current Coverage

The initial conformance suite covers:

- a valid package;
- a missing manifest;
- a missing referenced BoundarySpec;
- a spec path escape;
- a warning-only manual-assertion evidence package;
- local registry yank and unyank behavior.
- remote registry status, package index, package metadata, package version,
  exact capability search, yanked version, and not-found error payloads.
- read-only remote registry client behavior using fixture-backed fetch stubs.

## Non-Goals

Conformance artifacts do not define:

- `specpm publish`;
- remote registry service implementation;
- live remote registry availability;
- remote archive download, install, or cache behavior;
- package signing or trust policy;
- namespace governance;
- semantic search;
- full dependency solving;
- SpecGraph canonical graph reasoning;
- ContextBuilder artifact generation or artifact eval runtime.
