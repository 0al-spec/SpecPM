# CLI Reference

SpecPM exposes a local-first package-manager CLI.

## Validation and Inspection

```bash
specpm validate <package-dir> [--json]
specpm inspect <package-dir> [--json]
```

`validate` checks package structure, manifest fields, referenced specs,
capability declarations, supported YAML shape, and local path safety.

`inspect` exposes package identity, BoundarySpec summaries, evidence,
capabilities, compatibility metadata, provenance, effects, and contract
warnings.

## Packing

```bash
specpm pack <package-dir> [-o <archive>] [--json]
```

`pack` validates the package first and emits a deterministic
`specpm-tar-gzip-v0` archive. Package code is never executed.

## Local Registry

```bash
specpm index <package-dir-or-archive> [--index <path>] [--json]
specpm search <capability-id> [--index <path>] [--json]
specpm add <capability-id-or-package-ref> [--index <path>] [--project <dir>] [--json]
```

The MVP registry is local and file-backed. Search uses exact capability IDs for
normative resolution.

## Local Lifecycle

```bash
specpm yank <package-id@version> [--index <path>] --reason <reason> [--json]
specpm unyank <package-id@version> [--index <path>] [--json]
```

Yanked packages remain visible to exact search but are rejected by `add` until
they are unyanked.

## Diff

```bash
specpm diff <old-package-dir> <new-package-dir> [--json]
```

The MVP diff is structural and conservative. It classifies changes to package
metadata, capabilities, required capabilities, interfaces, `MUST` constraints,
and compatibility metadata.

## SpecGraph Inbox

```bash
specpm inbox list [--root .specgraph_exports] [--json]
specpm inbox inspect <package-id> [--root .specgraph_exports] [--json]
```

Inbox commands inspect local SpecGraph export bundles without mutating canonical
SpecGraph state.

## Exit Codes

The CLI exit code contract is documented in `SPECS/CLI_EXIT_CODES.md`.

## References

- `README.md`
- `SPECS/CLI_EXIT_CODES.md`
- <doc:JSONContracts>
