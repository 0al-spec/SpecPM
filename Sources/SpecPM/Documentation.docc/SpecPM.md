# ``SpecPM``

Local package management for reusable `SpecPackage` and `BoundarySpec` bundles.

## Overview

SpecPM is the package substrate for SpecGraph. It packages, validates, indexes,
inspects, preserves, and exposes reusable specification intent.

SpecPM does not own graph reasoning, artifact generation, prompt execution, or
artifact evaluation runtime. Package content is treated as untrusted data.

The local MVP supports:

- restricted YAML loading for `specpm.yaml` and `specs/*.spec.yaml`;
- validation of package shape, identifiers, versions, references, and paths;
- deterministic `.specpm.tgz` packing;
- local file-backed registry indexing;
- exact capability search;
- exact `intent.*` lookup over declared capability-to-intent mappings;
- observed intent catalog metadata from accepted packages;
- deterministic local add and lock metadata;
- local yank and unyank lifecycle state;
- structural diff;
- SpecGraph inbox inspection for `.specgraph_exports/` bundles;
- read-only remote registry metadata lookup;
- static public registry viewer for browsing the generated `/v0` API;
- viewer-facing JSON contracts and portable conformance artifacts;
- experimental Agent Skills for authoring and reviewing SpecPM package specs.

SpecPM does not perform natural-language intent resolution, embedding
generation, vector search, RAG orchestration, or semantic package selection.
That layer belongs in ContextBuilder, SpecGraph, or a downstream resolver.
SpecPM verifies exact candidate IDs and can expose exact `intent.*` mappings
declared by BoundarySpecs.

## Source Documents

The canonical source files remain in the repository:

- `README.md`
- `specs/PRD.md`
- `specs/WORKPLAN.md`
- `specs/JSON_CONTRACTS.md`
- `specs/CONFORMANCE.md`
- `specs/REMOTE_REGISTRY_API.md`
- `specs/IDENTIFIER_MODEL.md`
- `specs/INDEX_SUBMISSION_FLOW.md`
- `specs/PUBLIC_ALPHA.md`
- `specs/DEPLOY_FIRST.md`
- `specs/REGISTRY_OPERATIONS.md`
- `specs/RFC_0001_COVERAGE.md`
- `skills/README.md`
- `RFC/SpecGraph-RFC-0001.md`

This DocC site is a navigable documentation package built from those contracts.

## Boundary Statements

SpecPM may carry intent; SpecGraph decides meaning.

Package content can describe desired outputs. Package content cannot command the host.

## Topics

### Start Here

- <doc:GettingStarted>
- <doc:AddSpecPackage>
- <doc:StaticRegistryPipeline>
- <doc:IdentifierModel>
- <doc:PackageModel>
- <doc:CLIReference>

### Contracts

- <doc:JSONContracts>
- <doc:Conformance>
- <doc:SpecGraphIntegration>
- <doc:AgentSkills>
- <doc:PublicAlphaRegistry>

### Architecture

- <doc:BoundariesAndTrust>
- <doc:IntentDiscoveryBoundary>
- <doc:Deployment>
- <doc:RegistryOperations>
- <doc:Roadmap>
