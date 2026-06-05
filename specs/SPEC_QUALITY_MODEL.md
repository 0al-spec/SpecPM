# Spec Quality Model

Scope: how SpecPM maintainers, package authors, and producer-backed proposal
reviewers evaluate the quality of a `SpecPackage` and its referenced
`BoundarySpec` documents.

This document is a review model, not a new runtime validator. Existing
`specpm validate`, producer-bundle preflight, CI checks, and maintainer review
remain the enforcement surfaces. The model gives reviewers shared vocabulary
for deciding whether a package is merely valid, safe as a preview, useful to
downstream consumers, or ready for stronger acceptance claims.

## Principles

Spec quality is measured by whether the package is:

- valid under the current SpecPM schema and authoring rules;
- traceable from claims to evidence;
- bounded so it does not overclaim behavior, endorsement, authority, or runtime
  guarantees;
- useful to downstream consumers that need exact capabilities, interfaces,
  compatibility, and exclusions;
- reproducible from pinned sources, declared configuration, and recorded
  digests;
- reviewable without running package code, package scripts, producer tools,
  prompts, or analyzers inside SpecPM.

Prose polish is secondary. A well-written package that makes unsupported claims
is lower quality than a plain package that is valid, traceable, and explicit
about its limits.

## Quality Dimensions

### Validation

Validation is the entry gate:

```bash
specpm validate <package-dir> --json
```

A package should have:

- `error_count == 0`;
- referenced spec paths that exist;
- manifest capabilities backed by referenced BoundarySpecs;
- stable package, capability, interface, evidence, and constraint IDs;
- warnings that are expected, reviewed, and documented when they are retained.

Validation is necessary but not sufficient. A package can validate and still be
low quality if it is shallow, producer-centric, or weakly evidenced.

### Evidence Coverage

Every meaningful claim should be supported by evidence. Reviewers should check
at least these claim classes:

- package identity and provenance;
- capability IDs and capability summaries;
- intent IDs and capability-to-intent mappings;
- interfaces and interface outputs;
- compatibility platforms and languages;
- effects and side effects;
- constraints and exclusions;
- implementation bindings or foreign artifacts when present.

A practical coverage ratio is:

```text
evidence_coverage = supported_claim_count / total_reviewable_claim_count
```

SpecPM does not currently compute this ratio automatically. Reviewers may use it
as a manual review heuristic until a future report or lint command implements a
machine-readable score.

Generated or producer-backed candidates should be especially explicit about
which claims are supported by deterministic artifacts such as:

- `harvest.json`;
- package manifests and export maps;
- `public-interface-index.json`;
- analyzer reports;
- source digests;
- producer receipts and validation reports;
- maintainer review records.

Producer receipts and model review notes are evidence records. They are not
registry authority.

### Boundary Discipline

High-quality specs do not claim more than their evidence supports. A package
should explicitly avoid:

- upstream maintainer endorsement unless the upstream maintainer provided it;
- runtime behavior claims inferred only from package metadata;
- platform guarantees inferred only from ecosystem packaging;
- install, build, test, or script behavior unless that behavior is evidenced;
- package selection, semantic intent resolution, agent execution, or registry
  acceptance authority unless the package actually owns that boundary.

Generated candidates should normally use `preview_only: true` until maintainer
review records acceptance or an explicit override.

### Subject Usefulness

A package should describe the subject package, contract, or subsystem rather
than primarily describing the producer process.

Weak subject summary:

```text
Generated SpecPackage for public package metadata.
```

Stronger subject summary:

```text
xyflow provides React and Svelte libraries plus shared system utilities for
node-based editors and flow diagram interfaces.
```

Producer provenance still belongs in provenance, receipts, diagnostics, and PR
evidence. The main package summary and BoundarySpec intent should help a
downstream reader understand what the subject provides and what is not
guaranteed.

### Interface Depth

Spec quality improves as interfaces become more precise and better evidenced.

Suggested interface depth levels:

```text
L0: package identity only
L1: package manifests, descriptions, licenses, and export hints
L2: public interface indexes, symbols, entrypoints, or export maps
L3: grouped APIs, examples, constraints, and compatibility evidence
L4: behavior contracts backed by tests, upstream docs, or maintained examples
```

Many generated public package candidates will start at L1. The next quality
target should usually be L2: deterministic public interface evidence without
executing repository code.

### Reproducibility

High-quality specs can be regenerated or audited from pinned inputs.

Reviewers should look for:

- exact source revisions;
- stable package and capability IDs;
- stable producer configuration digests when generated;
- output file hashes in producer receipts;
- deterministic public index generation;
- small, explainable diffs between proposal versions.

For generated candidates, a changed source revision, changed producer
configuration, or changed analyzer output should be visible in the proposal
evidence.

### Consumer Utility

A downstream consumer should be able to answer:

- What capability does this package provide?
- Which interface should I expect?
- What is explicitly not guaranteed?
- Which evidence supports each major claim?
- Is the package accepted, preview-only, deprecated, rejected, or otherwise
  lifecycle-limited?
- Can this package be used for exact lookup without relying on semantic
  interpretation outside SpecPM?

If those answers are unclear, the package may be valid but not yet
consumer-useful.

## Quality Levels

SpecPM can use these non-normative maturity levels during review.

### L0. Valid YAML

The package parses, basic paths exist, and validation can run. This is not
enough for public acceptance.

### L1. Safe Preview

The package validates with no errors, has provenance, avoids overclaims, and
uses `preview_only` or equivalent review gating when generated or unreviewed.

Generated candidates such as initial SpecHarvester outputs should meet at least
this level before being proposed.

### L2. Evidence-Backed Preview

Capabilities, interfaces, compatibility, and major intent claims are linked to
deterministic evidence. Warnings are intentional and documented.

This is the target for robust producer-backed preview packages.

### L3. Consumer-Useful Contract

The package is subject-focused, has clear exclusions, interface depth is enough
for downstream exact lookup and comparison, and evidence coverage is high.

This is the preferred bar for broadly useful public registry entries.

### L4. Regression-Stable Contract

Quality checks are repeatable in CI or producer tooling. Regeneration, public
index output, archive metadata, and evidence digests remain stable except for
intentional source or contract changes.

### L5. Maintainer-Grade Accepted Contract

The package has maintainer review, strong evidence coverage, low ambiguity,
clear lifecycle status, and downstream consumers can rely on it as reviewed
registry metadata without trusting producer output as authority.

## Generated Candidate Review

Producer-backed candidates should be reviewed with two separate questions:

1. Is the bundle safe to review and accept as data?
2. Is the generated spec high enough quality for its intended lifecycle status?

A generated candidate can be acceptable as an L1 preview even when it is not yet
an L3 consumer-useful contract. Reviewers should keep this distinction explicit
in PR descriptions, acceptance decisions, and follow-up tasks.

For example, an initial harvested package may be acceptable when it:

- validates with no errors;
- is marked `preview_only`;
- records source revision and producer receipt evidence;
- avoids upstream endorsement and runtime behavior claims;
- represents observed package manifests accurately.

The same package should receive follow-up work when:

- summaries describe the producer more than the subject;
- `interfaces.inbound` are only package-manifest placeholders;
- compatibility claims are not tied to evidence;
- evidence `supports` entries cover broad capability claims but not interfaces
  or compatibility;
- model review notes are available but not separated from registry authority.

## Review Checklist

Before accepting a package or asking a producer for regeneration, reviewers can
use this checklist:

- Validation: `specpm validate <package-dir> --json` has no errors.
- Lifecycle: generated or unreviewed packages are `preview_only` or otherwise
  gated.
- Evidence: every major capability, interface, compatibility, and effect claim
  has a specific evidence path or documented gap.
- Boundary: exclusions prevent endorsement, runtime, install, script, and
  registry-authority overclaims.
- Subject focus: summary, intent, and scope describe the target package rather
  than only the producer.
- Interfaces: interface entries are specific enough for downstream exact lookup
  and comparison.
- Reproducibility: source revisions, producer config, output hashes, and
  validation reports are recorded when generated.
- Consumer utility: a downstream reader can identify what is provided, what is
  not guaranteed, and what evidence backs the claim.
- Model evidence: LM Studio or other model output is treated as bounded review
  evidence only, never as direct registry authority or direct file mutation.

## Future Automation

Future SpecPM or producer tooling may expose a machine-readable quality report
with fields such as:

```json
{
  "status": "warning",
  "level": "L2",
  "evidenceCoverage": {
    "supportedClaimCount": 18,
    "totalReviewableClaimCount": 23
  },
  "interfaceDepth": "L2",
  "overclaimFindings": [],
  "consumerUtilityFindings": [
    {
      "severity": "warning",
      "code": "compatibility_claim_not_evidence_backed",
      "field": "compatibility.platforms"
    }
  ]
}
```

Until such automation exists, this document is the shared manual review model.
