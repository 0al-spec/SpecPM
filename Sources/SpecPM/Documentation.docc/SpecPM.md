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
- deterministic local add and lock metadata;
- local yank and unyank lifecycle state;
- structural diff;
- SpecGraph inbox inspection for `.specgraph_exports/` bundles;
- read-only remote registry metadata lookup;
- viewer-facing JSON contracts and portable conformance artifacts;
- experimental Agent Skills for authoring and reviewing SpecPM package specs.

SpecPM does not perform natural-language intent resolution, embedding
generation, vector search, RAG orchestration, or semantic package selection.
That layer belongs in ContextBuilder, SpecGraph, or a downstream resolver; SpecPM
verifies exact candidate IDs.

## Source Documents

The canonical source files remain in the repository:

- `README.md`
- `specs/PRD.md`
- `specs/WORKPLAN.md`
- `specs/JSON_CONTRACTS.md`
- `specs/CONFORMANCE.md`
- `specs/REMOTE_REGISTRY_API.md`
- `specs/INDEX_SUBMISSION_FLOW.md`
- `specs/DEPLOY_FIRST.md`
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
- <doc:PackageModel>
- <doc:CLIReference>

### Contracts

- <doc:JSONContracts>
- <doc:Conformance>
- <doc:SpecGraphIntegration>
- <doc:AgentSkills>

### Architecture

- <doc:BoundariesAndTrust>
- <doc:IntentDiscoveryBoundary>
- <doc:Deployment>
- <doc:Roadmap>
