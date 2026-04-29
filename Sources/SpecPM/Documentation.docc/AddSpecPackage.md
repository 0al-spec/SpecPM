# Add a SpecPackage

Submit public `SpecPackage` repositories for inclusion in the SpecPM public
alpha registry.

## Overview

Anyone can propose a package for the public index. The current intake path is a
GitHub Issue form, modeled after public package indexes that use issues as a
reviewable queue.

Submission does not publish a package automatically. It validates public package
data, records review evidence in the issue, and lets maintainers decide whether
to add the source to the public index manifest.

Use the issue form:

[Add SpecPackage(s)](https://github.com/0al-spec/SpecPM/issues/new?template=add-specpackages.yml)

## Requirements

Initial submissions should meet these requirements:

- The package repository is publicly accessible.
- The repository URL includes a protocol, usually `https://`.
- The repository contains `specpm.yaml` at the root or at the submitted package
  path.
- Referenced `specs/*.spec.yaml` files exist.
- `specpm validate` passes.
- `metadata.id` is valid and stable.
- `metadata.version` is SemVer.
- `metadata.license` is present.
- Package content is data and does not require execution during validation.
- Package content complies with the index policy and code of conduct.

## Submission Flow

```text
GitHub Issue: Add SpecPackage(s)
        |
        v
Issue form collects public repository URLs
        |
        v
GitHub Actions validates each candidate
        |
        v
Bot comments with pass/fail evidence
        |
        v
Maintainers review the issue
        |
        v
Accepted source is added to public-index/accepted-packages.yml
        |
        v
GitHub Pages publishes static /v0 registry metadata
```

## What to Submit

The issue form asks for:

- one public Git repository URL per line;
- an optional package path when `specpm.yaml` is not at repository root;
- maintainer notes, such as package scope or known validation caveats;
- acknowledgements that the package is public, reviewable, data-only during
  validation, and policy-compliant.

If the package is not at repository root, use a relative package path such as:

```text
packages/email_tools
```

Do not submit credentials, private repository links, signing keys, upload
tokens, or secrets. Public index submission is reviewable metadata intake, not a
remote mutation API.

## Validation

The submission workflow:

- parses the issue form body;
- rejects missing URLs, non-HTTPS URLs, credential-bearing URLs, URL fragments,
  absolute package paths, and package path traversal;
- shallow-clones submitted public repositories without submodules;
- runs `specpm validate` against the submitted package path;
- posts a Markdown validation report back to the issue.

Invalid submissions can still be useful: the validation report shows what needs
to be fixed before maintainer review can continue.

## Acceptance

Maintainers accept packages by reviewing the issue and updating:

```text
public-index/accepted-packages.yml
```

Remote accepted entries are pinned to an exact commit revision before registry
generation. This keeps the public index reproducible and reviewable.

After merge, the GitHub Pages workflow regenerates the static registry metadata
served under:

```text
https://0al-spec.github.io/SpecPM/v0
```

## Boundaries

The public index submission flow does not add:

- `specpm publish`;
- package upload;
- remote mutation APIs;
- authentication or authorization;
- package installation or archive download behavior;
- package signing or trust-web enforcement;
- online intent-to-spec runtime;
- package content execution.

Package content is untrusted data. Package content can describe desired outputs.
Package content cannot command the host.
