# SpecPM

Intent-level dependency management for local `SpecPackage` and `BoundarySpec`
bundles.

[The first draft of RFC with Specification Package format](https://github.com/0al-spec/SpecPM/blob/main/RFC/SpecGraph-RFC-0001.md)

License: MIT. See `LICENSE`.

## MVP baseline

Install locally:

```bash
python3 -m pip install -e ".[dev]"
specpm --help
```

Run without installing by using the source tree:

```bash
PYTHONPATH=src python3 -m specpm.cli validate examples/email_tools --json
PYTHONPATH=src python3 -m specpm.cli inspect examples/email_tools --json
PYTHONPATH=src python3 -m specpm.cli pack examples/email_tools -o /tmp/email_tools.specpm.tgz --json
PYTHONPATH=src python3 -m specpm.cli index examples/email_tools --index /tmp/specpm-index.json --json
PYTHONPATH=src python3 -m specpm.cli search document_conversion.email_to_markdown --index /tmp/specpm-index.json --json
PYTHONPATH=src python3 -m specpm.cli yank document_conversion.email_tools@0.1.0 --index /tmp/specpm-index.json --reason "local lifecycle smoke" --json
PYTHONPATH=src python3 -m specpm.cli unyank document_conversion.email_tools@0.1.0 --index /tmp/specpm-index.json --json
PYTHONPATH=src python3 -m specpm.cli add document_conversion.email_to_markdown --index /tmp/specpm-index.json --project /tmp/specpm-project --json
PYTHONPATH=src python3 -m specpm.cli diff examples/email_tools examples/email_tools --json
PYTHONPATH=src python3 -m specpm.cli inbox list --root tests/fixtures/specgraph_exports --json
PYTHONPATH=src python3 -m specpm.cli inbox inspect specgraph.core_repository_facade --root tests/fixtures/specgraph_exports --json
PYTHONPATH=src python3 -m specpm.cli public-index generate --manifest public-index/accepted-packages.yml --output /tmp/specpm-public-index --registry https://registry.example.invalid --json
```

Run through Docker:

```bash
docker build -t specpm:dev .
docker compose run --rm specpm validate examples/email_tools --json
docker compose run --rm specpm inspect examples/email_tools --json
docker compose run --rm specpm pack examples/email_tools -o /tmp/email_tools.specpm.tgz --json
docker compose run --rm specpm index examples/email_tools --index /tmp/specpm-index.json --json
docker compose run --rm specpm search document_conversion.email_to_markdown --index /tmp/specpm-index.json --json
docker compose run --rm specpm yank document_conversion.email_tools@0.1.0 --index /tmp/specpm-index.json --reason "local lifecycle smoke" --json
docker compose run --rm specpm unyank document_conversion.email_tools@0.1.0 --index /tmp/specpm-index.json --json
docker compose run --rm specpm add document_conversion.email_to_markdown --index /tmp/specpm-index.json --project /tmp/specpm-project --json
docker compose run --rm specpm diff examples/email_tools examples/email_tools --json
docker compose run --rm specpm inbox list --root tests/fixtures/specgraph_exports --json
docker compose run --rm specpm inbox inspect specgraph.core_repository_facade --root tests/fixtures/specgraph_exports --json
docker compose run --rm specpm public-index generate --manifest public-index/accepted-packages.yml --output /tmp/specpm-public-index --registry https://registry.example.invalid --json
```

Run the local public index service:

```bash
make public-index-up
make public-index-smoke
```

The default registry URL is `http://localhost:8081`. The service regenerates
`.specpm/public-index` from `public-index/accepted-packages.yml` and serves the
static `/v0` tree through Docker Compose. `make public-index-smoke` reads
`/v0/status`, `/v0/packages`, and an exact capability search endpoint. Stop it
with:

```bash
make public-index-down
```

For integration from another local runtime, override:

```bash
SPECPM_PUBLIC_INDEX_PORT=8082 make public-index-up
SPECPM_PUBLIC_INDEX_REGISTRY_URL=http://localhost:8082 make public-index-smoke
```

Run the post-MVP read-only remote metadata client against a compatible registry:

```bash
PYTHONPATH=src python3 -m specpm.cli remote status --registry https://registry.example.invalid --json
PYTHONPATH=src python3 -m specpm.cli remote packages --registry https://registry.example.invalid --json
PYTHONPATH=src python3 -m specpm.cli remote search document_conversion.email_to_markdown --registry https://registry.example.invalid --json
docker compose run --rm specpm remote status --registry https://registry.example.invalid --json
docker compose run --rm specpm remote packages --registry https://registry.example.invalid --json
docker compose run --rm specpm remote search document_conversion.email_to_markdown --registry https://registry.example.invalid --json
```

Quality gates:

```bash
make test
make lint
make format-check
make docker-test
```

Implemented first slice:

- `specpm validate <package-dir> [--json]`
- `specpm inspect <package-dir> [--json]`
- `specpm pack <package-dir> [-o <archive>] [--json]`
- `specpm index <package-dir-or-archive> [--index <path>] [--json]`
- `specpm search <capability-id> [--index <path>] [--json]`
- `specpm add <capability-id-or-package-ref> [--index <path>] [--project <dir>] [--json]`
- `specpm yank <package-id@version> [--index <path>] --reason <reason> [--json]`
- `specpm unyank <package-id@version> [--index <path>] [--json]`
- `specpm diff <old-package-dir> <new-package-dir> [--json]`
- `specpm inbox list [--root .specgraph_exports] [--json]`
- `specpm inbox inspect <package-id> [--root .specgraph_exports] [--json]`
- `specpm remote status --registry <url> [--json]`
- `specpm remote packages --registry <url> [--json]`
- `specpm remote package <package-id> --registry <url> [--json]`
- `specpm remote version <package-id@version> --registry <url> [--json]`
- `specpm remote search <capability-id> --registry <url> [--json]`
- `specpm public-index generate [<package-dir>...] [--manifest <accepted-packages.yml>] --output <dir> --registry <url> [--json]`

Inbox JSON includes bundle layout checks, validation status, handoff continuity
fields, and actionable gaps for incomplete SpecGraph export bundles.

Viewer-facing JSON contracts and golden fixtures are documented in
`specs/JSON_CONTRACTS.md`.

Portable conformance artifacts are documented in `specs/CONFORMANCE.md`.

The post-MVP remote registry API contract is documented in
`specs/REMOTE_REGISTRY_API.md`. The `specpm remote` commands are read-only
metadata clients for that contract; they do not download package archives,
publish packages, mutate remote state, or execute package content.

Public index and enterprise registry deployment options are tracked in
`specs/INDEX_SUBMISSION_FLOW.md`. The reference public-index issue form is
`.github/ISSUE_TEMPLATE/add-specpackages.yml`, and the reference submission
validation workflow is `.github/workflows/package-submission-check.yml`.
`specpm public-index generate` emits static read-only `/v0` registry metadata
and deterministic package archives for GitHub Pages-style hosting. The checked-in
accepted package source for Pages is `public-index/accepted-packages.yml`; it is
a maintainer-reviewed list of repository-relative package directories or pinned
public Git sources, not a remote mutation API. Remote entries must include a
reviewed `ref` plus exact commit `revision`; generation fails if the checkout no
longer resolves to that revision. The generator does not publish packages,
mutate remote state, install packages, or execute package content.
`docker compose up public-index` serves that generated registry locally for
SpecGraph, ContextBuilder, and manual integration testing.

SpecPM does not translate plain-text user intent into capability IDs or package
selections. Natural-language discovery, embeddings, vector search, RAG, and
semantic reranking belong in ContextBuilder, SpecGraph, or a future downstream
intent resolver. SpecPM remains the exact lookup and verification layer for
structured package metadata. This boundary is documented in
`specs/INTENT_DISCOVERY_BOUNDARY.md`.

CLI exit code behavior is documented in `specs/CLI_EXIT_CODES.md`. RFC 0001
implementation coverage is tracked in `specs/RFC_0001_COVERAGE.md`.

This repository is also a self-describing SpecPM package. The root
`specpm.yaml` and `specs/specpm.spec.yaml` describe the implemented public CLI
surface and importable core functions as a `SpecPackage`. CI validates this
self-spec and checks that it tracks the current CLI commands and exported core
API.

Build the DocC documentation site locally:

```bash
make docs-build
```

The GitHub Pages workflow builds the same DocC catalog from
`Sources/SpecPM/Documentation.docc`.

The same Pages artifact also includes the generated read-only public index
metadata under `/v0`, produced from `public-index/accepted-packages.yml` by
`specpm public-index generate` during the documentation workflow. This is static
hosting only; remote manifest entries are checked out as untrusted data at a
pinned commit before validation and packing. This does not add `specpm publish`,
remote mutation APIs, package install behavior, or package content execution.
