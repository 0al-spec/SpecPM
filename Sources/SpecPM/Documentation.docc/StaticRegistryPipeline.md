# Static Registry Pipeline

Understand how SpecPM exposes a registry API through static GitHub Pages files
without running a mutable public backend.

## Overview

The public SpecPM registry is a build-time API. Package metadata is reviewed,
validated, generated into deterministic `/v0` JSON, and then served as static
files by GitHub Pages.

No request-time server computes registry responses. GitHub Pages only serves the generated artifact.

```text
GitHub Issue: Add SpecPackage(s)
        |
        v
GitHub Actions validation
        |
        v
Maintainer review
        |
        v
public-index/accepted-packages.yml
        |
        v
specpm public-index generate
        |
        v
GitHub Pages artifact
        |
        v
/v0 static JSON registry API
```

## What Runs When

Submission-time work happens in GitHub Issues and GitHub Actions:

- users submit public repository URLs through the `Add SpecPackage(s)` issue
  form;
- the validation workflow checks package shape and posts pass/fail evidence;
- maintainers decide whether to accept the submitted package source.

Build-time work happens after reviewed source changes:

- maintainers update `public-index/accepted-packages.yml`;
- accepted remote sources are pinned to exact commit revisions;
- `specpm public-index generate` validates accepted packages;
- the generator writes static `/v0` registry metadata and deterministic package
  archives into the Pages artifact.

Request-time work is static file serving:

- GitHub Pages returns generated JSON files;
- no Python process, database, queue, LLM, package validator, or resolver runs
  on public registry reads;
- public requests cannot mutate registry state.

## Public Endpoints

The public alpha registry base URL is:

```text
https://0al-spec.github.io/SpecPM
```

The read-only registry API is served under:

```text
/v0
```

Current metadata endpoints include:

```text
GET /v0/status
GET /v0/packages
GET /v0/packages/{package_id}
GET /v0/packages/{package_id}/versions/{version}
GET /v0/capabilities/{capability_id}/packages
GET /v0/intents/{intent_id}/packages
```

These endpoints are metadata lookup surfaces. They do not install packages,
download archives into a project, execute package content, authenticate users,
or publish new packages.

## Static Host Details

SpecPM writes both JSON files and adjacent static-host index files. This lets
GitHub Pages serve extensionless URLs such as `/v0/status` while preserving a
direct strict JSON path for consumers that need one.

For example:

```text
/v0/status
/v0/status/
/v0/status/index.json
```

The extensionless path may redirect and can be served by GitHub Pages with a
static-host content type. Strict JSON consumers should use `index.json`, such as:

```text
https://0al-spec.github.io/SpecPM/v0/status/index.json
```

SpecPM's own `specpm remote` client handles the published registry surface and
validates payload shape before returning success.

## Local Development Loop

The same generated registry surface can run locally through Docker:

```bash
make dev-up
make dev-smoke
```

The local base URL is:

```text
http://localhost:8081
```

After changing accepted sources, package metadata, registry generation code, or
registry contracts, recreate and smoke the local service:

```bash
make dev-reload
```

This makes the local Docker service the first live integration surface for
SpecGraph, ContextBuilder, SpecNode, and manual checks.

## Boundaries

The static registry pipeline does not add:

- `specpm publish`;
- package upload;
- remote mutation APIs;
- authentication or authorization;
- package archive install/cache behavior;
- package content execution;
- semantic search;
- online intent-to-spec runtime.

Package content is untrusted data. Package content can describe desired outputs.
Package content cannot command the host.

## Related Topics

- <doc:AddSpecPackage>
- <doc:PublicAlphaRegistry>
- <doc:Deployment>
- <doc:RegistryOperations>
- <doc:JSONContracts>
