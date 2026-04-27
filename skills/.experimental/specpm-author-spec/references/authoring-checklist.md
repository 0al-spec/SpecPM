# SpecPM Authoring Checklist

## Minimal Layout

```text
specpm.yaml
specs/<package-or-boundary>.spec.yaml
evidence/      optional
foreign/       optional
```

Use the repository's existing layout if present. Prefer lowercase `specs/` for
new work to avoid case-sensitive filesystem surprises.

## `specpm.yaml` Skeleton

```yaml
apiVersion: specpm.dev/v0.1
kind: SpecPackage
metadata:
  id: example.package
  name: Example Package
  version: 0.1.0
  summary: Short package summary.
  license: MIT
  authors:
    - name: Example Team
specs:
  - path: specs/example.package.spec.yaml
index:
  provides:
    capabilities:
      - example.capability
  requires:
    capabilities: []
compatibility:
  platforms:
    - any
  languages:
    - python
keywords:
  - example
foreignArtifacts: []
```

## `BoundarySpec` Skeleton

```yaml
apiVersion: specpm.dev/v0.1
kind: BoundarySpec
metadata:
  id: example.package
  title: Example Package Boundary
  version: 0.1.0
  status: draft
  authors:
    - name: Example Team
intent:
  summary: What reusable intent this package carries.
scope:
  boundedContext: example
  includes:
    - Specific in-scope behavior.
  excludes:
    - Specific out-of-scope behavior.
provides:
  capabilities:
    - id: example.capability
      role: primary
      summary: What this capability enables.
requires:
  capabilities: []
interfaces:
  inbound: []
  outbound: []
constraints: []
effects: []
evidence: []
provenance:
  confidence: medium
  notes:
    - Authored from repository docs and public API surface.
implementationBindings: []
```

## Evidence Guidance

Prefer evidence that a reviewer can inspect:

- CLI help, command docs, or tests for command surfaces.
- Public API files for importable functions/classes.
- Workflows for CI/deployment contracts.
- Examples and fixtures for package behavior.
- PRD/Workplan/RFC documents for intentional boundaries.

Avoid unsupported claims such as "production-ready", "secure", or "complete"
unless the repository evidence directly supports them.

## Capability IDs

Use lowercase dotted IDs:

```text
domain.area.action
specpm.package.validate
specpm.registry.public_static_index
```

Keep IDs stable, specific, and reviewable. Do not use natural-language
sentences as IDs.

## Validation Commands

```bash
PYTHONPATH=src python3 -m specpm.cli validate . --json
specpm validate <package-dir> --json
```
