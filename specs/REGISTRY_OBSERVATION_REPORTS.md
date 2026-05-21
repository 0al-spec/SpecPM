# Registry Observation Reports

Status: Public alpha operator workflow.
Updated: 2026-05-21
Scope: Reusable read-only observation artifacts for the public `/v0` registry

## Purpose

Registry observation reports are machine-readable evidence files that operators
and downstream tools can attach to pull requests, issues, or release notes when
checking public registry behavior.

They are generated from read-only `specpm remote observe` metadata calls. They
do not download package archives, install packages, mutate local state, publish
packages, execute package content, authenticate, sign packages, or decide
SpecGraph graph state.

## Standard Targets

Use the local Docker-backed registry when validating a branch before merge:

```bash
make dev-reload
make public-index-observation-report
```

Use GitHub Pages after deployment or when validating the currently published
static registry:

```bash
make pages-observation-report
```

Generate both reports when the local registry is running and the public Pages
deployment should be compared:

```bash
make registry-observation-reports
```

The legacy alpha report targets remain available:

```bash
make public-alpha-report
make pages-alpha-report
```

Those write the historical alpha filenames. The reusable targets below write
review-oriented filenames under one directory.

## File Locations

Default outputs:

| Surface | Target | Output |
| --- | --- | --- |
| Local Docker public index | `make public-index-observation-report` | `.specpm/registry-observations/local-public-index-observation.json` |
| GitHub Pages public index | `make pages-observation-report` | `.specpm/registry-observations/pages-public-index-observation.json` |
| Both surfaces | `make registry-observation-reports` | both files above |
| Legacy local alpha | `make public-alpha-report` | `.specpm/public-alpha-observation.json` |
| Legacy Pages alpha | `make pages-alpha-report` | `.specpm/pages-alpha-observation.json` |

`.specpm/` is ignored by Git. Attach reports to reviews or issues when they are
needed as evidence; do not commit routine report output.

For long-lived release evidence, copy reports into an external release artifact
store or attach them to the release issue with a stable name:

```text
<YYYYMMDDTHHMMSSZ>-<surface>-public-index-observation-<short-revision>.json
```

Example:

```text
20260521T170300Z-pages-public-index-observation-9aeb9409e0e8.json
```

## Covered Examples

The default report arguments check:

- `specpm.core` package visibility;
- `specnode.core` package visibility;
- retained `specpm.core@0.1.0`;
- current `specpm.core@0.2.0`;
- `specnode.core@0.1.0`;
- `specpm.registry.public_alpha_index` exact capability lookup;
- `specnode.typed_job_protocol` exact capability lookup;
- `intent.registry.intent_lookup` exact observed intent lookup;
- `intent.document_conversion.email_to_markdown` exact observed intent lookup.

The report target is intentionally small enough for review comments and broad
enough to cover package, version, capability, and intent visibility.

## Comparison Workflow

1. Start or refresh the local public index:

   ```bash
   make dev-reload
   ```

2. Capture local evidence:

   ```bash
   make public-index-observation-report
   ```

3. Capture deployed Pages evidence:

   ```bash
   make pages-observation-report
   ```

4. Compare stable fields first:

   ```bash
   diff -u \
     .specpm/registry-observations/local-public-index-observation.json \
     .specpm/registry-observations/pages-public-index-observation.json
   ```

Expected differences usually include `registry`, endpoint URLs, build number,
and build revision. Unexpected differences include failed checks, missing
packages, missing versions, missing capabilities, missing intents, package
count changes, version count changes, or lifecycle state drift.

When a report is attached to a downstream review, cite:

- report filename;
- registry base URL;
- `summary.registry_status`;
- `summary.package_count`;
- `summary.version_count`;
- `summary.capability_count`;
- `summary.intent_count`;
- failed check IDs, if any.

## Boundary

Observation reports are downstream evidence. They do not replace the canonical
remote registry contract in `specs/REMOTE_REGISTRY_API.md` and they do not give
SpecPM authority over SpecGraph graph reasoning. For SpecGraph-specific finding
vocabulary, see `specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md`.
