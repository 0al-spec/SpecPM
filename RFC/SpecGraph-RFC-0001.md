# SpecGraph RFC 0001 Minimal Specification Package Format for SpecPM MVP

**Status**: Draft
**Version**: 0.0.1
**Category**: Standards Track, Public
**Created**: 2026-04-20
**Target** Release: SpecPM MVP
**Authors**: SpecGraph Project, Egor Merkushev, Pavel Lebedev

## 1. Abstract

This document defines the **Minimal Specification Package Format** for the first MVP version of **SpecPM**, the SpecGraph package manager.

The format allows authors, tools, and import adapters to package reusable software intent as machine-readable **boundary specifications**. A boundary specification describes the external contract of a repository, module, component, or bounded context: what capability it provides, what it requires, how it is integrated, and what evidence supports the claim.

This RFC intentionally does not define the full SpecGraph model. It defines the smallest useful package format that enables:

1. publishing specification packages;
2. indexing packages by capability;
3. resolving packages by exact capability ID;
4. importing a package into a consuming project;
5. preserving provenance from foreign formats such as CodeSpeak, OpenAPI, GraphQL, protobuf, README files, tests, and source files;
6. validating the package structure.

The core idea is:

> SpecPM MVP manages reusable **specification packages**, not code packages.
> A package is useful if it can say: “I provide this capability, under these constraints, with this evidence, through this boundary.”

## 2. Status of This Memo

This document is a draft and is not yet stable.

Implementations **MAY** experiment with the format described here. Breaking changes are expected before `specpm.dev/v1`.

Once accepted, this RFC will become the normative basis for the first SpecPM MVP PRD.

## 3. Design Intent

SpecPM is not intended to be “npm for arbitrary Markdown files.” It is intended to be a package manager for **software intent**.

However, the MVP **MUST** avoid overdesign. It **MUST NOT** require a full formal ontology, proof system, code generator, or deep static analyzer. The package format MUST be useful even when the source repository contains only approximate documentation.

The initial format is therefore **boundary-first**.

It focuses on:

```
What does this package provide?
What does it require?
Where is its external boundary?
How does a consuming system interact with it?
What constraints matter?
What evidence supports the spec?
Where did the information come from?
```

It intentionally does not attempt to model every internal function, class, algorithm, or implementation detail.

## 4. Terminology

### 4.1. SpecPM

**SpecPM** is the package manager for SpecGraph specification packages.

### 4.2. Spec Package

A **Spec Package** is a versioned package containing one or more specification documents and package-level metadata.

A Spec Package is the unit of publication, resolution, installation, and import.

### 4.3. Boundary Spec

A **Boundary Spec** is a machine-readable description of a bounded context, component, repository facade, module, external API, plugin, service, CLI tool, library surface, or other reusable software boundary.

### 4.4. Capability

A **Capability** is a named reusable ability provided or required by a package.

Examples:

```
document_conversion.email_to_markdown
auth.secure_token_storage
payments.card_authorization
search.full_text_indexing
observability.audit_logging
```

For the MVP, capabilities are resolved by exact identifier matching.

### 4.5. Bounded Context Border

A **Bounded Context Border** is the external surface through which a consumer, host system, or neighboring context interacts with the specified component.

This may include public APIs, CLI commands, HTTP routes, config files, events, queues, plugin registries, generated files, environment variables, or shared integration files.

### 4.6. Evidence

**Evidence** is any source artifact that supports a claim in the spec.

Examples:

```
README.md
docs/
tests/
OpenAPI files
CodeSpeak specs
GraphQL schemas
protobuf files
source files
examples
architecture decision records
```

### 4.7. Provenance

**Provenance** records where a claim came from and how trustworthy that source is considered.

### 4.8. Foreign Artifact

A **Foreign Artifact** is a specification-like or documentation artifact not native to SpecGraph.

Examples:

```
CodeSpeak .cs.md files
OpenAPI documents
GraphQL schemas
protobuf files
AsyncAPI documents
README files
ADR documents
package manifests
```

Foreign artifacts **MAY** be preserved inside a Spec Package. SpecPM **MUST NOT** require support for any particular foreign format in the MVP.

### 4.9. Implementation Binding

An **Implementation Binding** links a Boundary Spec to concrete implementation artifacts such as source files, packages, modules, repositories, or generated adapters.

Implementation bindings are **OPTIONAL** in this RFC.

## 5. Normative Language

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described by RFC 2119 and RFC 8174.  

Lowercase words such as “must”, “should”, and “may” are used in their ordinary English sense and are not normative.

## 6. Goals

The Minimal Specification Package Format **MUST** support the following MVP goals:

1. A package author can create a versioned specification package.
2. A registry can index packages by package ID, version, capabilities, license, compatibility metadata, and keywords.
3. A consumer can search for packages by exact capability ID.
4. A consumer can inspect what a package provides and requires.
5. A consumer can import the package metadata into a project-level SpecGraph.
6. A package can preserve references to source documentation, foreign specs, tests, and implementation files.
7. A validator can determine whether the package is structurally valid.
8. SpecPM can detect basic breaking changes between two package versions.

## 7. Non-Goals

This RFC does not define:

1. a full SpecGraph ontology;
2. code generation semantics;
3. automatic reverse engineering of arbitrary codebases;
4. AI-based semantic search;
5. formal verification;
6. runtime execution;
7. sandboxing;
8. package signing;
9. proof-carrying code;
10. full dependency solving;
11. full semantic diffing;
12. marketplace governance;
13. trust scoring;
14. compatibility with every existing spec language.

These features **MAY** be added by future RFCs.

## 8. Format Overview

A Spec Package is a directory or archive with this minimal layout:

```
my-package/
  specpm.yaml
  specs/
    main.spec.yaml
  evidence/
    README.md
    tests/
  foreign/
    codespeak/
    openapi/
    graphql/
```

Only the following are **REQUIRED**:

```
specpm.yaml
at least one BoundarySpec document
```

The canonical package manifest file name is:

```
specpm.yaml
```

A package **MAY** also be represented as a single bundled file, but the directory layout is the normative MVP representation.

## 9. Serialization Format

SpecPM MVP packages use `YAML` for human authoring.

Implementations **SHOULD** parse the format as a restricted YAML 1.2 subset consisting only of JSON-compatible maps, arrays, strings, numbers, booleans, and null values. YAML 1.2 was designed to align YAML with JSON more closely, but YAML as a language remains complex; therefore this RFC restricts the accepted subset for interoperability.  

The following YAML features **MUST NOT** be used in MVP packages:

```
anchors
aliases
custom tags
multiple YAML documents in one file
implicit non-JSON scalar typing
executable tags
binary blobs
```

A JSON representation **MAY** be supported later. Implementations **SHOULD** keep the data model JSON-compatible so that JSON Schema validation can be used. JSON Schema is explicitly designed to describe and validate the required structure of JSON documents.  

## 10. Package Manifest: specpm.yaml

The package manifest describes the package as a publishable and resolvable unit.

### 10.1. Minimal Example

```yaml
apiVersion: specpm.dev/v0.1
kind: SpecPackage
metadata:
  id: document_conversion.email_tools
  name: Email Tools
  version: 0.1.0
  summary: Boundary specifications for email document conversion.
  license: MIT
  authors:
    - name: Example Author
specs:
  - path: specs/email-to-markdown.spec.yaml
index:
  provides:
    capabilities:
      - document_conversion.email_to_markdown
  requires:
    capabilities: []
compatibility:
  platforms:
    - any
  languages: []
foreignArtifacts:
  - format: codespeak
    path: foreign/codespeak/email_converter.cs.md
    role: primary_intent_source
```

## 10.2. Required Fields

A valid specpm.yaml manifest **MUST** contain:

| Field | Required | Description |
|---|---|---|
| `apiVersion` | yes | SpecGraph format version. For this RFC: specpm.dev/v0.1. |
| `kind` | yes | **MUST** be SpecPackage. |
| `metadata.id` | yes	| Stable package identifier. |
| `metadata.name` | yes | Human-readable package name. |
| `metadata.version` | yes | Package version. |
| `metadata.summary` | yes | Short human-readable package summary. |
| `metadata.license` | yes | Package license expression or UNLICENSED. |
| `specs` | yes | List of Boundary Spec file paths. |
| `index.provides.capabilities` | yes | Capabilities exposed for registry indexing. |

### 10.3. Package Identifier

`metadata.id` **MUST** be stable across versions.

It **SHOULD** use lowercase dotted names.

Examples:

```
auth.secure_token_storage
document_conversion.email_tools
payments.stripe_card_authorization
observability.audit_logger
```

For MVP validation, package IDs **MUST** match:

```regex
^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$
```

### 10.4. Versioning

`metadata.version` **MUST** follow Semantic Versioning 2.0.0.

SemVer defines `MAJOR.MINOR.PATCH`, where major increments signal incompatible API changes, minor increments signal backward-compatible additions, and patch increments signal backward-compatible fixes.  

In SpecPM, SemVer applies to the **public specification contract**, not necessarily to implementation code.

A package **MUST** increment `MAJOR` when it introduces a breaking change to its public specification contract.

Breaking changes include, but are not limited to:

```
removing a provided capability
renaming a capability
changing the meaning of a capability incompatibly
removing a public interface
changing required inputs incompatibly
changing outputs incompatibly
adding a new required dependency
strengthening a MUST-level constraint
weakening an advertised guarantee
changing package identity
```

A package **SHOULD** increment `MINOR` when it adds backward-compatible capabilities, optional interfaces, evidence, or optional dependencies.

A package **SHOULD** increment `PATCH` when it fixes typos, metadata errors, evidence paths, descriptions, or non-contractual clarifications.

### 10.5. Registry Index Fields

The index section exists because registries need to index packages without fully understanding every spec document.

The manifest-level `index.provides.capabilities` field **MUST** contain every primary capability that the package wants to expose for search and resolution.

SpecPM validators **SHOULD** check that every manifest-level capability appears in at least one referenced Boundary Spec.

The MVP registry **MUST** support exact lookup by capability ID.

The MVP registry **MAY** support keyword search.

The MVP registry **MUST NOT** rely on AI semantic search for normative resolution behavior.

## 11. Boundary Spec Document

A Boundary Spec describes a reusable bounded context or external contract.

The canonical file extension is:

```
.spec.yaml
```

### 11.1. Minimal Example

```yaml
apiVersion: specpm.dev/v0.1
kind: BoundarySpec
metadata:
  id: document_conversion.email_to_markdown
  title: Email to Markdown Converter
  version: 0.1.0
  status: draft
intent:
  summary: Convert email message files into Markdown while preserving visible message content and basic metadata.
scope:
  boundedContext: email_converter
  includes:
    - Parse email message input.
    - Extract subject, sender, recipients, date, and body.
    - Produce Markdown output.
  excludes:
    - Send email messages.
    - Authenticate to mail servers.
    - Synchronize inbox state.
provides:
  capabilities:
    - id: document_conversion.email_to_markdown
      role: primary
      summary: Convert email content into Markdown.
requires:
  capabilities: []
interfaces:
  inbound:
    - id: email_file_input
      kind: file
      summary: Accepts an email message file as input.
      inputs:
        - name: source
          mediaTypes:
            - message/rfc822
          extensions:
            - .eml
      outputs:
        - name: markdown
          mediaTypes:
            - text/markdown
  outbound: []
effects:
  sideEffects:
    - id: reads_input_file
      kind: filesystem_read
      summary: Reads the supplied email file.
constraints:
  - id: no_network_access_required
    level: MUST
    statement: Converting a local email file must not require network access.
evidence:
  - id: readme
    kind: documentation
    path: evidence/README.md
    supports:
      - intent.summary
      - provides.capabilities.document_conversion.email_to_markdown
provenance:
  sourceConfidence:
    intent: medium
    boundary: medium
    behavior: low
```

11.2. Required Fields

A valid Boundary Spec **MUST** contain:

| Field | Required | Description |
|---|---|---|
| `apiVersion` | yes | **MUST** be `specpm.dev/v0.1`. |
| `kind` | yes | **MUST** be BoundarySpec.
| `metadata.id` |	yes | Stable spec identifier. |
| `metadata.title` | yes | Human-readable title. |
| `metadata.version` | yes | Spec version. |
| `intent.summary` | yes | One-sentence purpose. |
| `scope.boundedContext` | yes |	Name of the bounded context or boundary. |
| `provides.capabilities` |	yes |	List of capabilities provided by this spec. |
| `interfaces` | yes | Inbound and/or outbound integration surface. |
| `evidence` | yes | At least one evidence entry or explicit empty list with justification. |

### 11.3. Recommended Fields

A Boundary Spec **SHOULD** contain:

```
scope.includes
scope.excludes
requires.capabilities
effects.sideEffects
constraints
provenance
implementationBindings
foreignArtifacts
keywords
```

## 12. Capability Model

### 12.1. Capability Identifier

A capability ID **MUST** be a stable string.

It **SHOULD** use this style:

```
domain.object_action
```

Examples:

```
auth.token_persistence
auth.secure_token_storage
document_conversion.email_to_markdown
http.retry_policy
storage.key_value_cache
observability.audit_logging
```

For MVP validation, capability IDs **MUST** match:

```regex
^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$
```

### 12.2. Provided Capabilities

A provided capability describes what the package offers.

```yaml
provides:
  capabilities:
    - id: auth.secure_token_storage
      role: primary
      summary: Persist, retrieve, and delete authentication tokens securely.
```

The field role **MAY** be:

```
primary
secondary
supporting
experimental
```

A package **MUST** have at least one primary capability across all Boundary Specs.

### 12.3. Required Capabilities

A required capability describes what the package expects from its environment or other packages.

```yaml
requires:
  capabilities:
    - id: platform.secure_storage
      optional: false
      summary: Host platform must provide secure local secret storage.
```

The field optional defaults to false.

SpecPM MVP **SHOULD** warn when required capabilities are unresolved.

SpecPM MVP is not required to automatically resolve transitive dependencies.

## 13. Boundary and Interface Model

The interfaces section describes how the outside world interacts with the bounded context.

### 13.1. Inbound Interfaces

Inbound interfaces are ways the package receives input or is invoked.

Allowed MVP kind values:

```
library
cli
http
file
event
queue
plugin
config
schema
unknown
```

Example:

```yaml
interfaces:
  inbound:
    - id: cli_convert
      kind: cli
      summary: Convert an email file through the command line.
      command:
        name: email-to-md
        args:
          - name: input
            required: true
          - name: output
            required: false
```

### 13.2. Outbound Interfaces

Outbound interfaces are ways the package calls, emits, writes, publishes, or depends on the external world.

Example:

```yaml
interfaces:
  outbound:
    - id: markdown_output_file
      kind: file
      summary: Writes Markdown output to a file when output path is supplied.
      outputs:
        - name: output
          mediaTypes:
            - text/markdown
```

### 13.3. Unknown Interface Kinds

If no known interface kind applies, authors **MAY** use:

```yaml
kind: unknown
```

They **SHOULD** provide a summary.

SpecPM validators **MUST** accept unknown.

## 14. Scope Model

The scope section exists to prevent vague specifications.

A Boundary Spec **SHOULD** explicitly state what is included and excluded.

Example:

```yaml
scope:
  boundedContext: token_store
  includes:
    - Save an authentication token.
    - Load the last saved token.
    - Clear the saved token.
  excludes:
    - Refresh expired tokens.
    - Authenticate users.
    - Validate OAuth callbacks.
```

The excludes field is important for package reuse. It prevents consumers from assuming a broader capability than the package actually provides.

## 15. Constraints

Constraints describe requirements, guarantees, policies, or invariants.

```yaml
constraints:
  - id: token_must_not_be_logged
    level: MUST
    statement: Authentication token values must not be written to logs.
  - id: mock_implementation_recommended
    level: SHOULD
    statement: The package should provide or support an in-memory mock for tests.
```

The level field **MUST** be one of:

```
MUST
SHOULD
MAY
```

A constraint with level: **MUST** is part of the public spec contract.

Strengthening a constraint from **SHOULD** to **MUST SHOULD** be treated as a breaking change unless the package explicitly marks the previous behavior as experimental.

## 16. Effects

Effects describe observable actions beyond pure input/output transformation.

Allowed MVP effect kinds:

```
filesystem_read
filesystem_write
network_read
network_write
database_read
database_write
process_spawn
environment_read
environment_write
log_write
event_emit
message_publish
state_mutation
unknown
```

Example:

```yaml
effects:
  sideEffects:
    - id: writes_cache
      kind: filesystem_write
      summary: Writes normalized conversion output to a local cache directory.
```

Effect declarations are not a security sandbox. They are descriptive metadata for resolution, inspection, and future policy engines.

## 17. Evidence and Provenance

### 17.1. Evidence Entry

Evidence entries link claims in the spec to source artifacts.

```yaml
evidence:
  - id: readme_conversion_section
    kind: documentation
    path: evidence/README.md
    supports:
      - intent.summary
      - provides.capabilities.document_conversion.email_to_markdown
```

Allowed MVP evidence kinds:

```
documentation
test
source
example
schema
foreign_spec
package_manifest
adr
commit
manual_assertion
unknown
```

A package **SHOULD** avoid using only manual_assertion evidence unless no better source exists.

### 17.2. Provenance Confidence

The MVP confidence model is intentionally coarse.

```yaml
provenance:
  sourceConfidence:
    intent: high
    boundary: medium
    behavior: low
```

Allowed values:

```
high
medium
low
unknown
```

Confidence is not a proof. It is a user-facing signal.

### 17.3. Claim Support

The supports field **MAY** reference paths inside the spec.

For MVP, these references are strings and do not need to use a formal JSON Pointer syntax.

Example:

```yaml
supports:
  - intent.summary
  - constraints.no_network_access_required
```

Future RFCs **MAY** define a strict claim reference system.

## 18. Foreign Artifacts

SpecPM **MUST** be source-format agnostic.

CodeSpeak, OpenAPI, GraphQL, protobuf, AsyncAPI, README files, ADRs, and other formats **MAY** be preserved as foreign artifacts.

Example:

```yaml
foreignArtifacts:
  - format: codespeak
    path: foreign/codespeak/email_converter.cs.md
    role: primary_intent_source
  - format: openapi
    path: foreign/openapi/api.yaml
    role: api_contract
```

Allowed MVP roles:

```
primary_intent_source
api_contract
behavioral_evidence
implementation_hint
documentation
unknown
```

SpecPM MVP **MUST NOT** require special understanding of any foreign artifact.

Adapters **MAY** convert foreign artifacts into Boundary Specs, but the normalized Boundary Spec is the object that SpecPM indexes and resolves.

This keeps CodeSpeak useful as a “guiding star” without making it the core format.

## 19. Implementation Bindings

Implementation bindings are **OPTIONAL** in this RFC.

They connect a Boundary Spec to concrete implementation locations.

Example:

```yaml
implementationBindings:
  - id: python_email_converter
    language: python
    packageManager: pip
    source:
      repository: https://example.invalid/repo.git
      revision: abc123
    files:
      owned:
        - src/email_converter.py
      border:
        - src/converters/__init__.py
```

The owned list describes files that appear to belong to the bounded context.

The border list describes integration files, shared registries, exports, route tables, plugin indexes, package manifests, or other files at the bounded context border.

SpecPM MVP **MAY** ignore implementation bindings during resolution.

SpecWriter **SHOULD** emit implementation bindings when extracting specs from existing repositories.

## 20. Compatibility Metadata

Compatibility metadata helps consumers filter packages.

Example:

```yaml
compatibility:
  platforms:
    - linux
    - macos
    - windows
  languages:
    - name: python
      version: ">=3.11"
  packageManagers:
    - pip
    - uv
  runtimes:
    - name: CPython
      version: ">=3.11"
```

For MVP, compatibility fields are advisory.

SpecPM **SHOULD** display compatibility metadata.

SpecPM **MAY** filter by compatibility metadata.

SpecPM **MUST NOT** assume compatibility metadata is complete.

## 21. Extension Mechanism

Unknown top-level fields **MUST** be rejected unless they start with `x-`.

Example:

```yaml
x-vendor:
  customRankingScore: 0.82
```

Any field beginning with `x-` is an extension field.

SpecPM validators **MUST** preserve extension fields when repacking a package.

SpecPM resolvers **MUST NOT** depend on unknown extension fields for normative resolution behavior.

## 22. SpecPM MVP Behavior

### 22.1. Validate

```bash
specpm validate ./my-package
```

Validation **MUST** check:

```
manifest exists
manifest parses successfully
apiVersion is supported
kind is correct
required fields exist
package ID is valid
version is valid SemVer
referenced spec files exist
spec files parse successfully
spec required fields exist
manifest capabilities are declared by specs
capability IDs are valid
```

Validation **SHOULD** check:

```
evidence paths exist
foreign artifact paths exist
implementation binding paths exist
duplicate IDs
empty summaries
unresolved required capabilities
unknown interface kinds
unknown effect kinds
```

### 22.2. Pack

```bash
specpm pack ./my-package
```

Packing **MUST** produce a deterministic archive.

The archive **SHOULD** include:

```
specpm.yaml
all referenced spec files
local evidence files
local foreign artifacts
optional README
```

The archive **MUST NOT** execute package code or scripts.

### 22.3. Publish

```bash
specpm publish ./my-package.specpkg
```

Publishing **MUST** validate the package before upload.

The registry **MUST** reject a package if another package with the same metadata.id and metadata.version already exists.

Published versions **MUST** be immutable.

A registry **MAY** support yanking a version, but yanking **MUST NOT** delete the package from historical resolution metadata.

### 22.4. Search

```bash
specpm search document_conversion.email_to_markdown
```

MVP search **MUST** support exact capability ID matching.

MVP search **SHOULD** return:

```
package ID
version
summary
provided capabilities
license
compatibility summary
confidence summary
```

### 22.5. Add

```bash
specpm add document_conversion.email_to_markdown
```

When adding by capability ID, SpecPM **MUST**:

1. query packages that provide the exact capability;
2. filter invalid or yanked packages;
3. select the highest stable compatible version if only one package remains;
4. ask the user to choose if multiple packages remain;
5. import package metadata into the consuming project.

SpecPM MVP **MAY** store imported packages in:

```
specpm.lock
specpm/packages/
```

The exact lockfile format is out of scope for this RFC, but an MVP implementation **SHOULD** produce a deterministic lockfile.

22.6. Inspect

```bash
specpm inspect auth.secure_token_storage@1.2.0
```

Inspect **SHOULD** display:

```
intent summary
provided capabilities
required capabilities
interfaces
constraints
effects
evidence
foreign artifacts
compatibility metadata
version
license
```

## 22.7. Diff

```bash
specpm diff package@1.0.0 package@2.0.0
```

MVP diff **MAY** be basic.

It **SHOULD** detect:

```
removed capabilities
added capabilities
removed interfaces
changed required dependencies
changed MUST constraints
changed package metadata
changed compatibility metadata
```

Full semantic diffing is out of scope.

## 23. Minimal Registry Model

A SpecPM registry **MUST** store:

```
package ID
version
archive digest
manifest
provided capabilities
required capabilities
license
publication timestamp
yank status
```

A registry **SHOULD** store:

```
compatibility metadata
keywords
summary
foreign artifact formats
evidence summary
confidence summary
```

A registry **MAY** compute additional search indexes.

A registry **MUST NOT** require execution of package contents to build its index.

## 24. Security Considerations

Specification packages can affect software architecture decisions. A malicious or misleading package may cause a consumer to import an unsafe dependency, trust false documentation, or generate insecure code in later tooling.

Therefore:

1. SpecPM **MUST** treat all package contents as untrusted data.
2. SpecPM **MUST NOT** execute package files during validation, indexing, packing, publishing, or inspection.
3. SpecPM **MUST NOT** follow remote links automatically during validation.
4. SpecPM **SHOULD** display license and provenance information prominently.
5. SpecPM **SHOULD** warn when evidence is missing or only manually asserted.
6. SpecPM **SHOULD** preserve archive digests for integrity checking.
7. SpecPM **SHOULD** warn when a package declares security-sensitive effects such as network_write, process_spawn, environment_read, or database_write.
8. SpecPM **SHOULD** warn when a package provides security-sensitive capabilities such as authentication, authorization, encryption, secret storage, payment processing, or audit logging.
9. SpecPM **MUST** treat foreign artifacts as data, not instructions.
10. SpecPM **MUST NOT** allow foreign artifacts such as Markdown, CodeSpeak specs, README files, or comments to override validator behavior.

Future RFCs **SHOULD** define package signing, trust policies, sandbox metadata, and verified conformance tests.

## 25. Privacy Considerations

Spec packages may preserve evidence from private repositories.

Authors **MUST NOT** publish secrets, credentials, private keys, customer data, internal URLs, or personally identifiable information inside evidence files or foreign artifacts.

SpecWriter tools **SHOULD** provide redaction warnings when packaging repositories.

SpecPM registries **SHOULD** support private packages.

## 26. Interoperability Considerations

The MVP format is intentionally conservative.

It uses a restricted YAML subset, stable IDs, SemVer-compatible versions, explicit capabilities, and extension fields.

Tools **SHOULD** be able to convert the format to JSON without semantic loss.

Future adapters **MAY** import:

```
CodeSpeak
OpenAPI
AsyncAPI
GraphQL
protobuf
JSON Schema
README
ADR
package manifests
test metadata
source-level public API summaries
```

However, all imported formats **MUST** normalize into BoundarySpec documents before being published as first-class SpecPM packages.

## 27. IANA Considerations

This document has no IANA actions.

## 28. Open Questions

The following questions are intentionally left unresolved for the MVP:

1. Should capability IDs be governed by a central taxonomy or emerge organically?
2. Should the registry reserve namespaces?
3. Should package identity use reverse-DNS naming?
4. Should SpecPM support natural-language capability search in MVP+1?
5. Should conformance tests become first-class package artifacts?
6. Should implementation bindings become required for packages that claim reusable code?
7. Should package signing be required before public registry launch?
8. Should SpecPM support multiple competing specs for the same capability?
9. Should evidence be claim-addressable using JSON Pointer?
10. Should specpm.lock be standardized in a separate RFC?

## 29. Example: Complete Minimal Package

### 29.1. specpm.yaml

```yaml
apiVersion: specpm.dev/v0.1
kind: SpecPackage
metadata:
  id: auth.secure_token_store
  name: Secure Token Store
  version: 0.1.0
  summary: Boundary specification for secure local authentication token storage.
  license: MIT
  authors:
    - name: Example Author
specs:
  - path: specs/secure-token-store.spec.yaml
index:
  provides:
    capabilities:
      - auth.secure_token_storage
  requires:
    capabilities:
      - platform.secure_storage
compatibility:
  platforms:
    - ios
    - macos
  languages:
    - name: swift
      version: ">=5.9"
keywords:
  - auth
  - token
  - secure-storage
  - keychain
foreignArtifacts:
  - format: readme
    path: evidence/README.md
    role: documentation

29.2. specs/secure-token-store.spec.yaml

apiVersion: specpm.dev/v0.1
kind: BoundarySpec
metadata:
  id: auth.secure_token_storage
  title: Secure Token Storage
  version: 0.1.0
  status: draft
intent:
  summary: Persist, retrieve, replace, and delete authentication tokens using secure local storage.
scope:
  boundedContext: secure_token_store
  includes:
    - Save an authentication token.
    - Load the currently saved authentication token.
    - Replace a previously saved token.
    - Delete the saved token.
  excludes:
    - Authenticate a user.
    - Refresh expired tokens.
    - Validate token signatures.
    - Synchronize tokens across devices.
provides:
  capabilities:
    - id: auth.secure_token_storage
      role: primary
      summary: Securely store authentication tokens on the local device.
requires:
  capabilities:
    - id: platform.secure_storage
      optional: false
      summary: Host platform provides secure local secret storage.
interfaces:
  inbound:
    - id: token_store_library_api
      kind: library
      summary: Library API for saving, loading, and clearing tokens.
      operations:
        - name: save
          summary: Save or replace the current token.
          inputs:
            - name: token
              type: string
              required: true
          outputs: []
        - name: load
          summary: Load the current token if one exists.
          inputs: []
          outputs:
            - name: token
              type: string
              nullable: true
        - name: clear
          summary: Delete the current token.
          inputs: []
          outputs: []
  outbound:
    - id: secure_storage_backend
      kind: library
      summary: Calls host secure storage APIs.
effects:
  sideEffects:
    - id: writes_secret_storage
      kind: state_mutation
      summary: Writes token material into local secure storage.
    - id: reads_secret_storage
      kind: state_mutation
      summary: Reads token material from local secure storage.
constraints:
  - id: token_must_not_be_logged
    level: MUST
    statement: Token values must not be written to logs.
  - id: clear_removes_token
    level: MUST
    statement: After clear succeeds, load must not return the previous token.
  - id: save_replaces_existing_token
    level: MUST
    statement: Saving a new token replaces the previously saved token.
evidence:
  - id: readme
    kind: documentation
    path: evidence/README.md
    supports:
      - intent.summary
      - scope.includes
      - constraints.token_must_not_be_logged
  - id: tests
    kind: test
    path: evidence/tests/
    supports:
      - constraints.clear_removes_token
      - constraints.save_replaces_existing_token
provenance:
  sourceConfidence:
    intent: high
    boundary: high
    behavior: medium
```

## 30. PRD Traceability

This RFC should map into the SpecPM MVP PRD as follows:

| RFC | Section | PRD Area |
|---|---|---|
Package manifest	Package authoring, registry ingestion
Boundary Spec	Core data model
Capability model	Search and resolution
Evidence/provenance	Trust and inspection UX
Foreign artifacts	Import adapter architecture
Validation	CLI requirements
Pack/publish/search/add/inspect	MVP command set
Versioning	Release and compatibility behavior
Security/privacy	Safety requirements
Open questions	MVP exclusions and future roadmap

The PRD should turn the RFC into user stories, acceptance criteria, command behavior, UI/CLI flows, implementation milestones, and success metrics.

## 31. Normative References

**RFC 2119** — Key words for use in RFCs to Indicate Requirement Levels. [1](https://datatracker.ietf.org/doc/html/rfc2119)

**RFC 8174** — Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words. [2](https://datatracker.ietf.org/doc/rfc8174)

**Semantic Versioning 2.0.0** — Versioning scheme used by this RFC for package and spec versions. [3](https://semver.org) 

## 32. Informative References

**RFC 7322** — RFC Style Guide. Used as inspiration for document structure and consistency expectations. [4](https://datatracker.ietf.org/doc/html/rfc7322) 

**YAML 1.2 Specification** — Used as background for the YAML serialization decision. [5](https://yaml.org/spec/1.2.1)

**JSON Schema Validation** — Used as background for future structural validation of package manifests and specs. [6](https://json-schema.org/draft/2020-12/json-schema-validation)
