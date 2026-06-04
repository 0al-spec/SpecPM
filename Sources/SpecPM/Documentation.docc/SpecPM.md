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
- `specs/DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.md`
- `specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md`
- `specs/REGISTRY_OBSERVATION_REPORTS.md`
- `specs/IDENTIFIER_MODEL.md`
- `specs/INTENT_TAXONOMY_GOVERNANCE.md`
- `specs/0002_Abstract_SpecPackage_Conformance_Target_Decision.md`
- `specs/0003_SpecPM_API_Versioning_Decision.md`
- `specs/INDEX_SUBMISSION_FLOW.md`
- `specs/PUBLIC_ALPHA.md`
- `specs/DEPLOY_FIRST.md`
- `specs/REGISTRY_OPERATIONS.md`
- `specs/GITHUB_ACTIONS_MAINTENANCE.md`
- `specs/GITHUB_ACTIONS_PERMISSIONS.md`
- `specs/REMOTE_PACKAGE_ACQUISITION.md`
- `specs/PACKAGE_SIGNING_REVOCATION.md`
- `specs/PROVENANCE_RECEIPTS.md`
- `specs/PRODUCER_RECEIPTS.md`
- `specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md`
- `specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md`
- `specs/REGISTRY_ACCEPTANCE_DECISIONS.md`
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
- <doc:DownstreamRegistryConsumers>
- <doc:SpecGraphRegistryObservation>
- <doc:RegistryObservationReports>
- <doc:AgentSkills>
- <doc:PublicAlphaRegistry>

### Architecture

- <doc:BoundariesAndTrust>
- <doc:IntentDiscoveryBoundary>
- <doc:IntentTaxonomyGovernance>
- <doc:Deployment>
- <doc:RegistryOperations>
- <doc:GitHubActionsMaintenance>
- <doc:GitHubActionsPermissions>
- <doc:RemotePackageAcquisition>
- <doc:PackageSigningRevocation>
- <doc:ProvenanceReceipts>
- <doc:ProducerReceipts>
- <doc:ProducerBundleProposalPolicy>
- <doc:ProducerBundleProposalAutomation>
- <doc:ProducerBundleFixturePolicy>
- <doc:RegistryAcceptanceDecisions>
- <doc:Roadmap>
