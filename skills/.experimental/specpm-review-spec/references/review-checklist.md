# SpecPM Review Checklist

## Manifest Checks

- `apiVersion` and `kind` are correct.
- `metadata.id` is stable and valid.
- `metadata.version` is SemVer.
- `metadata.license` is present and matches repository license.
- `metadata.authors` reflects actual authorship requested by maintainers.
- Every `specs[].path` exists and stays inside package root.
- Every `index.provides.capabilities[]` is declared by a referenced
  BoundarySpec.
- No unknown non-extension top-level fields are introduced accidentally.

## BoundarySpec Checks

- `metadata.id` and version are stable.
- `intent.summary` is concrete.
- `scope.includes` avoids marketing language and maps to actual package
  behavior or accepted intent.
- `scope.excludes` protects adjacent systems and deferred tracks.
- `provides.capabilities[].id` is precise and valid.
- `requires.capabilities` is not used as a vague dependency bucket.
- `interfaces` describe real CLI/API/file/HTTP contracts when available.
- `constraints` use MUST/SHOULD language only where intended.
- `effects` identify filesystem/network/security-sensitive behavior when
  relevant.
- `evidence[].path` points to files that exist or is intentionally documented
  as external evidence.
- `implementationBindings` point to real owned/border files.

## Boundary Red Flags

- SpecPM spec claims PRD generation in core.
- Package content is described as trusted instructions.
- SpecPM is made responsible for graph reasoning or ContextBuilder generation.
- A future profile field is treated as a stable MVP JSON contract.
- Public index workflows imply remote mutation, publish, auth, package install,
  or package execution.
- Namespace claims imply machine-enforced ownership.

## Validation Checklist

Run at least:

```bash
PYTHONPATH=src python3 -m specpm.cli validate . --json
```

For SpecPM repository changes, also prefer:

```bash
pytest tests/test_core.py -q -k "spec or workflow or issue_template"
git diff --check
```

Use broader tests when behavior, schemas, workflows, or generated docs changed.
