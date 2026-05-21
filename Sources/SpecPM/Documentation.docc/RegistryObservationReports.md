# Registry Observation Reports

Capture reusable JSON evidence for local and deployed public registry checks.

The canonical source document is `specs/REGISTRY_OBSERVATION_REPORTS.md`.

## Targets

Use the local Docker-backed public index:

```bash
make dev-reload
make public-index-observation-report
```

Use the deployed GitHub Pages registry:

```bash
make pages-observation-report
```

Generate both when comparing local and deployed registry behavior:

```bash
make registry-observation-reports
```

## Outputs

Reusable reports are written under:

```text
.specpm/registry-observations/
```

Default filenames:

- `local-public-index-observation.json`
- `pages-public-index-observation.json`

`.specpm/` is ignored by Git. Attach reports to issues, pull requests, or
release notes when they are needed as review evidence.

## Coverage

The default report checks `specpm.core`, `specnode.core`, retained and current
package versions, exact capability lookup, and exact observed intent lookup.
Reports remain read-only metadata artifacts; they do not download archives,
install packages, execute package content, mutate registry state, or decide
SpecGraph graph meaning.

## References

- <doc:PublicAlphaRegistry>
- <doc:SpecGraphRegistryObservation>
- <doc:Deployment>
- <doc:JSONContracts>
