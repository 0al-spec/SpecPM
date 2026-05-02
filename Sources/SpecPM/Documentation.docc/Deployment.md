# Deployment

SpecPM follows a deploy-first operating model for the registry surface: the
current `/v0` public index should be runnable locally as a live service and
smoke-tested through the same read-only client contract that downstream
consumers use.

## Local Live Registry

Start and smoke the Docker-backed local public index:

```bash
make dev-up
```

The service listens at:

```text
http://localhost:8081/v0
```

It generates `.specpm/public-index` from the maintainer-reviewed
`public-index/accepted-packages.yml` manifest and serves static registry
metadata for SpecGraph, ContextBuilder, and manual ecosystem testing.

After changing accepted sources, package metadata, public index generation code,
or remote registry contract code, recreate the service and smoke the baseline
registry surface:

```bash
make dev-reload
```

For full alpha package visibility, run:

```bash
make public-alpha-smoke
make public-alpha-report
```

`public-alpha-smoke` includes the baseline local public-index smoke checks.
`public-alpha-report` writes `.specpm/public-alpha-observation.json` for
downstream tooling.

Stop the local service:

```bash
make dev-down
```

## Public Static Deployment

The current public deployment is GitHub Pages:

```text
https://0al-spec.github.io/SpecPM
```

The Pages artifact contains DocC documentation, generated static `/v0`
registry metadata, and the static registry viewer at `/viewer/`. Smoke the
deployed baseline registry with:

```bash
make pages-smoke
```

For full public alpha visibility, run:

```bash
make pages-alpha-smoke
make pages-alpha-report
```

`pages-alpha-smoke` includes the baseline Pages smoke checks.
`pages-alpha-report` writes `.specpm/pages-alpha-observation.json`.

See <doc:StaticRegistryPipeline> for the build-time pipeline that turns reviewed
package sources into the public static registry API.

## Boundaries

The deploy-first loop does not add:

- `specpm publish`;
- a remote mutation API;
- authentication or authorization;
- archive download or install behavior;
- package execution;
- online intent-to-spec runtime.

Current public reads are static files. Future non-static services need separate
design for fresh-version deployment, backups, rollback, rate limits, abuse
monitoring, and DDoS protection.

See <doc:RegistryOperations> for the detailed runbook.

## Source Contract

The detailed operating notes are maintained in `specs/DEPLOY_FIRST.md` and
`specs/REGISTRY_OPERATIONS.md`.
