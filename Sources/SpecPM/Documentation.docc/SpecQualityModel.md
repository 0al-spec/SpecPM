# Spec Quality Model

SpecPM uses a review model for deciding whether a `SpecPackage` is merely
valid, safe as preview data, useful to downstream consumers, or ready for
reviewed public registry acceptance.

The canonical contract is `specs/SPEC_QUALITY_MODEL.md`.

## Boundary

The quality model is documentation-level review guidance. It is not a new
runtime validator and it does not change `specpm validate`.

Existing validation, producer-bundle preflight, CI checks, and maintainer review
remain the enforcement surfaces.

## Review Dimensions

Reviewers evaluate:

- validation status;
- evidence coverage;
- boundary discipline;
- subject usefulness;
- interface depth;
- reproducibility;
- consumer utility.

## Levels

The model defines non-normative L0-L5 levels:

- L0 valid YAML;
- L1 safe preview;
- L2 evidence-backed preview;
- L3 consumer-useful contract;
- L4 regression-stable contract;
- L5 maintainer-grade accepted contract.

Generated candidates can be acceptable as safe preview data before they become
consumer-useful contracts. Producer receipts, validation reports, diagnostics,
preflight output, and model review notes are evidence records; maintainer review
and registry acceptance decisions remain the authority for public index
acceptance.
