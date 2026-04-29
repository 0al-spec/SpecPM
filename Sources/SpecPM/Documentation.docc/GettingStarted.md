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
make dev-up
make dev-smoke
```

The compose service exposes a local read-only public index at
`http://localhost:8081`. It regenerates `.specpm/public-index` from the
maintainer-reviewed `public-index/accepted-packages.yml` manifest and serves
the static `/v0` registry tree for manual testing and local SpecGraph or
ContextBuilder integration.

After changing package manifests, accepted package sources, registry generator
code, or remote contract code, recreate the live container and smoke it:

```bash
make dev-reload
```

Smoke the deployed GitHub Pages registry:

```bash
make pages-smoke
```

For the public alpha seed package set, run:

```bash
make pages-alpha-smoke
make pages-alpha-report
```

`pages-alpha-smoke` includes the baseline Pages smoke checks.
`pages-alpha-report` writes `.specpm/pages-alpha-observation.json` for
downstream tools.

```bash
make dev-down
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
- <doc:Deployment>
