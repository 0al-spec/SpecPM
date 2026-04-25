# RFC 0001 Implementation Coverage

Status: Draft
Updated: 2026-04-25
Source: `RFC/SpecGraph-RFC-0001.md`

This document records what the SpecPM MVP implements from RFC 0001 and what is
intentionally left for post-MVP tracks.

## Coverage Summary

| RFC area | MVP status | Notes |
| --- | --- | --- |
| Package layout, manifest, and BoundarySpec loading | Implemented | Directory packages with `specpm.yaml` and referenced BoundarySpecs are supported. |
| Restricted YAML / JSON-compatible data model | Implemented | Anchors, aliases, tags, multiple documents, binary/non-JSON values, and malformed YAML are rejected with structured issues. |
| Manifest required fields | Implemented | `apiVersion`, `kind`, `metadata.*`, `specs`, and `index.provides.capabilities` are validated. |
| Package ID and capability ID syntax | Implemented | RFC-style lowercase IDs are enforced. |
| SemVer validation | Implemented | Package and BoundarySpec versions must be SemVer. |
| BoundarySpec required fields | Implemented | Required identity, intent, scope, capabilities, interfaces, and evidence fields are checked. |
| Manifest capability declaration checks | Implemented | Manifest-provided capabilities must be declared by referenced BoundarySpecs. |
| Evidence, foreign artifacts, and implementation bindings | Implemented as data | Paths are validated as local package data. Missing advisory paths warn; path escapes fail. No foreign format is interpreted. |
| Provenance confidence | Implemented | Validation warns on unknown confidence values; inspect exposes confidence for viewers. |
| Unknown extension fields | Implemented | Unknown non-extension top-level fields fail; `x-` extension fields are preserved as data. |
| Compatibility metadata | Implemented | Compatibility metadata is preserved, indexed, inspected, searched, and diffed. |
| Deterministic pack | Implemented | `.specpm.tgz` archives use stable file ordering, ownership, modes, and timestamps. Package code is never executed. |
| Local registry index | Implemented | File-backed local index stores package identity, digest, capabilities, requirements, license, compatibility, evidence summary, source, and yanked state. |
| Exact capability search | Implemented | Search is exact-match only for normative resolution. Missing local indexes return empty results. |
| Add / local project state | Implemented | `specpm.lock`, `.specpm/index.json`, and `.specpm/packages/.../package.json` are deterministic local metadata. |
| Inspect | Implemented | Package, BoundarySpec, evidence, effects, compatibility, provenance, implementation binding, and contract warning summaries are exposed. |
| Structural diff | Implemented | Diff detects capability, required capability, interface, MUST constraint, package metadata, and compatibility changes with conservative classification. |
| Security handling | Implemented for MVP | Packages are untrusted data; path traversal, symlinks, unsafe archive members, malformed YAML/JSON, and script execution are blocked or avoided. |
| SpecGraph inbox | Implemented as local bridge | `.specgraph_exports/` bundles are listed and inspected without mutating canonical SpecGraph files. This extends the local MVP bridge. |

## Partial Or Deferred Areas

| RFC area | Status | Reason |
| --- | --- | --- |
| `specpm publish` | Post-MVP | Remote registry hosting, immutability enforcement, and governance are outside the local-first MVP. |
| Remote registry API | Post-MVP | The MVP uses a local file-backed index only. |
| Package signing / trust web | Post-MVP | Signing, trust policy, and revocation are explicitly non-goals for the MVP. |
| Full dependency solving | Post-MVP | `add` resolves one exact package or capability at a time. |
| Keyword/fuzzy/semantic search | Post-MVP for normative resolution | Exact capability ID matching is the only normative search path. |
| Full semantic diffing | Post-MVP | MVP diff is structural and conservative. |
| Foreign artifact semantic understanding | Post-MVP | Foreign artifacts are preserved as data and never override validation behavior. |
| Redaction warnings for private data | Post-MVP | Privacy guidance is documented in the RFC, but automated secret/PII detection is not part of the local MVP. |
| Standardized lockfile RFC | Post-MVP | The MVP lockfile is small, deterministic, and local to SpecPM. |

## Verification Links

- CLI exit code contract: `SPECS/CLI_EXIT_CODES.md`
- Viewer JSON contracts: `SPECS/JSON_CONTRACTS.md`
- Golden JSON fixtures: `tests/fixtures/golden/`
- End-to-end and hardening tests: `tests/test_core.py`
- MVP example package: `examples/email_tools/`
- SpecGraph inbox fixture: `tests/fixtures/specgraph_exports/specgraph.core_repository_facade/`
