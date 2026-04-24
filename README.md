# SpecPM

Intent-level dependency management for local `SpecPackage` and `BoundarySpec`
bundles.

[The first draft of RFC with Specification Package format](https://github.com/0al-spec/SpecPM/blob/main/RFC/SpecGraph-RFC-0001.md)

## MVP baseline

Install locally:

```bash
python3 -m pip install -e ".[dev]"
specpm --help
```

Run without installing by using the source tree:

```bash
PYTHONPATH=src python3 -m specpm.cli validate examples/email_tools --json
PYTHONPATH=src python3 -m specpm.cli pack examples/email_tools -o /tmp/email_tools.specpm.tgz --json
PYTHONPATH=src python3 -m specpm.cli index examples/email_tools --index /tmp/specpm-index.json --json
PYTHONPATH=src python3 -m specpm.cli search document_conversion.email_to_markdown --index /tmp/specpm-index.json --json
PYTHONPATH=src python3 -m specpm.cli add document_conversion.email_to_markdown --index /tmp/specpm-index.json --project /tmp/specpm-project --json
PYTHONPATH=src python3 -m specpm.cli diff examples/email_tools examples/email_tools --json
PYTHONPATH=src python3 -m specpm.cli inbox list --json
```

Run through Docker:

```bash
docker build -t specpm:dev .
docker compose run --rm specpm validate examples/email_tools --json
docker compose run --rm specpm pack examples/email_tools -o /tmp/email_tools.specpm.tgz --json
docker compose run --rm specpm index examples/email_tools --index /tmp/specpm-index.json --json
docker compose run --rm specpm search document_conversion.email_to_markdown --index /tmp/specpm-index.json --json
docker compose run --rm specpm add document_conversion.email_to_markdown --index /tmp/specpm-index.json --project /tmp/specpm-project --json
docker compose run --rm specpm diff examples/email_tools examples/email_tools --json
docker compose run --rm specpm inbox list --json
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
- `specpm diff <old-package-dir> <new-package-dir> [--json]`
- `specpm inbox list [--root .specgraph_exports] [--json]`
- `specpm inbox inspect <package-id> [--root .specgraph_exports] [--json]`

Inbox JSON includes bundle layout checks, validation status, handoff continuity
fields, and actionable gaps for incomplete SpecGraph export bundles.

Viewer-facing JSON contracts and golden fixtures are documented in
`SPECS/JSON_CONTRACTS.md`.
