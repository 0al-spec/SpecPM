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

Inbox JSON includes bundle layout checks, validation status, handoff continuity
fields, and actionable gaps for incomplete SpecGraph export bundles.

Viewer-facing JSON contracts and golden fixtures are documented in
`specs/JSON_CONTRACTS.md`.

Portable conformance artifacts are documented in `specs/CONFORMANCE.md`.

The post-MVP remote registry API contract is documented in
`specs/REMOTE_REGISTRY_API.md`.

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
