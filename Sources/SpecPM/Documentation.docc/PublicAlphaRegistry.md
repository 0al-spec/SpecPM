# Public Alpha Registry

The public alpha registry is the first live SpecPM ecosystem surface for
SpecGraph, SpecNode, ContextBuilder, and manual tools.

It is a static, read-only registry hosted through GitHub Pages.

See <doc:StaticRegistryPipeline> for how the public `/v0` API is generated and
served without a mutable public backend.

## Endpoint

Registry base URL:

```text
https://0al-spec.github.io/SpecPM
```

API prefix:

```text
/v0
```

Try the registry with:

```bash
specpm remote status --registry https://0al-spec.github.io/SpecPM --json
specpm remote packages --registry https://0al-spec.github.io/SpecPM --json
specpm remote package specnode.core --registry https://0al-spec.github.io/SpecPM --json
specpm remote version specnode.core@0.1.0 --registry https://0al-spec.github.io/SpecPM --json
specpm remote search specnode.typed_job_protocol --registry https://0al-spec.github.io/SpecPM --json
specpm remote observe --registry https://0al-spec.github.io/SpecPM --package specpm.core --package specnode.core --version specpm.core@0.1.0 --version specnode.core@0.1.0 --capability specpm.registry.public_alpha_index --capability specnode.typed_job_protocol --json
```

Operators can run the same alpha visibility checks with:

```bash
make pages-alpha-smoke
```

Generate a machine-readable downstream observation report with:

```bash
make pages-alpha-report
```

The report is written to `.specpm/pages-alpha-observation.json`.

## Add a SpecPackage

Anyone can propose a public SpecPackage repository for future inclusion in the
public alpha registry:

[Add SpecPackage(s)](https://github.com/0al-spec/SpecPM/issues/new?template=add-specpackages.yml)

The submission must point to a public HTTPS Git repository with `specpm.yaml`
and referenced `specs/*.spec.yaml` files at the repository root or declared
package path. The package must pass `specpm validate`; maintainers review
validated submissions before adding sources to `public-index/accepted-packages.yml`.

See <doc:AddSpecPackage> for the full submission guide.

## Seed Packages

The alpha registry currently exposes:

- `document_conversion.email_tools@0.1.0`;
- `specpm.core@0.1.0`;
- `specnode.core@0.1.0`.

`specpm.core` comes from the SpecPM repository root. `specnode.core` comes from
the pinned public Git source recorded in `public-index/accepted-packages.yml`.

## Boundary

The alpha registry is metadata-only. It does not provide `specpm publish`,
package upload, remote mutation APIs, authentication, package installation,
online intent-to-spec runtime, or package content execution.

## Source Contract

The detailed alpha contract is maintained in `specs/PUBLIC_ALPHA.md`.
