# SpecPM Conformance Artifacts

Status: Draft
Updated: 2026-05-02
Scope: local SpecPM package-manager behavior and post-MVP registry contract payloads

## Purpose

SpecPM conformance artifacts provide a small, portable test corpus for
implementations and downstream SpecGraph tooling. They describe expected
outcomes for package validation, local registry lifecycle behavior, static
remote registry contract payloads, generated public static index endpoints,
enterprise registry compatibility payloads, and fixture-backed read-only client
behavior without requiring a remote registry service, package signing, semantic
search, semantic intent inference, graph reasoning, artifact generation, or
agent runtime behavior.

The current suite lives at:

```text
tests/fixtures/conformance/specpm-conformance-v0.json
```

The fixture manifest for downstream consumers lives at:

```text
tests/fixtures/conformance/fixture-manifest.json
```

Fixture packages live under:

```text
tests/fixtures/conformance/packages/
```

Remote registry and enterprise registry payload fixtures live under:

```text
tests/fixtures/conformance/remote_registry/
tests/fixtures/conformance/enterprise_registry/
```

## Suite Format

The suite file is JSON so non-Python implementations can consume it directly:

```json
{
  "schemaVersion": 1,
  "suite": "specpm-conformance-v0",
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

## Fixture Manifest

`fixture-manifest.json` is metadata for downstream consumers that need a stable
subset of conformance payloads, such as fixture-backed HTTP/static registry
smoke tests. It declares the fixture suite, SpecPM package version, registry API
version, named fixture sets, and the repository-relative fixture paths with
their expected payload `kind`, `valid` marker, usage, and optional
`staticPath`.

Fixture sets are grouped by intended use. `remote_registry_static_smoke` and
`enterprise_registry_static_smoke` contain positive payloads that can be copied
into a downstream static `/v0` tree at their declared `staticPath` values.
Lifecycle, error, and negative validation fixtures are kept in separate sets so
downstream HTTP/static smoke tests do not accidentally publish invalid or error
payloads as live endpoints.

The manifest is not a lock file and is not a root of trust. Downstream
consumers must pin the SpecPM repository revision outside the manifest, ideally
by checking out an exact 40-character commit SHA. A human-readable tag may be
logged or checked for consistency, but the trusted input is the externally
pinned commit.

Recommended downstream flow:

1. check out SpecPM at the consumer-owned pinned commit revision;
2. assert `git rev-parse HEAD` equals that expected revision;
3. read `tests/fixtures/conformance/fixture-manifest.json`;
4. copy only fixtures from a positive static smoke set to their declared
   `staticPath` values;
5. run fixture-backed client or HTTP/static smoke checks.

This keeps downstream contract tests independent from mutable public index
sources, remote package source freshness, and full `public-index` supply-chain
validation.

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
- exact capability and intent query fields where applicable
- yanked/deprecated lifecycle state where applicable
- error payload fields where applicable

This case kind may also carry negative shape fixtures where
`expected.validation_status` is `invalid` and `expected.validation_error_codes`
lists expected validator error codes.

This case kind does not start a registry server, perform HTTP requests,
download archives, or mutate registry state.

### `public_registry_static_index`

Generates a static public `/v0` registry tree from repository-relative package
fixtures and checks endpoint payload shape:

1. generate the public index with `specpm public-index generate` behavior;
2. assert required JSON endpoints exist;
3. assert adjacent `index.html` files carry the same JSON bodies for static
   hosts;
4. validate generated payloads against the remote registry API contract;
5. check archive digest and size metadata against the generated archive;
6. assert missing package/capability paths are not fabricated as package data.

This case kind does not start a server, publish packages, mutate remote state,
download remote archives as a client, or execute package content.

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
- a warning-only strict authoring quality package for dangling evidence
  support targets, ambiguous IDs, and weak `unknown` kinds;
- local registry yank and unyank behavior.
- remote registry status, package index, package metadata, package version,
  exact capability search, observed intent catalog metadata, exact intent
  search, yanked version, deprecated version, not-found error, and
  invalid-shape payloads.
- read-only remote registry client behavior using fixture-backed fetch stubs.
- generated public static `/v0` endpoint shape, adjacent static-host HTML
  payloads, archive digest metadata, and absent missing package/capability
  paths.
- enterprise registry status payload compatibility for implementations that
  reuse the same read-only metadata contract behind private policy controls.

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
