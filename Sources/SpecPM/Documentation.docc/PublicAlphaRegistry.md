# Public Alpha Registry

The public alpha registry is the first live SpecPM ecosystem surface for
SpecGraph, SpecNode, ContextBuilder, and manual tools.

It is a static, read-only registry hosted through GitHub Pages.

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
```

Operators can run the same alpha visibility checks with:

```bash
make pages-alpha-smoke
```

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
