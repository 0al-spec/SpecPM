# SpecPM Public Alpha Registry

Status: Alpha
Updated: 2026-04-29
Scope: read-only public static registry for early SpecGraph and SpecNode
integration

## Purpose

The SpecPM public alpha registry exposes a small, reviewed set of SpecPackage
metadata through the static read-only `/v0` registry contract.

This alpha is meant for early ecosystem integration. SpecGraph, SpecNode,
ContextBuilder, and manual tools can discover package IDs, versions,
capabilities, declared canonical intents, and archive metadata without
depending on a mutable registry backend.

## Endpoint

Registry base URL:

```text
https://0al-spec.github.io/SpecPM
```

API path prefix:

```text
/v0
```

Browser viewer:

```text
https://0al-spec.github.io/SpecPM/viewer/
```

The viewer is static and read-only. When hosted on GitHub Pages it reads the
same-origin `/v0` API, so normal browsing does not require cross-origin access.

Client examples:

```bash
specpm remote status --registry https://0al-spec.github.io/SpecPM --json
specpm remote packages --registry https://0al-spec.github.io/SpecPM --json
specpm remote package specnode.core --registry https://0al-spec.github.io/SpecPM --json
specpm remote version specnode.core@0.1.0 --registry https://0al-spec.github.io/SpecPM --json
specpm remote search specnode.typed_job_protocol --registry https://0al-spec.github.io/SpecPM --json
specpm remote intents --registry https://0al-spec.github.io/SpecPM --json
specpm remote intent intent.document_conversion.email_to_markdown --registry https://0al-spec.github.io/SpecPM --json
specpm remote search-intent intent.document_conversion.email_to_markdown --registry https://0al-spec.github.io/SpecPM --json
specpm remote observe --registry https://0al-spec.github.io/SpecPM --package specpm.core --package specnode.core --version specpm.core@0.1.0 --version specnode.core@0.1.0 --capability specpm.registry.public_alpha_index --capability specnode.typed_job_protocol --json
```

The `remote intents` and `remote intent` commands expose an observed intent
catalog built from accepted package metadata. Observed intent IDs are useful for
authoring and discovery, but they are not a canonical intent dictionary.

For a reusable downstream evidence artifact:

```bash
make pages-alpha-report
```

The report is written to `.specpm/pages-alpha-observation.json`.

## Add a SpecPackage

Anyone can propose a public SpecPackage repository for future inclusion in the
public alpha registry:

```text
https://github.com/0al-spec/SpecPM/issues/new?template=add-specpackages.yml
```

Initial requirements:

- the repository is publicly accessible over HTTPS;
- the repository contains `specpm.yaml` at the root or a declared package path;
- referenced `specs/*.spec.yaml` files exist;
- `specpm validate` passes;
- `metadata.id` is stable and valid;
- `metadata.version` is SemVer;
- `metadata.license` is present;
- package content is data and does not require execution during validation.

The validation workflow comments with pass/fail evidence on the issue. A
maintainer still reviews the submission before adding a pinned source to
`public-index/accepted-packages.yml`.

## Alpha Package Set

The alpha registry is seeded from `public-index/accepted-packages.yml`.

Current accepted packages:

- `document_conversion.email_tools@0.1.0`: example package for the original
  RFC fixture and registry smoke tests.
- `specpm.core@0.1.0`: the SpecPM self-spec from this repository root.
- `specnode.core@0.1.0`: the SpecNode package from the pinned public Git source
  `https://github.com/0al-spec/SpecNode.git` at revision
  `9b6046777723435d94d66d4149fe5e9a6c52f604`.

## Intended Consumers

The public alpha registry is useful for:

- SpecGraph observing which SpecPM and SpecNode package capabilities are
  publicly visible.
- SpecNode discovering SpecPM package-generation and typed job protocol
  capabilities.
- ContextBuilder rendering registry availability and package metadata.
- Human operators checking the end-to-end static registry contract.

## Promotion Model

Alpha package promotion is still maintainer-reviewed source control:

1. Update `public-index/accepted-packages.yml`.
2. Validate local generation with `make dev-reload`.
3. Merge through a pull request.
4. Let GitHub Pages publish generated DocC and `/v0` registry metadata.
5. Verify deployment with `make pages-alpha-smoke`.
6. Capture downstream observation evidence with `make pages-alpha-report`.

Remote package sources MUST be public HTTPS Git repositories pinned to an exact
40-character commit revision. If the reviewed ref no longer resolves to the
pinned revision, public index generation fails.

## Boundaries

The public alpha registry does not add:

- `specpm publish`;
- package upload;
- remote mutation APIs;
- authentication or authorization;
- package archive install/download client behavior;
- package signing or trust-web enforcement;
- online intent-to-spec runtime;
- package content execution.

The registry is metadata-only and static-hosted. Package content remains
untrusted data.
