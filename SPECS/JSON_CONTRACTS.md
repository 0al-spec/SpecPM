# SpecPM JSON Contracts

Status: Draft
Updated: 2026-04-24
Scope: MVP viewer-facing JSON outputs

## Stability Rules

SpecPM JSON output is intended for ContextBuilder and other viewers. Consumers
should treat these contracts as stable for the MVP:

- existing top-level fields should not be renamed or removed without a
  Workplan update;
- status vocabularies are closed unless this document is updated;
- new optional fields may be added when they are additive;
- arrays are emitted in deterministic order where ordering affects rendering;
- paths are data only and must not be executed or fetched automatically;
- validation warnings and inspection `contract_warnings` are separate surfaces.

Golden fixtures live under `tests/fixtures/golden/` and cover representative
payloads for these contracts.

## Common Types

### Issue

```text
Issue = {
  severity: "error" | "warning",
  code: string,
  message: string,
  file?: string,
  field?: string
}
```

### PackageIdentity

```text
PackageIdentity = {
  package_id?: string,
  name?: string,
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

## Status Vocabularies

- Validation status: `valid`, `warning_only`, `invalid`.
- Pack status: `packed`, `invalid`.
- Index status: `indexed`, `unchanged`, `invalid`.
- Search status: `ok`, `invalid`.
- Add status: `added`, `unchanged`, `ambiguous`, `invalid`.
- Inbox bundle status: `draft_visible`, `ready_for_review`, `invalid`,
  `blocked`.
- Diff status: `ok`, `invalid`.
- Diff classification: `unchanged`, `non_breaking`, `review_required`,
  `breaking`, `invalid`.
- Source kind: `directory`, `archive`.
- Archive format: `specpm-tar-gzip-v0`.

## Validation Report

Command:

```bash
specpm validate <package-dir> --json
```

Contract:

```text
ValidationReport = {
  status: ValidationStatus,
  error_count: number,
  warning_count: number,
  errors: Issue[],
  warnings: Issue[],
  package_identity: PackageIdentity | null,
  capabilities: string[],
  checked_files: string[]
}
```

Golden fixture: `tests/fixtures/golden/validate-email-tools.json`.

## Inspection Report

Command:

```bash
specpm inspect <package-dir> --json
```

Contract:

```text
InspectionReport = {
  package: {
    identity: PackageIdentity | null,
    name?: string,
    summary?: string,
    license?: string,
    capabilities: string[],
    required_capabilities: string[],
    compatibility: object,
    preview_only: boolean,
    keywords: string[]
  },
  boundary_specs: BoundarySpecSummary[],
  contract_warnings: Issue[],
  validation: ValidationReport
}

BoundarySpecSummary = {
  path: string,
  id?: string,
  title?: string,
  version?: string,
  status?: string,
  intent_summary?: string,
  scope: object,
  bounded_context?: string,
  provides: string[],
  requires: string[],
  interfaces: object,
  effects: object,
  constraints: object[],
  evidence: object[],
  foreign_artifacts: object[],
  implementation_bindings: object[],
  compatibility: object,
  keywords: string[],
  provenance: object,
  provenance_confidence: object
}
```

`contract_warnings` are advisory review hints. They do not change validation
status and are intended for viewer emphasis, for example security-sensitive
effects or capabilities.

Golden fixture: `tests/fixtures/golden/inspect-email-tools.json`.

## Pack Result

Command:

```bash
specpm pack <package-dir> -o <archive> --json
```

Contract:

```text
PackResult = {
  status: "packed" | "invalid",
  archive: string | null,
  digest: Digest | null,
  format: "specpm-tar-gzip-v0",
  included_files: string[],
  archive_size?: number,
  validation: ValidationReport,
  errors: Issue[]
}
```

Golden fixture: `tests/fixtures/golden/pack-email-tools.json`.

## Search Result

Command:

```bash
specpm search <capability-id> --index <path> --json
```

Contract:

```text
SearchReport = {
  status: "ok" | "invalid",
  index: string,
  query: { capability_id: string },
  result_count: number,
  results: SearchResult[],
  errors: Issue[]
}

SearchResult = {
  package_id: string,
  version: string,
  name?: string,
  summary?: string,
  license?: string,
  matched_capability: string,
  provided_capabilities: string[],
  required_capabilities: string[],
  compatibility: object,
  confidence_summary: {
    validation_status?: ValidationStatus,
    evidence: object
  },
  source: {
    kind: "directory" | "archive",
    path: string,
    digest: Digest
  },
  yanked: boolean
}
```

Golden fixture: `tests/fixtures/golden/search-email-tools.json`.

## Add Result

Command:

```bash
specpm add <capability-id-or-package-ref> --index <path> --project <dir> --json
```

Contract:

```text
AddReport = {
  status: "added" | "unchanged" | "ambiguous" | "invalid",
  target: string,
  resolved_by: "capability" | "package_ref" | "path",
  index: string,
  project: string,
  package: object | null,
  candidates: SearchResult[],
  lockfile?: string,
  cache_entry?: string,
  index_report?: object,
  errors: Issue[]
}
```

Golden fixture: `tests/fixtures/golden/add-email-tools.json`.

## Inbox List

Command:

```bash
specpm inbox list --root .specgraph_exports --json
```

Contract:

```text
InboxListReport = {
  root: string,
  bundle_count: number,
  bundles: InboxBundleReport[]
}

InboxBundleReport = {
  found: boolean,
  package_id: string,
  path: string,
  layout: object,
  inbox_status: InboxBundleStatus,
  validation_status: ValidationStatus,
  package_identity: PackageIdentity | null,
  handoff_summary: object | null,
  handoff: object | null,
  gaps: Issue[]
}
```

Golden fixture: `tests/fixtures/golden/inbox-list-specgraph.json`.

## Inbox Inspect

Command:

```bash
specpm inbox inspect <package-id> --root .specgraph_exports --json
```

Contract:

```text
InboxInspectReport = InboxBundleReport & {
  inspection?: InspectionReport
}
```

SpecGraph continuity fields remain under `handoff`, `handoff_summary`, and
`inbox_status`. Core package validation and plain `inspect` output do not import
SpecGraph-specific lifecycle fields.

Golden fixture: `tests/fixtures/golden/inbox-inspect-specgraph.json`.

## Diff Result

Command:

```bash
specpm diff <old-package-dir> <new-package-dir> --json
```

Contract:

```text
DiffReport = {
  status: "ok" | "invalid",
  classification: DiffClassification,
  has_changes?: boolean,
  old_package: string,
  new_package: string,
  old_identity: PackageIdentity | null,
  new_identity: PackageIdentity | null,
  changes: {
    capabilities: { removed: string[], added: string[] },
    required_capabilities: { removed: string[], added: string[] },
    interfaces: { removed: object[], added: object[], changed: object[] },
    must_constraints: { removed: object[], added: object[], changed: object[] },
    package_metadata: { changed: object[] },
    compatibility: { changed: boolean, old: object, new: object }
  },
  impact: {
    breaking: object[],
    review_required: object[],
    non_breaking: object[]
  },
  errors: Issue[]
}
```

Golden fixture: `tests/fixtures/golden/diff-email-tools-unchanged.json`.

## Viewer Examples

### Package Card

A compact package card should prefer:

```text
title = inspection.package.identity.name
subtitle = inspection.package.identity.package_id + "@" + version
summary = inspection.package.summary
badges = [
  inspection.validation.status,
  inspection.package.license,
  first boundary_specs[].status
]
primary_capabilities = inspection.package.capabilities
warnings = inspection.validation.warnings + inspection.contract_warnings
```

Evidence state can be summarized from each `boundary_specs[].evidence` item by
counting evidence entries and highlighting missing-path validation warnings.

### Capability Search Result

A capability search table should prefer:

```text
matched = result.matched_capability
package = result.package_id + "@" + result.version
summary = result.summary
license = result.license
confidence = result.confidence_summary.validation_status
evidence_count = result.confidence_summary.evidence.total
source_kind = result.source.kind
yanked = result.yanked
```

Search is exact-match only in the MVP. Viewers may add filters or sorting, but
must not treat fuzzy or semantic matches as normative resolution.
