---
name: specpm-review-spec
description: Review and fix SpecPM package specifications. Use when Codex needs to audit `specpm.yaml`, `specs/*.spec.yaml`, self-spec coverage, BoundarySpec claims, capability/evidence consistency, validation failures, or review comments about SpecPM specs.
---

# SpecPM Review Spec

## Purpose

Review SpecPM specs as package contracts. Prioritize correctness,
traceability, boundary discipline, and validation stability over prose polish.

## Review Workflow

1. Establish scope.
   - Identify target package root, changed spec files, and related source/docs.
   - Preserve unrelated user changes.

2. Run or inspect validation first.
   - In SpecPM source checkouts:
     `PYTHONPATH=src python3 -m specpm.cli validate . --json`
   - Otherwise:
     `specpm validate <package-dir> --json`
   - Treat non-zero validation as the first fix target.

3. Check package/spec consistency.
   - `specpm.yaml` references existing spec paths.
   - Manifest `index.provides.capabilities` is a subset of capabilities
     declared by referenced BoundarySpecs.
   - Package ID, capability IDs, and SemVer are stable and valid.
   - Capability `intentIds`, when present, are package-neutral `intent.*` IDs
     and do not reuse provider or repository namespaces.
   - Authors, license, compatibility, and keywords match repository facts.

4. Check BoundarySpec quality.
   - Intent is specific and bounded.
   - Scope includes implemented or explicitly intended behavior only.
   - Excludes protect adjacent responsibilities and future tracks.
   - Interfaces, constraints, effects, evidence, provenance, and
     implementation bindings are grounded in files or docs.
   - Evidence `supports` targets resolve to real capabilities, constraints,
     effects, interfaces, implementation bindings, foreign artifacts, or
     allowed structural fields.
   - IDs are not reused ambiguously across evidence, constraints, interfaces,
     effects, implementation bindings, and foreign artifacts.
   - `kind: unknown` is justified or replaced with a specific known enum value.

5. Check boundary risks.
   - SpecPM must not become a PRD generator, artifact eval runtime, prompt
     executor, semantic resolver, remote mutation API, package installer, or
     package-content execution environment unless the task explicitly changes a
     post-MVP boundary document.
   - Package content remains untrusted data.

6. Fix narrowly.
   - Prefer minimal spec/docs edits over runtime changes.
   - If a PRD/Workplan gap is discovered, update those docs with the actual
     boundary and status.
   - Re-run validation and relevant tests after edits.
   - Check AI review suggestions against the current SpecPM schema and enum
     contract before applying them.

## Output Style

When reporting findings, list concrete issues first with file/field references.
For fixes, summarize changed files and validation commands actually run.

## References

Read `references/review-checklist.md` for a compact field-by-field review
checklist.
