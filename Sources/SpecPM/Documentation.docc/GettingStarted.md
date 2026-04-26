# Getting Started

Install SpecPM locally from a checkout:

```bash
python3 -m pip install -e ".[dev]"
specpm --help
```

Run commands without installing by using the source tree:

```bash
PYTHONPATH=src python3 -m specpm.cli validate examples/email_tools --json
PYTHONPATH=src python3 -m specpm.cli inspect examples/email_tools --json
PYTHONPATH=src python3 -m specpm.cli pack examples/email_tools -o /tmp/email_tools.specpm.tgz --json
```

Run through Docker:

```bash
docker build -t specpm:dev .
docker compose run --rm specpm validate examples/email_tools --json
docker compose run --rm specpm inspect examples/email_tools --json
docker compose run --rm specpm pack examples/email_tools -o /tmp/email_tools.specpm.tgz --json
```

Run the local public index service:

```bash
make public-index-up
make public-index-smoke
```

The compose service exposes a local read-only public index at
`http://localhost:8081`. It regenerates `.specpm/public-index` from the example
package and serves the static `/v0` registry tree for manual testing and local
SpecGraph or ContextBuilder integration.

```bash
make public-index-down
```

Use the repository quality gates before opening or merging changes:

```bash
make test
make lint
make format-check
make docker-test
```

Build the DocC documentation locally:

```bash
make docs-build
```

The documentation build writes static output to `.docc-build/`.

## Useful Paths

- Runtime implementation: `src/specpm/`
- Tests: `tests/test_core.py`
- Golden JSON fixtures: `tests/fixtures/golden/`
- Conformance suite: `tests/fixtures/conformance/specpm-conformance-v0.json`
- Example package: `examples/email_tools/`

## Next Topics

- <doc:PackageModel>
- <doc:CLIReference>
- <doc:JSONContracts>
