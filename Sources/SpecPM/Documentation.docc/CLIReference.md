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

## Remote Registry Metadata

```bash
specpm remote status --registry <url> [--json]
specpm remote packages --registry <url> [--json]
specpm remote package <package-id> --registry <url> [--json]
specpm remote version <package-id@version> --registry <url> [--json]
specpm remote search <capability-id> --registry <url> [--json]
```

Remote commands are explicit read-only metadata clients for the post-MVP
registry contract. `status` and `packages` provide the discovery surface for
local SpecGraph and ContextBuilder observation before requesting a specific
package or capability. Remote commands do not download archives, publish
packages, mutate remote state, or execute package content.

## Public Static Index

```bash
specpm public-index generate [<package-dir>...] [--manifest <accepted-packages.yml>] --output <dir> --registry <url> [--json]
```

The public index generator validates and deterministically packs package
directories, then writes static `/v0` remote registry metadata for package
status, package index, package lookup, package version lookup, and exact
capability search. The output can be hosted by GitHub Pages or another static
host.

The command generates metadata and mirrored deterministic archives only. It
can read the maintainer-reviewed `public-index/accepted-packages.yml` manifest
used by GitHub Pages deployment. It does not publish to a remote service,
mutate GitHub issues, install packages, download archives as a client, or
execute package content.

## Local Public Index Service

```bash
make public-index-up
make public-index-smoke
make public-index-down
```

The compose service serves generated static `/v0` registry metadata at
`http://localhost:8081` by default from `public-index/accepted-packages.yml`.
Use `SPECPM_PUBLIC_INDEX_PORT`, `SPECPM_PUBLIC_INDEX_REGISTRY_URL`, or
`SPECPM_PUBLIC_INDEX_MANIFEST` when another local runtime needs a different
host-visible endpoint or accepted package source.

## Exit Codes

The CLI exit code contract is documented in `specs/CLI_EXIT_CODES.md`.

## References

- `README.md`
- `specs/CLI_EXIT_CODES.md`
- <doc:JSONContracts>
