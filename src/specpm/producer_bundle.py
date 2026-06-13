from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from specpm.index_submission import (
    append_accepted_manifest_sources,
    read_accepted_manifest_for_update,
)

PRODUCER_BUNDLE_PREFLIGHT_KIND = "SpecPMProducerBundlePreflightReport"
PRODUCER_BUNDLE_PREFLIGHT_SCHEMA_VERSION = 1
PACKAGE_SET_HANDOFF_API_VERSION = "spec-harvester.package-set-handoff-proposal/v0"
PACKAGE_SET_HANDOFF_KIND = "SpecHarvesterPackageSetHandoffProposal"
PACKAGE_SET_MATERIALIZATION_KIND = "SpecPMPackageSetMaterializationReport"
PACKAGE_SET_MATERIALIZATION_SCHEMA_VERSION = 1
PACKAGE_SET_AI_ENRICHMENT_API_VERSION = "spec-harvester.package-set-ai-enrichment/v0"
PACKAGE_SET_AI_ENRICHMENT_KIND = "SpecHarvesterPackageSetAIEnrichmentProposal"
PACKAGE_SET_AI_ENRICHMENT_PREFLIGHT_KIND = "SpecPMPackageSetAIEnrichmentPreflightReport"
PACKAGE_SET_AI_ENRICHMENT_PREFLIGHT_SCHEMA_VERSION = 1
PACKAGE_SET_AI_DRAFT_API_VERSION = "spec-harvester.package-set-ai-draft/v0"
PACKAGE_SET_AI_DRAFT_KIND = "SpecHarvesterPackageSetAIDraftProposal"
PACKAGE_SET_AI_DRAFT_PREFLIGHT_KIND = "SpecPMPackageSetAIDraftPreflightReport"
PACKAGE_SET_AI_DRAFT_PREFLIGHT_SCHEMA_VERSION = 1
REFRESH_DECISION_API_VERSION = "specpm.decisions/v0"
REFRESH_DECISION_KIND = "SpecPMGeneratedCandidateRefreshDecision"
REFRESH_DECISION_PREFLIGHT_KIND = "SpecPMGeneratedCandidateRefreshDecisionPreflightReport"
REFRESH_DECISION_PREFLIGHT_SCHEMA_VERSION = 1
REFRESH_DECISION_PREPARE_KIND = "SpecPMGeneratedCandidateRefreshDecisionPrepareReport"
REFRESH_DECISION_PREPARE_SCHEMA_VERSION = 1
BASELINE_SUBMISSION_HANDOFF_API_VERSION = "spec-harvester.baseline-submission-handoff/v0"
BASELINE_SUBMISSION_HANDOFF_KIND = "SpecHarvesterBaselineSubmissionHandoff"
BASELINE_SUBMISSION_HANDOFF_PREFLIGHT_KIND = "SpecPMBaselineSubmissionHandoffPreflightReport"
BASELINE_SUBMISSION_HANDOFF_PREFLIGHT_SCHEMA_VERSION = 1
SELECTED_CANDIDATE_HANDOFF_API_VERSION = "spec-harvester.selected-candidate-handoff-proposal/v0"
SELECTED_CANDIDATE_HANDOFF_KIND = "SpecHarvesterSelectedCandidateHandoffProposal"
REFRESHED_SELECTED_CANDIDATE_HANDOFF_API_VERSION = (
    "spec-harvester.refreshed-candidate-layer-selected-handoff/v0"
)
REFRESHED_SELECTED_CANDIDATE_HANDOFF_KIND = "SpecHarvesterRefreshedCandidateLayerSelectedHandoff"
SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_API_VERSION = "specpm.selected-candidate-handoff-preflight/v0"
SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_KIND = "SpecPMSelectedCandidateHandoffPreflightReport"
SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_SCHEMA_VERSION = 1
FRESH_CANDIDATE_REFRESH_RUN_API_VERSION = "spec-harvester.fresh-candidate-refresh-run/v0"
FRESH_CANDIDATE_REFRESH_RUN_KIND = "SpecHarvesterFreshCandidateRefreshRun"
MISSING_BASELINE_DIAGNOSTIC = "refresh_decision_prepare_current_contract_files_missing"

REQUIRED_PRODUCER_EVIDENCE_ROLES = {
    "accepted_source_bundle",
    "manifest",
    "boundary_spec",
    "producer_receipt",
    "validation_report",
    "diagnostics",
    "accepted_source_diff",
}
OPTIONAL_PRODUCER_EVIDENCE_ROLES = {"producer_preflight", "static_viewer"}
KNOWN_PATH_SCOPES = {"repo_relative", "candidate_bundle", "workflow_artifact", "pull_request"}
KNOWN_PACKAGE_SET_EVIDENCE_PATH_SCOPES = {
    "bundle_relative",
    "local_path",
    "repo_relative",
    "workflow_artifact",
}
REQUIRED_PACKAGE_SET_EVIDENCE_ROLES = {
    "package_set_draft",
    "package_relation_proposals",
    "package_relation_summary",
}
REQUIRED_MEMBER_EVIDENCE_ROLES = {
    "member_manifest",
    "member_boundary_spec",
    "member_producer_receipt",
    "member_validation_report",
    "member_diagnostics",
}
VALID_DECISION_STATUSES = {
    "external_required",
    "pending",
    "approved",
    "rejected",
    "override",
    "withdrawn",
}
VALID_REFRESH_DECISION_STATUSES = {
    "no_update_required",
    "curated_update_required",
    "new_generated_candidate_required",
    "new_package_version_required",
    "manual_review_required",
}
VALID_NO_UPDATE_REASONS = {
    "no_contract_delta",
}
VALID_REFRESH_SUPPORTING_REASONS = {
    "same_source_revision",
    "generated_contract_bytes_unchanged",
    "curated_artifact_remains_stronger",
    "producer_receipt_only_delta",
    "immutable_generated_candidate",
}
REFRESH_CONTRACT_DELTA_FLAGS = {
    "sourceRevisionChanged",
    "acceptedContractChanged",
    "generatedContractChanged",
    "capabilitiesChanged",
    "relationsChanged",
    "evidenceChanged",
}
VALID_BASELINE_HANDOFF_STATUSES = {"first_submission_required", "baseline_review_required"}
REQUIRED_BASELINE_HANDOFF_ACTIONS = {
    "first_submission_review",
    "seed_baseline",
    "reject_or_request_regeneration",
}
REQUIRED_BASELINE_HANDOFF_NON_GOALS = {
    "specpm_acceptance",
    "registry_publication",
    "baseline_mutation",
    "refresh_decision_emission",
    "source_repository_execution",
    "package_manager_execution",
}
REQUIRED_SELECTED_CANDIDATE_EVIDENCE_ROLES = {
    "candidate_bundle",
    "manifest",
    "boundary_spec",
    "producer_receipt",
    "validation_report",
    "diagnostics",
    "quality_report",
    "producer_preflight",
    "static_viewer",
    "static_viewer_payload",
    "selected_handoff_dry_run",
}
REQUIRED_REFRESHED_SELECTED_CANDIDATE_EVIDENCE_ROLES = {
    "manifest",
    "boundary_spec",
    "producer_receipt",
    "validation_report",
    "diagnostics",
    "quality_report",
}
REQUIRED_REFRESHED_SELECTED_CANDIDATE_MEMBER_EVIDENCE_ROLES = {
    "member_manifest",
    "member_producer_receipt",
    "member_validation_report",
    "member_diagnostics",
    "member_quality_report",
}
KNOWN_SELECTED_CANDIDATE_EVIDENCE_PATH_SCOPES = {
    "bundle_relative",
    "candidate_bundle",
    "local_path",
    "repo_relative",
    "workflow_artifact",
}
REQUIRED_REFRESHED_SELECTED_HANDOFF_NON_AUTHORITY_FLAGS = {
    "acceptsPackages": False,
    "acceptsRelations": False,
    "createsSpecPMPullRequest": False,
    "producerEvidenceOnly": True,
    "publishesRegistryMetadata": False,
    "removesPreviewOnly": False,
    "seedsBaselines": False,
    "treatsAIOutputAsRegistryTruth": False,
}
REQUIRED_LEGACY_SELECTED_HANDOFF_NON_AUTHORITY_PHRASES = {
    "not specpm registry acceptance",
    "does not accept packages",
    "does not accept relations",
    "does not seed baselines",
    "does not remove preview",
    "does not publish registry metadata",
    "does not create a specpm pull request",
}
AI_ENRICHMENT_REQUIRED_PRIVACY_FLAGS = {
    "rawPromptsPersisted",
    "rawModelResponsesPersisted",
    "chainOfThoughtPersisted",
    "secretsIncluded",
}
AI_ENRICHMENT_REQUIRED_NON_GOALS = {
    "specpm_acceptance",
    "package_acceptance",
    "relation_acceptance",
    "registry_publication",
}
AI_ENRICHMENT_ALLOWED_ARTIFACT_STATUSES = {"completed", "warning"}
AI_ENRICHMENT_PROPOSAL_STATUSES = {"proposed", "missing_model_output"}
AI_DRAFT_REQUIRED_NON_GOALS = {
    "deterministic_spec_generation",
    "specpm_acceptance",
    "package_acceptance",
    "relation_acceptance",
    "registry_publication",
    "model_authored_file_mutation",
}
AI_DRAFT_ALLOWED_ARTIFACT_STATUSES = {"completed", "warning"}
AI_DRAFT_MEMBER_ROLES = {
    "workspace",
    "primary_package",
    "published_package",
    "plugin_package",
    "cli_package",
    "platform_binary_package",
    "example_package",
    "fixture_package",
    "test_package",
    "private_tooling_package",
    "member_package",
}
AI_DRAFT_EXCLUSION_CATEGORIES = {
    "fixture",
    "test",
    "example",
    "private_tooling",
    "platform_artifact",
    "out_of_scope",
}
AI_DRAFT_INPUT_PATH_SCOPES = KNOWN_PACKAGE_SET_EVIDENCE_PATH_SCOPES | {"request_relative"}

JSON_FENCE_PATTERN = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)
SHA256_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def preflight_producer_bundle(body_path: Path, root: Path | None = None) -> dict[str, Any]:
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors = [
            issue(
                "producer_bundle_body_unreadable",
                f"Proposal body could not be read: {exc}.",
                field="body",
            )
        ]
        return {
            "kind": PRODUCER_BUNDLE_PREFLIGHT_KIND,
            "schemaVersion": PRODUCER_BUNDLE_PREFLIGHT_SCHEMA_VERSION,
            "status": "failed",
            "body": str(body_path),
            "root": str(root) if root else None,
            "summary": {
                "producerEvidenceRoleCount": 0,
                "packageSetHandoff": None,
                "errorCount": len(errors),
                "warningCount": 0,
            },
            "producerEvidenceRoles": [],
            "packageSetHandoff": None,
            "registryAcceptanceDecision": {
                "status": None,
                "recordKind": None,
                "producerReceiptAuthority": None,
                "producerAuthority": None,
            },
            "errors": errors,
            "warnings": [],
        }
    payloads = _extract_json_payloads(body)
    package_set_handoff = _find_package_set_handoff_payload(payloads)
    producer_links = _find_list_payload(payloads, "producerEvidenceLinks")
    registry_decision = _find_mapping_payload(payloads, "registryAcceptanceDecision")
    if registry_decision is None and isinstance(package_set_handoff, dict):
        registry_decision = _mapping_value(package_set_handoff.get("registryAcceptanceDecision"))

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if producer_links is None and package_set_handoff is None:
        errors.append(
            issue(
                "producer_evidence_links_missing",
                "Proposal body must include a JSON producerEvidenceLinks block.",
            )
        )
        producer_links = []
    if registry_decision is None:
        errors.append(
            issue(
                "registry_acceptance_decision_missing",
                "Proposal body must include a JSON registryAcceptanceDecision block.",
            )
        )
        registry_decision = {}

    role_map = {}
    if producer_links is not None:
        role_map = validate_producer_evidence_links(producer_links, errors, warnings, root)

    if package_set_handoff is None:
        validate_registry_acceptance_decision(registry_decision, errors, warnings)
        package_set_summary = None
    else:
        package_set_summary = validate_package_set_handoff(
            package_set_handoff,
            errors,
            warnings,
            root,
        )

    return {
        "kind": PRODUCER_BUNDLE_PREFLIGHT_KIND,
        "schemaVersion": PRODUCER_BUNDLE_PREFLIGHT_SCHEMA_VERSION,
        "status": "failed" if errors else ("warning" if warnings else "passed"),
        "body": str(body_path),
        "root": str(root) if root else None,
        "summary": {
            "producerEvidenceRoleCount": len(role_map),
            "packageSetHandoff": package_set_summary,
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "producerEvidenceRoles": sorted(role_map),
        "packageSetHandoff": package_set_summary,
        "registryAcceptanceDecision": {
            "status": registry_decision.get("status"),
            "recordKind": registry_decision.get("recordKind"),
            "producerReceiptAuthority": registry_decision.get("producerReceiptAuthority"),
            "producerAuthority": registry_decision.get("producerAuthority"),
        },
        "errors": errors,
        "warnings": warnings,
    }


def materialize_package_set_handoff(
    handoff_path: Path,
    root: Path,
    *,
    package_ids: list[str],
    relation_ids: list[str],
    output_root: Path,
    manifest_path: Path,
    apply_update: bool = False,
) -> dict[str, Any]:
    handoff = load_package_set_handoff(handoff_path)
    preflight = preflight_producer_bundle(handoff_path, root=root)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if not handoff:
        errors.append(
            issue(
                "package_set_handoff_missing",
                "Materialization requires a package-set handoff proposal JSON payload.",
                field="handoff",
            )
        )
    if preflight.get("status") != "passed":
        errors.append(
            issue(
                "package_set_preflight_not_passed",
                "Package-set materialization requires a passing SpecPM handoff preflight.",
                field="preflight.status",
            )
        )

    selected_package_ids = ordered_unique(package_ids)
    selected_relation_ids = ordered_unique(relation_ids)
    if not selected_package_ids:
        errors.append(
            issue(
                "package_set_materialization_packages_missing",
                "Maintainer-selected materialization requires at least one package ID.",
                field="selection.packageIds",
            )
        )

    members = _list_of_mappings(handoff.get("members"))
    relations = _list_of_mappings(handoff.get("relations"))
    member_by_id = {
        package_id: member
        for member in members
        if isinstance((package_id := member.get("packageId")), str) and package_id
    }
    relation_by_id = {
        relation_id: relation
        for relation in relations
        if isinstance((relation_id := relation.get("id")), str) and relation_id
    }

    for package_id in selected_package_ids:
        if package_id not in member_by_id:
            errors.append(
                issue(
                    "package_set_materialization_package_unknown",
                    f"Selected package ID is not present in the handoff: {package_id}.",
                    field="selection.packageIds",
                )
            )
    for relation_id in selected_relation_ids:
        if relation_id not in relation_by_id:
            errors.append(
                issue(
                    "package_set_materialization_relation_unknown",
                    f"Selected relation ID is not present in the handoff: {relation_id}.",
                    field="selection.relationIds",
                )
            )

    package_candidates = [
        build_package_materialization_candidate(
            package_id,
            member_by_id[package_id],
            root,
            output_root,
            errors,
        )
        for package_id in selected_package_ids
        if package_id in member_by_id
    ]
    selected_package_set = {candidate["package_id"] for candidate in package_candidates}
    relation_candidates = [
        build_relation_materialization_candidate(
            relation_id,
            relation_by_id[relation_id],
            selected_package_set,
            errors,
        )
        for relation_id in selected_relation_ids
        if relation_id in relation_by_id
    ]

    manifest = read_accepted_manifest_for_update(manifest_path)
    errors.extend(manifest["errors"])
    known_sources = list(manifest["sources"]) + read_local_accepted_manifest_sources(manifest_path)
    added_sources: list[dict[str, str]] = []
    skipped_sources: list[dict[str, Any]] = []
    planned_sources: list[dict[str, str]] = []
    for candidate in package_candidates:
        source = candidate.get("source")
        if not isinstance(source, dict):
            continue
        if any(same_materialized_source(source, known) for known in known_sources):
            candidate["manifestStatus"] = "skipped"
            skipped_sources.append(
                {
                    "reason": "exact_source_already_present",
                    "package_id": candidate["package_id"],
                    "version": candidate["version"],
                    "source": source,
                }
            )
            continue
        candidate["manifestStatus"] = "planned"
        known_sources.append(source)
        planned_sources.append(source)
        added_sources.append(source)

    if apply_update and not errors:
        for candidate in package_candidates:
            if candidate.get("manifestStatus") == "skipped":
                continue
            target_dir = Path(candidate["resolvedOutputPath"])
            if target_dir.exists():
                errors.append(
                    issue(
                        "package_set_materialization_output_exists",
                        "Accepted-source output already exists: "
                        f"{candidate['acceptedSourcePath']}.",
                        field="outputRoot",
                    )
                )
                continue

    if apply_update and not errors:
        for candidate in package_candidates:
            if candidate.get("manifestStatus") == "skipped":
                continue
            source_dir = Path(candidate["resolvedSourcePath"])
            target_dir = Path(candidate["resolvedOutputPath"])
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_dir, target_dir)
            candidate["copyStatus"] = "applied"
        if not errors and added_sources:
            append_accepted_manifest_sources(manifest_path, added_sources)

    if errors:
        status = "invalid"
    elif apply_update and added_sources:
        status = "applied"
    elif not added_sources:
        status = "unchanged"
    else:
        status = "prepared"

    return {
        "schemaVersion": PACKAGE_SET_MATERIALIZATION_SCHEMA_VERSION,
        "kind": PACKAGE_SET_MATERIALIZATION_KIND,
        "status": status,
        "applied": bool(apply_update and status == "applied"),
        "handoff": {
            "path": str(handoff_path),
            "packageSetId": _mapping_value(handoff.get("packageSet")).get("id"),
            "preflightStatus": preflight.get("status"),
        },
        "selection": {
            "packageIds": selected_package_ids,
            "relationIds": selected_relation_ids,
        },
        "outputRoot": str(output_root),
        "manifest": {
            "path": str(manifest_path),
            "candidate": {
                "schemaVersion": 1,
                "packages": planned_sources,
            },
        },
        "summary": {
            "selectedPackageCount": len(selected_package_ids),
            "selectedRelationCount": len(selected_relation_ids),
            "addedPackageCount": len(added_sources),
            "skippedPackageCount": len(skipped_sources),
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "packages": package_candidates,
        "relations": relation_candidates,
        "skipped": skipped_sources,
        "errors": errors,
        "warnings": warnings,
    }


def preflight_package_set_ai_enrichment(
    body_path: Path,
    *,
    root: Path | None = None,
    handoff_path: Path | None = None,
) -> dict[str, Any]:
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors = [
            issue(
                "ai_enrichment_body_unreadable",
                f"AI enrichment proposal could not be read: {exc}.",
                field="body",
            )
        ]
        return package_set_ai_enrichment_report(
            body_path,
            root,
            handoff_path,
            None,
            errors,
            [],
            None,
            "not_loaded",
        )

    payloads = _extract_json_payloads(body)
    enrichment = _find_package_set_ai_enrichment_payload(payloads)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if enrichment is None:
        errors.append(
            issue(
                "ai_enrichment_payload_missing",
                "Preflight requires a SpecHarvesterPackageSetAIEnrichmentProposal JSON payload.",
                field="body",
            )
        )
        return package_set_ai_enrichment_report(
            body_path,
            root,
            handoff_path,
            None,
            errors,
            warnings,
            None,
            "not_loaded",
        )

    handoff = load_package_set_handoff(handoff_path) if handoff_path is not None else {}
    handoff_member_ids = package_set_handoff_member_ids(handoff)
    package_alignment = "not_provided"
    if handoff_path is not None:
        if not handoff:
            errors.append(
                issue(
                    "ai_enrichment_handoff_missing",
                    "AI enrichment preflight could not read package-set handoff members.",
                    field="handoff",
                )
            )
            package_alignment = "failed"
        elif not handoff_member_ids:
            errors.append(
                issue(
                    "ai_enrichment_handoff_members_missing",
                    "AI enrichment preflight could not extract package IDs from "
                    "package-set handoff members.",
                    field="handoff.members",
                )
            )
            package_alignment = "failed"
        else:
            package_alignment = "verified"

    validate_package_set_ai_enrichment(
        enrichment,
        errors,
        warnings,
        root,
        handoff,
        handoff_member_ids,
    )
    if not handoff_member_ids and handoff_path is None:
        warnings.append(
            issue(
                "ai_enrichment_handoff_not_provided",
                "Package ID alignment against package-set handoff members was not verified.",
                field="handoff",
            )
        )

    return package_set_ai_enrichment_report(
        body_path,
        root,
        handoff_path,
        enrichment,
        errors,
        warnings,
        handoff_member_ids or None,
        package_alignment,
    )


def package_set_ai_enrichment_report(
    body_path: Path,
    root: Path | None,
    handoff_path: Path | None,
    enrichment: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    handoff_member_ids: set[str] | None,
    package_alignment: str,
) -> dict[str, Any]:
    proposals = _list_of_mappings(enrichment.get("proposals")) if enrichment else []
    inputs = _list_of_mappings(enrichment.get("inputs")) if enrichment else []
    allowed_paths = ai_enrichment_allowed_evidence_paths(enrichment or {})
    provider_receipt_count = sum(
        1 for proposal in proposals if isinstance(proposal.get("providerReceipt"), dict)
    )
    status = "failed" if errors else ("warning" if warnings else "passed")
    package_set = _mapping_value(enrichment.get("packageSet")) if enrichment else {}
    return {
        "kind": PACKAGE_SET_AI_ENRICHMENT_PREFLIGHT_KIND,
        "schemaVersion": PACKAGE_SET_AI_ENRICHMENT_PREFLIGHT_SCHEMA_VERSION,
        "status": status,
        "body": str(body_path),
        "root": str(root) if root else None,
        "handoff": str(handoff_path) if handoff_path else None,
        "packageSetAIEnrichment": (
            {
                "id": package_set.get("id"),
                "artifactStatus": enrichment.get("status"),
                "authority": enrichment.get("authority"),
                "proposalCount": len(proposals),
                "providerReceiptCount": provider_receipt_count,
                "packageAlignment": package_alignment,
                "handoffMemberCount": len(handoff_member_ids or set()),
            }
            if enrichment
            else None
        ),
        "summary": {
            "packageSetId": package_set.get("id"),
            "proposalCount": len(proposals),
            "inputCount": len(inputs),
            "allowedEvidencePathCount": len(allowed_paths),
            "providerReceiptCount": provider_receipt_count,
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }


def preflight_package_set_ai_draft(
    body_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors = [
            issue(
                "ai_draft_body_unreadable",
                f"AI draft proposal could not be read: {exc}.",
                field="body",
            )
        ]
        return package_set_ai_draft_report(
            body_path,
            root,
            None,
            errors,
            [],
            {},
            "not_loaded",
        )

    payloads = _extract_json_payloads(body)
    draft = _find_package_set_ai_draft_payload(payloads)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if draft is None:
        errors.append(
            issue(
                "ai_draft_payload_missing",
                "Preflight requires a SpecHarvesterPackageSetAIDraftProposal JSON payload.",
                field="body",
            )
        )
        return package_set_ai_draft_report(
            body_path,
            root,
            None,
            errors,
            warnings,
            {},
            "not_loaded",
        )

    if root is None:
        warnings.append(
            issue(
                "ai_draft_root_not_provided",
                "Workspace inventory file and digest alignment were not verified.",
                field="root",
            )
        )
    inventory = load_ai_draft_workspace_inventory(draft, root, errors, warnings)
    validate_package_set_ai_draft(draft, errors, warnings, root, inventory)
    inventory_alignment = ai_draft_inventory_alignment(root, inventory, errors)

    return package_set_ai_draft_report(
        body_path,
        root,
        draft,
        errors,
        warnings,
        inventory,
        inventory_alignment,
    )


def preflight_refresh_decision(
    body_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors = [
            issue(
                "refresh_decision_body_unreadable",
                f"Refresh decision could not be read: {exc}.",
                field="body",
            )
        ]
        return refresh_decision_report(body_path, root, None, errors, [], 0)

    payloads = _extract_json_payloads(body)
    decision = _find_refresh_decision_payload(payloads)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    digest_verified_count = 0
    if decision is None:
        errors.append(
            issue(
                "refresh_decision_payload_missing",
                "Preflight requires a SpecPMGeneratedCandidateRefreshDecision JSON payload.",
                field="body",
            )
        )
        return refresh_decision_report(body_path, root, None, errors, warnings, 0)

    if root is None:
        warnings.append(
            issue(
                "refresh_decision_root_not_provided",
                "Generated contract file existence and digest alignment were not verified.",
                field="root",
            )
        )

    digest_verified_count = validate_refresh_decision(decision, errors, warnings, root)
    return refresh_decision_report(
        body_path,
        root,
        decision,
        errors,
        warnings,
        digest_verified_count,
    )


def preflight_baseline_submission_handoff(
    body_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors = [
            issue(
                "baseline_handoff_body_unreadable",
                f"Baseline submission handoff could not be read: {exc}.",
                field="body",
            )
        ]
        return baseline_submission_handoff_report(
            body_path,
            root,
            None,
            errors,
            [],
            "not_loaded",
            0,
        )

    payloads = _extract_json_payloads(body)
    handoff = _find_baseline_submission_handoff_payload(payloads)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    input_alignment = "not_provided"
    digest_verified_count = 0
    if handoff is None:
        errors.append(
            issue(
                "baseline_handoff_payload_missing",
                "Preflight requires a SpecHarvesterBaselineSubmissionHandoff JSON payload.",
                field="body",
            )
        )
        return baseline_submission_handoff_report(
            body_path,
            root,
            None,
            errors,
            warnings,
            "not_loaded",
            0,
        )

    if root is None:
        warnings.append(
            issue(
                "baseline_handoff_root_not_provided",
                "Linked fresh-run and SpecPM prepare-report digests were not verified.",
                field="root",
            )
        )

    digest_verified_count = validate_baseline_submission_handoff(
        handoff,
        errors,
        warnings,
        root,
    )
    if root is None:
        input_alignment = "not_verified"
    elif any(
        isinstance(error.get("code"), str) and error["code"].startswith("baseline_handoff_input_")
        for error in errors
    ):
        input_alignment = "failed"
    else:
        input_alignment = "verified"
    return baseline_submission_handoff_report(
        body_path,
        root,
        handoff,
        errors,
        warnings,
        input_alignment,
        digest_verified_count,
    )


def preflight_selected_candidate_handoff(
    body_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors = [
            issue(
                "selected_handoff_body_unreadable",
                f"Selected candidate handoff could not be read: {exc}.",
                field="body",
            )
        ]
        return selected_candidate_handoff_report(body_path, root, None, errors, [], 0)

    payloads = _extract_json_payloads(body)
    handoff = _find_selected_candidate_handoff_payload(payloads)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if handoff is None:
        errors.append(
            issue(
                "selected_handoff_payload_missing",
                "Preflight requires a SpecHarvester selected candidate handoff JSON payload.",
                field="body",
            )
        )
        return selected_candidate_handoff_report(body_path, root, None, errors, warnings, 0)

    if root is None:
        warnings.append(
            issue(
                "selected_handoff_root_not_provided",
                "Linked source fixture digests were not verified.",
                field="root",
            )
        )

    digest_verified_count = validate_selected_candidate_handoff(
        handoff,
        errors,
        warnings,
        root,
    )
    return selected_candidate_handoff_report(
        body_path,
        root,
        handoff,
        errors,
        warnings,
        digest_verified_count,
    )


def prepare_refresh_decision(
    *,
    root: Path,
    fresh_generated_root: Path,
    package_ids: list[str],
    version: str,
    source_revision: str,
    source_repository: str | None = None,
    package_id: str | None = None,
    scope: str = "package_set",
    current_generated_root: Path = Path("public-index/generated"),
    curated_root: Path = Path("public-index/curated"),
    run_label: str = "local-refresh-evaluation",
    review_location: str = "local-draft",
    decision_by: str = "SpecPM maintainer review",
    receipt_only_changed: bool = True,
    advisory_report_only_changed: bool = True,
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    root_resolved = root.resolve(strict=False)
    package_ids = [value for value in package_ids if isinstance(value, str) and value]
    subject_package_id = package_id or (package_ids[0] if package_ids else "")

    if not package_ids:
        errors.append(
            issue(
                "refresh_decision_prepare_packages_missing",
                "Prepare refresh decision requires at least one --package.",
                field="packageIds",
            )
        )
    if not non_empty_string(version):
        errors.append(
            issue(
                "refresh_decision_prepare_version_missing",
                "Prepare refresh decision requires --version.",
                field="version",
            )
        )
    if not non_empty_string(source_revision):
        errors.append(
            issue(
                "refresh_decision_prepare_source_revision_missing",
                "Prepare refresh decision requires --source-revision.",
                field="sourceRevision",
            )
        )

    accepted_artifacts: list[str] = []
    current_generated_artifacts: list[str] = []
    generated_contract_files: list[dict[str, Any]] = []
    generated_contract_changed = False
    accepted_contract_changed = False
    source_revision_changed = False
    source_revision_evidence_found = False

    for item_index, item_package_id in enumerate(package_ids):
        package_field = f"packageIds[{item_index}]"
        if not is_safe_relative_path(item_package_id) or "/" in item_package_id:
            errors.append(
                issue(
                    "refresh_decision_prepare_package_id_unsafe",
                    "Package IDs must be safe single path segments for generated refresh compare.",
                    field=package_field,
                )
            )
            continue

        current_package_dir = root_join(
            root_resolved,
            current_generated_root,
            item_package_id,
            version,
        )
        fresh_package_dir = root_join(root_resolved, fresh_generated_root, item_package_id, version)
        curated_package_dir = root_join(root_resolved, curated_root, item_package_id, version)
        current_artifact = repo_relative_path(root_resolved, current_package_dir)
        accepted_artifact = repo_relative_path(root_resolved, curated_package_dir)
        if current_artifact is None:
            errors.append(
                issue(
                    "refresh_decision_prepare_current_path_unresolved",
                    "Current generated package path must resolve within --root.",
                    field=package_field,
                )
            )
        else:
            current_generated_artifacts.append(current_artifact)
        if accepted_artifact is None:
            errors.append(
                issue(
                    "refresh_decision_prepare_curated_path_unresolved",
                    "Curated package path must resolve within --root.",
                    field=package_field,
                )
            )
        else:
            accepted_artifacts.append(accepted_artifact)

        if not curated_package_dir.is_dir():
            accepted_contract_changed = True
            warnings.append(
                issue(
                    "refresh_decision_prepare_curated_artifact_missing",
                    (
                        "Curated accepted artifact is missing: "
                        f"{accepted_artifact or curated_package_dir}."
                    ),
                    field=package_field,
                )
            )

        current_contract_candidates = (
            refresh_contract_files(current_package_dir) if current_artifact is not None else []
        )
        current_contracts: list[Path] = []
        for current_contract in current_contract_candidates:
            current_contract_repo_path = repo_relative_path(root_resolved, current_contract)
            if current_contract_repo_path is None:
                errors.append(
                    issue(
                        "refresh_decision_prepare_contract_file_path_unresolved",
                        "Current generated contract file must resolve within --root.",
                        field=package_field,
                    )
                )
                continue
            current_contracts.append(current_contract)
            generated_contract_files.append(
                {
                    "path": current_contract_repo_path,
                    "sha256": sha256_file(current_contract),
                }
            )
        fresh_contracts = refresh_contract_files(fresh_package_dir)
        if not current_contracts:
            errors.append(
                issue(
                    "refresh_decision_prepare_current_contract_files_missing",
                    (
                        "Current generated artifact has no contract files: "
                        f"{current_artifact or current_package_dir}."
                    ),
                    field=package_field,
                )
            )
        if not fresh_contracts:
            generated_contract_changed = True
            errors.append(
                issue(
                    "refresh_decision_prepare_fresh_contract_files_missing",
                    f"Fresh generated artifact has no contract files: {fresh_package_dir}.",
                    field=package_field,
                )
            )

        current_relative_paths = {
            path.relative_to(current_package_dir) for path in current_contracts
        }
        fresh_relative_paths = {path.relative_to(fresh_package_dir) for path in fresh_contracts}
        if current_relative_paths != fresh_relative_paths:
            generated_contract_changed = True
            warnings.append(
                issue(
                    "refresh_decision_prepare_contract_file_set_changed",
                    (
                        "Fresh generated contract-file set differs from the current "
                        "generated artifact."
                    ),
                    field=package_field,
                )
            )

        for current_contract in current_contracts:
            relative_contract = current_contract.relative_to(current_package_dir)
            fresh_contract = fresh_package_dir / relative_contract
            if (
                fresh_contract.is_file()
                and current_contract.read_bytes() != fresh_contract.read_bytes()
            ):
                generated_contract_changed = True

        current_source_revisions = source_revisions_from_contracts(current_contracts)
        if current_source_revisions:
            source_revision_evidence_found = True
        if current_source_revisions and any(
            value != source_revision for value in current_source_revisions
        ):
            source_revision_changed = True

    update_needed = bool(
        errors or generated_contract_changed or accepted_contract_changed or source_revision_changed
    )
    status = "manual_review_required" if update_needed else "no_update_required"
    reason = "refresh_prepare_requires_review" if update_needed else "no_contract_delta"
    supporting_reasons: list[str] = []
    if not update_needed:
        supporting_reasons = [
            "generated_contract_bytes_unchanged",
            "curated_artifact_remains_stronger",
            "immutable_generated_candidate",
        ]
        if source_revision_evidence_found:
            supporting_reasons.insert(0, "same_source_revision")
        if receipt_only_changed:
            insert_index = 3 if source_revision_evidence_found else 2
            supporting_reasons.insert(insert_index, "producer_receipt_only_delta")

    decision = {
        "apiVersion": REFRESH_DECISION_API_VERSION,
        "kind": REFRESH_DECISION_KIND,
        "schemaVersion": 1,
        "decisionId": refresh_decision_id(subject_package_id, version, source_revision, status),
        "requiredFor": ["public_index_refresh_evaluation"],
        "subject": {
            "packageId": subject_package_id,
            "version": version,
            "scope": scope,
            "packageIds": package_ids,
            "acceptedArtifacts": accepted_artifacts,
            "currentGeneratedArtifacts": current_generated_artifacts,
            "freshGeneratedRun": {
                "kind": "local_review_evidence",
                "label": run_label,
                "sourceRepository": source_repository or "",
                "sourceRevision": source_revision,
                "summary": refresh_decision_fresh_run_summary(update_needed),
            },
        },
        "decision": {
            "status": status,
            "updateNeeded": update_needed,
            "reason": reason,
            "supportingReasons": supporting_reasons,
        },
        "comparison": {
            "sourceRevisionChanged": source_revision_changed,
            "acceptedContractChanged": accepted_contract_changed,
            "generatedContractChanged": generated_contract_changed,
            "capabilitiesChanged": generated_contract_changed,
            "relationsChanged": generated_contract_changed,
            "evidenceChanged": generated_contract_changed,
            "receiptOnlyChanged": receipt_only_changed,
            "advisoryReportOnlyChanged": advisory_report_only_changed,
            "freshCandidateCount": len(package_ids),
        },
        "generatedContractFiles": generated_contract_files,
        "authority": {
            "producerEvidenceAuthority": "evidence_only",
            "registryAuthority": "maintainer_review_required",
            "noRegistryMutation": True,
        },
        "maintainerReview": {
            "decisionBy": decision_by,
            "reviewLocation": review_location,
            "summary": refresh_decision_review_summary(update_needed),
        },
    }
    preflight_errors: list[dict[str, Any]] = []
    preflight_warnings: list[dict[str, Any]] = []
    digest_verified_count = validate_refresh_decision(
        decision,
        preflight_errors,
        preflight_warnings,
        root_resolved,
    )
    return refresh_decision_prepare_report(
        root_resolved,
        fresh_generated_root,
        decision,
        errors,
        warnings,
        preflight_errors,
        preflight_warnings,
        digest_verified_count,
    )


def refresh_decision_prepare_report(
    root: Path,
    fresh_generated_root: Path,
    decision: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    preflight_errors: list[dict[str, Any]],
    preflight_warnings: list[dict[str, Any]],
    digest_verified_count: int,
) -> dict[str, Any]:
    subject = _mapping_value(decision.get("subject"))
    decision_payload = _mapping_value(decision.get("decision"))
    generated_contract_files = _list_of_mappings(decision.get("generatedContractFiles"))
    all_errors = errors + preflight_errors
    all_warnings = warnings + preflight_warnings
    status = "failed" if all_errors else ("warning" if all_warnings else "passed")
    return {
        "kind": REFRESH_DECISION_PREPARE_KIND,
        "schemaVersion": REFRESH_DECISION_PREPARE_SCHEMA_VERSION,
        "status": status,
        "root": str(root),
        "freshGeneratedRoot": str(fresh_generated_root),
        "refreshDecision": {
            "decisionId": decision.get("decisionId"),
            "packageId": subject.get("packageId"),
            "version": subject.get("version"),
            "status": decision_payload.get("status"),
            "updateNeeded": decision_payload.get("updateNeeded"),
            "reason": decision_payload.get("reason"),
            "packageCount": len(string_list(subject.get("packageIds"))),
            "generatedContractFileCount": len(generated_contract_files),
            "digestVerifiedCount": digest_verified_count,
        },
        "summary": {
            "packageId": subject.get("packageId"),
            "packageCount": len(string_list(subject.get("packageIds"))),
            "generatedContractFileCount": len(generated_contract_files),
            "digestVerifiedCount": digest_verified_count,
            "updateNeeded": decision_payload.get("updateNeeded"),
            "errorCount": len(all_errors),
            "warningCount": len(all_warnings),
        },
        "decision": decision,
        "preflight": {
            "kind": REFRESH_DECISION_PREFLIGHT_KIND,
            "status": (
                "failed" if preflight_errors else ("warning" if preflight_warnings else "passed")
            ),
            "digestVerifiedCount": digest_verified_count,
            "errorCount": len(preflight_errors),
            "warningCount": len(preflight_warnings),
            "errors": preflight_errors,
            "warnings": preflight_warnings,
        },
        "errors": all_errors,
        "warnings": all_warnings,
    }


def refresh_decision_report(
    body_path: Path,
    root: Path | None,
    decision: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    digest_verified_count: int,
) -> dict[str, Any]:
    subject = _mapping_value(decision.get("subject")) if decision else {}
    decision_payload = _mapping_value(decision.get("decision")) if decision else {}
    package_ids = string_list(subject.get("packageIds"))
    generated_contract_files = (
        _list_of_mappings(decision.get("generatedContractFiles")) if decision else []
    )
    status = "failed" if errors else ("warning" if warnings else "passed")
    return {
        "kind": REFRESH_DECISION_PREFLIGHT_KIND,
        "schemaVersion": REFRESH_DECISION_PREFLIGHT_SCHEMA_VERSION,
        "status": status,
        "body": str(body_path),
        "root": str(root) if root else None,
        "refreshDecision": (
            {
                "decisionId": decision.get("decisionId"),
                "packageId": subject.get("packageId"),
                "version": subject.get("version"),
                "status": decision_payload.get("status"),
                "updateNeeded": decision_payload.get("updateNeeded"),
                "reason": decision_payload.get("reason"),
                "packageCount": len(package_ids),
                "generatedContractFileCount": len(generated_contract_files),
                "digestVerifiedCount": digest_verified_count,
            }
            if decision
            else None
        ),
        "summary": {
            "packageId": subject.get("packageId"),
            "packageCount": len(package_ids),
            "generatedContractFileCount": len(generated_contract_files),
            "digestVerifiedCount": digest_verified_count,
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }


def baseline_submission_handoff_report(
    body_path: Path,
    root: Path | None,
    handoff: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    input_alignment: str,
    digest_verified_count: int,
) -> dict[str, Any]:
    package_set = _mapping_value(handoff.get("packageSet")) if handoff else {}
    prepare_report = _mapping_value(handoff.get("specpmPrepareReport")) if handoff else {}
    authority = _mapping_value(handoff.get("authority")) if handoff else {}
    member_ids = string_list(package_set.get("memberPackageIds"))
    status = "failed" if errors else ("warning" if warnings else "passed")
    return {
        "kind": BASELINE_SUBMISSION_HANDOFF_PREFLIGHT_KIND,
        "schemaVersion": BASELINE_SUBMISSION_HANDOFF_PREFLIGHT_SCHEMA_VERSION,
        "status": status,
        "body": str(body_path),
        "root": str(root) if root else None,
        "baselineSubmissionHandoff": (
            {
                "packageSetId": package_set.get("id"),
                "artifactStatus": handoff.get("status"),
                "reason": handoff.get("reason"),
                "candidateCount": package_set.get("candidateCount"),
                "memberPackageCount": len(member_ids),
                "contractFileCount": package_set.get("contractFileCount"),
                "missingBaselineDiagnosticCount": prepare_report.get(
                    "missingBaselineDiagnosticCount"
                ),
                "inputAlignment": input_alignment,
                "digestVerifiedCount": digest_verified_count,
                "notRefreshDecision": authority.get("notRefreshDecision"),
                "noRegistryMutation": authority.get("noRegistryMutation"),
            }
            if handoff
            else None
        ),
        "summary": {
            "packageSetId": package_set.get("id"),
            "candidateCount": package_set.get("candidateCount") if handoff else 0,
            "memberPackageCount": len(member_ids),
            "contractFileCount": package_set.get("contractFileCount") if handoff else 0,
            "missingBaselineDiagnosticCount": prepare_report.get(
                "missingBaselineDiagnosticCount", 0
            ),
            "digestVerifiedCount": digest_verified_count,
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }


def selected_candidate_handoff_report(
    body_path: Path,
    root: Path | None,
    handoff: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    digest_verified_count: int,
) -> dict[str, Any]:
    selected_candidates = _list_of_mappings(handoff.get("selectedCandidates")) if handoff else []
    deferred_candidates = _list_of_mappings(handoff.get("deferredCandidates")) if handoff else []
    required_roles = selected_handoff_required_roles(handoff) if handoff else set()
    status = "failed" if errors else ("warning" if warnings else "passed")
    return {
        "apiVersion": SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_API_VERSION,
        "kind": SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_KIND,
        "schemaVersion": SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_SCHEMA_VERSION,
        "status": status,
        "authority": "specpm_consumer_preflight",
        "body": str(body_path),
        "root": str(root) if root else None,
        "input": (
            {
                "apiVersion": handoff.get("apiVersion"),
                "kind": handoff.get("kind"),
                "authority": handoff.get("authority"),
            }
            if handoff
            else None
        ),
        "selectedCandidateHandoff": (
            {
                "selectedCandidateCount": len(selected_candidates),
                "deferredCandidateCount": len(deferred_candidates),
                "requiredEvidenceRoleCount": len(required_roles),
                "digestVerifiedCount": digest_verified_count,
                "selectedCandidateIds": [
                    candidate_id(candidate) for candidate in selected_candidates
                ],
                "deferredCandidateIds": [
                    candidate_id(candidate) for candidate in deferred_candidates
                ],
            }
            if handoff
            else None
        ),
        "summary": {
            "selectedCandidateCount": len(selected_candidates),
            "deferredCandidateCount": len(deferred_candidates),
            "requiredEvidenceRoleCount": len(required_roles),
            "digestVerifiedCount": digest_verified_count,
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "nonAuthority": {
            "preflightOnly": True,
            "acceptsPackages": False,
            "acceptsRelations": False,
            "seedsBaselines": False,
            "removesPreviewOnly": False,
            "publishesRegistryMetadata": False,
            "createsSpecPMPullRequest": False,
        },
        "errors": errors,
        "warnings": warnings,
    }


def package_set_ai_draft_report(
    body_path: Path,
    root: Path | None,
    draft: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    inventory: dict[str, Any],
    inventory_alignment: str,
) -> dict[str, Any]:
    selected_members = _list_of_mappings(draft.get("selectedMembers")) if draft else []
    excluded_packages = _list_of_mappings(draft.get("excludedPackages")) if draft else []
    relations = _list_of_mappings(draft.get("relations")) if draft else []
    inputs = _list_of_mappings(draft.get("inputs")) if draft else []
    allowed_paths = ai_draft_allowed_evidence_paths(draft or {})
    provider_receipt_count = 1 if draft and isinstance(draft.get("providerReceipt"), dict) else 0
    package_set = _mapping_value(draft.get("packageSet")) if draft else {}
    inventory_packages = workspace_inventory_package_records(inventory)
    status = "failed" if errors else ("warning" if warnings else "passed")
    return {
        "kind": PACKAGE_SET_AI_DRAFT_PREFLIGHT_KIND,
        "schemaVersion": PACKAGE_SET_AI_DRAFT_PREFLIGHT_SCHEMA_VERSION,
        "status": status,
        "body": str(body_path),
        "root": str(root) if root else None,
        "packageSetAIDraft": (
            {
                "id": package_set.get("packageId"),
                "artifactStatus": draft.get("status"),
                "authority": draft.get("authority"),
                "selectedMemberCount": len(selected_members),
                "excludedPackageCount": len(excluded_packages),
                "relationCount": len(relations),
                "providerReceiptCount": provider_receipt_count,
                "inventoryAlignment": inventory_alignment,
                "inventoryPackageCount": len(inventory_packages),
            }
            if draft
            else None
        ),
        "summary": {
            "packageSetId": package_set.get("packageId"),
            "selectedMemberCount": len(selected_members),
            "excludedPackageCount": len(excluded_packages),
            "relationCount": len(relations),
            "inputCount": len(inputs),
            "allowedEvidencePathCount": len(allowed_paths),
            "inventoryPackageCount": len(inventory_packages),
            "providerReceiptCount": provider_receipt_count,
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }


def validate_refresh_decision(
    decision: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> int:
    if decision.get("apiVersion") != REFRESH_DECISION_API_VERSION:
        errors.append(
            issue(
                "refresh_decision_api_version_invalid",
                f"Refresh decision apiVersion must be {REFRESH_DECISION_API_VERSION}.",
                field="apiVersion",
            )
        )
    if decision.get("kind") != REFRESH_DECISION_KIND:
        errors.append(
            issue(
                "refresh_decision_kind_invalid",
                f"Refresh decision kind must be {REFRESH_DECISION_KIND}.",
                field="kind",
            )
        )
    if decision.get("schemaVersion") != 1:
        errors.append(
            issue(
                "refresh_decision_schema_version_invalid",
                "Refresh decision schemaVersion must be 1.",
                field="schemaVersion",
            )
        )
    if not non_empty_string(decision.get("decisionId")):
        errors.append(
            issue(
                "refresh_decision_id_missing",
                "Refresh decision must include a stable decisionId.",
                field="decisionId",
            )
        )

    required_for = string_list(decision.get("requiredFor"))
    if "public_index_refresh_evaluation" not in required_for:
        errors.append(
            issue(
                "refresh_decision_required_for_missing",
                "Refresh decision requiredFor must include public_index_refresh_evaluation.",
                field="requiredFor",
            )
        )

    subject = _mapping_value(decision.get("subject"))
    validate_refresh_decision_subject(subject, errors)
    validate_refresh_decision_decision(_mapping_value(decision.get("decision")), errors)
    validate_refresh_decision_comparison(
        _mapping_value(decision.get("comparison")),
        _mapping_value(decision.get("decision")),
        errors,
    )
    validate_refresh_decision_authority(_mapping_value(decision.get("authority")), errors)
    validate_refresh_decision_review(_mapping_value(decision.get("maintainerReview")), errors)
    return validate_refresh_decision_contract_files(
        _list_of_mappings(decision.get("generatedContractFiles")),
        errors,
        warnings,
        root,
    )


def validate_refresh_decision_subject(
    subject: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    package_id = subject.get("packageId")
    if not non_empty_string(package_id):
        errors.append(
            issue(
                "refresh_decision_package_id_missing",
                "Refresh decision subject.packageId is required.",
                field="subject.packageId",
            )
        )
    if not non_empty_string(subject.get("version")):
        errors.append(
            issue(
                "refresh_decision_version_missing",
                "Refresh decision subject.version is required.",
                field="subject.version",
            )
        )

    package_ids = string_list(subject.get("packageIds"))
    if not package_ids:
        errors.append(
            issue(
                "refresh_decision_package_ids_missing",
                "Refresh decision subject.packageIds must list the evaluated packages.",
                field="subject.packageIds",
            )
        )
    elif non_empty_string(package_id) and package_id not in package_ids:
        errors.append(
            issue(
                "refresh_decision_package_id_not_listed",
                "Refresh decision subject.packageId must appear in subject.packageIds.",
                field="subject.packageIds",
            )
        )

    for field in ("acceptedArtifacts", "currentGeneratedArtifacts"):
        values = string_list(subject.get(field))
        if not values:
            errors.append(
                issue(
                    f"refresh_decision_{field}_missing",
                    f"Refresh decision subject.{field} must list repo-relative paths.",
                    field=f"subject.{field}",
                )
            )
        for index, path in enumerate(values):
            validate_refresh_relative_path(path, errors, f"subject.{field}[{index}]")

    fresh_run = _mapping_value(subject.get("freshGeneratedRun"))
    source_revision = fresh_run.get("sourceRevision")
    if not isinstance(source_revision, str) or not re.fullmatch(r"[a-f0-9]{40}", source_revision):
        errors.append(
            issue(
                "refresh_decision_source_revision_invalid",
                "Refresh decision freshGeneratedRun.sourceRevision must be a 40-character SHA.",
                field="subject.freshGeneratedRun.sourceRevision",
            )
        )


def validate_refresh_decision_decision(
    decision_payload: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    status = decision_payload.get("status")
    update_needed = decision_payload.get("updateNeeded")
    reason = decision_payload.get("reason")
    if status not in VALID_REFRESH_DECISION_STATUSES:
        errors.append(
            issue(
                "refresh_decision_status_invalid",
                "Refresh decision status must be a known refresh decision status.",
                field="decision.status",
            )
        )
        return
    if not isinstance(update_needed, bool):
        errors.append(
            issue(
                "refresh_decision_update_needed_invalid",
                "Refresh decision updateNeeded must be a boolean.",
                field="decision.updateNeeded",
            )
        )
    elif status == "no_update_required" and update_needed is not False:
        errors.append(
            issue(
                "refresh_decision_no_update_flag_invalid",
                "status no_update_required requires updateNeeded false.",
                field="decision.updateNeeded",
            )
        )
    elif status != "no_update_required" and update_needed is not True:
        errors.append(
            issue(
                "refresh_decision_update_required_flag_invalid",
                "Update-required statuses require updateNeeded true.",
                field="decision.updateNeeded",
            )
        )

    if status == "no_update_required" and reason not in VALID_NO_UPDATE_REASONS:
        errors.append(
            issue(
                "refresh_decision_no_update_reason_invalid",
                "status no_update_required requires reason no_contract_delta.",
                field="decision.reason",
            )
        )
    elif status != "no_update_required" and not non_empty_string(reason):
        errors.append(
            issue(
                "refresh_decision_reason_missing",
                "Update-required refresh decisions must include a reason.",
                field="decision.reason",
            )
        )

    supporting_reasons = string_list(decision_payload.get("supportingReasons"))
    if status == "no_update_required" and not supporting_reasons:
        errors.append(
            issue(
                "refresh_decision_supporting_reasons_missing",
                "No-update refresh decisions must include supportingReasons.",
                field="decision.supportingReasons",
            )
        )
    for index, supporting_reason in enumerate(supporting_reasons):
        if (
            status == "no_update_required"
            and supporting_reason not in VALID_REFRESH_SUPPORTING_REASONS
        ):
            errors.append(
                issue(
                    "refresh_decision_supporting_reason_unknown",
                    f"Unknown refresh decision supporting reason: {supporting_reason}.",
                    field=f"decision.supportingReasons[{index}]",
                )
            )


def validate_refresh_decision_comparison(
    comparison: dict[str, Any],
    decision_payload: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    no_update = decision_payload.get("status") == "no_update_required"
    for flag in sorted(REFRESH_CONTRACT_DELTA_FLAGS):
        value = comparison.get(flag)
        if not isinstance(value, bool):
            errors.append(
                issue(
                    "refresh_decision_comparison_flag_invalid",
                    f"Refresh decision comparison.{flag} must be boolean.",
                    field=f"comparison.{flag}",
                )
            )
        elif no_update and value is not False:
            errors.append(
                issue(
                    "refresh_decision_no_update_delta_flag_invalid",
                    f"No-update refresh decisions require comparison.{flag} false.",
                    field=f"comparison.{flag}",
                )
            )


def validate_refresh_decision_authority(
    authority: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if authority.get("producerEvidenceAuthority") != "evidence_only":
        errors.append(
            issue(
                "refresh_decision_producer_authority_invalid",
                "Refresh decision producerEvidenceAuthority must be evidence_only.",
                field="authority.producerEvidenceAuthority",
            )
        )
    if authority.get("registryAuthority") != "maintainer_review_required":
        errors.append(
            issue(
                "refresh_decision_registry_authority_invalid",
                "Refresh decision registryAuthority must be maintainer_review_required.",
                field="authority.registryAuthority",
            )
        )
    if authority.get("noRegistryMutation") is not True:
        errors.append(
            issue(
                "refresh_decision_registry_mutation_flag_invalid",
                "Refresh decision authority.noRegistryMutation must be true.",
                field="authority.noRegistryMutation",
            )
        )


def validate_refresh_decision_review(
    review: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    for field in ("decisionBy", "reviewLocation", "summary"):
        if not non_empty_string(review.get(field)):
            errors.append(
                issue(
                    "refresh_decision_review_field_missing",
                    f"Refresh decision maintainerReview.{field} is required.",
                    field=f"maintainerReview.{field}",
                )
            )


def validate_refresh_decision_contract_files(
    contract_files: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> int:
    if not contract_files:
        errors.append(
            issue(
                "refresh_decision_contract_files_missing",
                "Refresh decision must include generatedContractFiles.",
                field="generatedContractFiles",
            )
        )
        return 0

    seen_paths: set[str] = set()
    verified_count = 0
    for index, item in enumerate(contract_files):
        path = item.get("path")
        sha256 = item.get("sha256")
        field = f"generatedContractFiles[{index}]"
        if not isinstance(path, str) or not path:
            errors.append(
                issue(
                    "refresh_decision_contract_file_path_missing",
                    "Generated contract file entry must include path.",
                    field=f"{field}.path",
                )
            )
            continue
        validate_refresh_relative_path(path, errors, f"{field}.path")
        if path in seen_paths:
            errors.append(
                issue(
                    "refresh_decision_contract_file_duplicate",
                    f"Duplicate generated contract file path: {path}.",
                    field=f"{field}.path",
                )
            )
        seen_paths.add(path)

        if not isinstance(sha256, str) or not SHA256_HEX_PATTERN.fullmatch(sha256):
            errors.append(
                issue(
                    "refresh_decision_contract_file_digest_invalid",
                    "Generated contract file sha256 must be a lowercase hex SHA-256 digest.",
                    field=f"{field}.sha256",
                )
            )
            continue
        if root is not None and validate_refresh_contract_file_digest(
            root,
            path,
            sha256,
            errors,
            field,
        ):
            verified_count += 1

    if root is None and contract_files:
        warnings.append(
            issue(
                "refresh_decision_contract_file_digests_not_verified",
                "Generated contract file digests were not verified because --root was omitted.",
                field="generatedContractFiles",
            )
        )
    return verified_count


def validate_refresh_contract_file_digest(
    root: Path,
    path: str,
    sha256: str,
    errors: list[dict[str, Any]],
    field: str,
) -> bool:
    resolved = resolve_package_set_path(root, path)
    if resolved is None:
        errors.append(
            issue(
                "refresh_decision_contract_file_path_unresolved",
                "Generated contract file path must resolve within the provided root.",
                field=f"{field}.path",
            )
        )
        return False
    if not resolved.is_file():
        errors.append(
            issue(
                "refresh_decision_contract_file_missing",
                f"Generated contract file does not exist: {path}.",
                field=f"{field}.path",
            )
        )
        return False
    actual = sha256_file(resolved)
    if actual != sha256:
        errors.append(
            issue(
                "refresh_decision_contract_file_digest_mismatch",
                "Generated contract file digest does not match file bytes.",
                field=f"{field}.sha256",
            )
        )
        return False
    return True


def validate_selected_candidate_handoff(
    handoff: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> int:
    is_refreshed = handoff.get("kind") == REFRESHED_SELECTED_CANDIDATE_HANDOFF_KIND
    is_legacy = handoff.get("kind") == SELECTED_CANDIDATE_HANDOFF_KIND
    validate_selected_handoff_identity(handoff, errors)

    selected = _list_of_mappings(handoff.get("selectedCandidates"))
    deferred = _list_of_mappings(handoff.get("deferredCandidates"))
    required_roles = selected_handoff_required_roles(handoff)

    validate_selected_handoff_summary(handoff, selected, deferred, required_roles, errors)
    validate_selected_handoff_candidate_sets(selected, deferred, errors)
    validate_selected_handoff_non_authority(handoff, is_refreshed, errors)

    for index, candidate in enumerate(selected):
        validate_selected_candidate_record(
            candidate,
            index,
            required_roles,
            is_refreshed,
            errors,
            warnings,
        )
    for index, candidate in enumerate(deferred):
        validate_deferred_candidate_record(candidate, index, is_refreshed, errors)

    if is_refreshed:
        validate_refreshed_selected_handoff_consumer_gate(handoff, errors)
        validate_refreshed_cupertino_deferral(deferred, errors)
        return validate_refreshed_selected_handoff_sources(handoff, errors, root)

    if is_legacy:
        return validate_legacy_selected_handoff_source(handoff, selected, errors, root)

    return 0


def validate_selected_handoff_identity(
    handoff: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    identity = (handoff.get("apiVersion"), handoff.get("kind"))
    supported = {
        (SELECTED_CANDIDATE_HANDOFF_API_VERSION, SELECTED_CANDIDATE_HANDOFF_KIND),
        (
            REFRESHED_SELECTED_CANDIDATE_HANDOFF_API_VERSION,
            REFRESHED_SELECTED_CANDIDATE_HANDOFF_KIND,
        ),
    }
    if identity not in supported:
        errors.append(
            issue(
                "unsupported_handoff_identity",
                "Selected candidate handoff apiVersion/kind is not supported.",
                field="apiVersion",
            )
        )
    if handoff.get("schemaVersion") != 1:
        errors.append(
            issue(
                "unsupported_handoff_schema_version",
                "Selected candidate handoff schemaVersion must be 1.",
                field="schemaVersion",
            )
        )
    if handoff.get("authority") != "producer_preview_evidence_only":
        errors.append(
            issue(
                "unsupported_producer_authority",
                "Selected candidate handoff authority must be producer_preview_evidence_only.",
                field="authority",
            )
        )


def validate_selected_handoff_summary(
    handoff: dict[str, Any],
    selected: list[dict[str, Any]],
    deferred: list[dict[str, Any]],
    required_roles: set[str],
    errors: list[dict[str, Any]],
) -> None:
    summary = _mapping_value(handoff.get("summary"))
    if summary.get("selectedCandidateCount") != len(selected):
        errors.append(
            issue(
                "selected_candidate_count_mismatch",
                "summary.selectedCandidateCount must match selectedCandidates length.",
                field="summary.selectedCandidateCount",
            )
        )
    if summary.get("deferredCandidateCount") != len(deferred):
        errors.append(
            issue(
                "deferred_candidate_count_mismatch",
                "summary.deferredCandidateCount must match deferredCandidates length.",
                field="summary.deferredCandidateCount",
            )
        )
    if "requiredEvidenceRoleCount" in summary and summary.get("requiredEvidenceRoleCount") != len(
        required_roles
    ):
        errors.append(
            issue(
                "required_evidence_role_count_mismatch",
                "summary.requiredEvidenceRoleCount must match requiredEvidenceRoles length.",
                field="summary.requiredEvidenceRoleCount",
            )
        )
    if summary.get("specpmPullRequestCreated") is not False:
        errors.append(
            issue(
                "unexpected_specpm_pull_request",
                "Selected candidate handoff must not claim a SpecPM pull request was created.",
                field="summary.specpmPullRequestCreated",
            )
        )
    if summary.get("registryMutationCount") != 0:
        errors.append(
            issue(
                "unexpected_registry_mutation",
                "Selected candidate handoff must not claim registry mutation.",
                field="summary.registryMutationCount",
            )
        )
    if handoff.get("kind") == REFRESHED_SELECTED_CANDIDATE_HANDOFF_KIND:
        refreshed_count_checks = {
            "candidateLayerReviewRequiredCount": (
                len(selected),
                "candidate_layer_review_count_mismatch",
            ),
            "needsRegenerationCount": (len(deferred), "needs_regeneration_count_mismatch"),
            "producerPreflightPassedCount": (
                len(selected),
                "producer_preflight_passed_count_mismatch",
            ),
            "viewerOkCount": (len(selected), "viewer_ok_count_mismatch"),
        }
        for field_name, (expected, code) in refreshed_count_checks.items():
            if summary.get(field_name) != expected:
                errors.append(
                    issue(
                        code,
                        f"summary.{field_name} must match the refreshed selected handoff set.",
                        field=f"summary.{field_name}",
                    )
                )


def validate_selected_handoff_candidate_sets(
    selected: list[dict[str, Any]],
    deferred: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    selected_ids = [candidate_id(candidate) for candidate in selected]
    deferred_ids = [candidate_id(candidate) for candidate in deferred]
    for index, package_id in enumerate(selected_ids):
        if not package_id:
            errors.append(
                issue(
                    "selected_candidate_id_missing",
                    "Selected candidate id is required.",
                    field=f"selectedCandidates[{index}].id",
                )
            )
    for index, package_id in enumerate(deferred_ids):
        if not package_id:
            errors.append(
                issue(
                    "deferred_candidate_id_missing",
                    "Deferred candidate id is required.",
                    field=f"deferredCandidates[{index}].id",
                )
            )
    for duplicate in sorted(duplicates([value for value in selected_ids if value])):
        errors.append(
            issue(
                "duplicate_selected_candidate_id",
                f"Duplicate selected candidate id: {duplicate}.",
                field="selectedCandidates",
            )
        )
    for duplicate in sorted(duplicates([value for value in deferred_ids if value])):
        errors.append(
            issue(
                "duplicate_deferred_candidate_id",
                f"Duplicate deferred candidate id: {duplicate}.",
                field="deferredCandidates",
            )
        )
    overlap = sorted(set(selected_ids) & set(deferred_ids))
    if overlap:
        errors.append(
            issue(
                "deferred_candidate_selected",
                f"Deferred candidates must not also be selected: {', '.join(overlap)}.",
                field="deferredCandidates",
            )
        )


def validate_selected_candidate_record(
    candidate: dict[str, Any],
    index: int,
    required_roles: set[str],
    is_refreshed: bool,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    field = f"selectedCandidates[{index}]"
    package_id = candidate_id(candidate) or f"selected candidate {index}"
    if candidate.get("previewOnly") is not True:
        errors.append(
            issue(
                "selected_candidate_not_preview_only",
                f"{package_id} must remain previewOnly before maintainer acceptance.",
                field=f"{field}.previewOnly",
            )
        )

    preflight = _mapping_value(candidate.get("producerPreflight"))
    if preflight.get("status") != "passed":
        errors.append(
            issue(
                "producer_preflight_not_passed",
                f"{package_id} producer preflight must be passed.",
                field=f"{field}.producerPreflight.status",
            )
        )
    if preflight.get("warningCount") != 0:
        errors.append(
            issue(
                "producer_preflight_warning_count_nonzero",
                f"{package_id} producer preflight warningCount must be 0.",
                field=f"{field}.producerPreflight.warningCount",
            )
        )
    if preflight.get("errorCount") != 0:
        errors.append(
            issue(
                "producer_preflight_error_count_nonzero",
                f"{package_id} producer preflight errorCount must be 0.",
                field=f"{field}.producerPreflight.errorCount",
            )
        )

    viewer = _mapping_value(candidate.get("viewer") or candidate.get("staticViewer"))
    if viewer.get("status") != "ok":
        errors.append(
            issue(
                "static_viewer_not_ok",
                f"{package_id} static viewer status must be ok.",
                field=f"{field}.viewer.status",
            )
        )

    decision = _mapping_value(candidate.get("registryAcceptanceDecision"))
    validate_selected_candidate_registry_decision(decision, field, package_id, errors)
    validate_selected_candidate_triage(candidate, field, package_id, is_refreshed, errors)
    validate_selected_candidate_evidence(
        candidate,
        field,
        package_id,
        required_roles,
        is_refreshed,
        errors,
        warnings,
    )


def validate_selected_candidate_registry_decision(
    decision: dict[str, Any],
    field: str,
    package_id: str,
    errors: list[dict[str, Any]],
) -> None:
    if decision.get("status") != "external_required":
        errors.append(
            issue(
                "registry_acceptance_not_external_required",
                f"{package_id} registry acceptance status must be external_required.",
                field=f"{field}.registryAcceptanceDecision.status",
            )
        )
    if decision.get("producerAuthority") != "evidence_only":
        errors.append(
            issue(
                "registry_acceptance_producer_authority_invalid",
                f"{package_id} producer authority must remain evidence_only.",
                field=f"{field}.registryAcceptanceDecision.producerAuthority",
            )
        )
    required_for = decision.get("requiredFor")
    valid_required_for = required_for == "public_index_acceptance" or (
        isinstance(required_for, list) and "public_index_acceptance" in required_for
    )
    if not valid_required_for:
        errors.append(
            issue(
                "registry_acceptance_required_for_missing",
                f"{package_id} registry acceptance must be required for public_index_acceptance.",
                field=f"{field}.registryAcceptanceDecision.requiredFor",
            )
        )


def validate_selected_candidate_triage(
    candidate: dict[str, Any],
    field: str,
    package_id: str,
    is_refreshed: bool,
    errors: list[dict[str, Any]],
) -> None:
    if is_refreshed:
        decision = _mapping_value(candidate.get("candidateLayerDecision"))
        if decision.get("status") != "candidate_layer_review_required":
            errors.append(
                issue(
                    "selected_candidate_triage_status_invalid",
                    f"{package_id} must be candidate_layer_review_required.",
                    field=f"{field}.candidateLayerDecision.status",
                )
            )
        if decision.get("selectedHandoffEligible") is not True:
            errors.append(
                issue(
                    "selected_candidate_not_handoff_eligible",
                    f"{package_id} must be selectedHandoffEligible.",
                    field=f"{field}.candidateLayerDecision.selectedHandoffEligible",
                )
            )
        if candidate.get("handoffRecommendation") != "ready_for_specpm_dry_run_review":
            errors.append(
                issue(
                    "selected_candidate_maintainer_action_invalid",
                    f"{package_id} handoff recommendation must be review-oriented.",
                    field=f"{field}.handoffRecommendation",
                )
            )
        return

    if candidate.get("triageClassification") != "candidate_layer_review_required":
        errors.append(
            issue(
                "selected_candidate_triage_status_invalid",
                f"{package_id} must be candidate_layer_review_required.",
                field=f"{field}.triageClassification",
            )
        )
    maintainer_action = candidate.get("maintainerAction")
    if maintainer_action not in {"review_for_possible_specpm_intake"}:
        errors.append(
            issue(
                "selected_candidate_maintainer_action_invalid",
                f"{package_id} maintainerAction must be review-oriented.",
                field=f"{field}.maintainerAction",
            )
        )


def validate_selected_candidate_evidence(
    candidate: dict[str, Any],
    field: str,
    package_id: str,
    required_roles: set[str],
    is_refreshed: bool,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    if is_refreshed:
        role_map = evidence_role_map(
            _list_of_mappings(candidate.get("evidenceRoles")),
            field=f"{field}.evidenceRoles",
            errors=errors,
        )
        missing_roles = sorted(
            missing_refreshed_selected_candidate_evidence_roles(set(role_map), required_roles)
        )
        for role in missing_roles:
            errors.append(
                issue(
                    "missing_required_evidence_role",
                    f"{package_id} is missing required evidence role {role}.",
                    field=f"{field}.evidenceRoles",
                )
            )
        for role, entry in role_map.items():
            if selected_handoff_digest_value(entry.get("digest")) is None:
                errors.append(
                    issue(
                        "invalid_evidence_digest",
                        f"{package_id} evidence role {role} must include a SHA-256 digest.",
                        field=f"{field}.evidenceRoles.{role}.digest",
                    )
                )
        validate_optional_digest_field(
            _mapping_value(candidate.get("producerPreflight")).get("reportDigest"),
            f"{field}.producerPreflight.reportDigest",
            errors,
        )
        viewer = _mapping_value(candidate.get("viewer"))
        validate_optional_digest_field(
            viewer.get("indexDigest"),
            f"{field}.viewer.indexDigest",
            errors,
        )
        validate_optional_digest_field(
            viewer.get("specPackageDigest"),
            f"{field}.viewer.specPackageDigest",
            errors,
        )
        return

    links = _list_of_mappings(candidate.get("evidenceLinks"))
    role_map = evidence_role_map(links, field=f"{field}.evidenceLinks", errors=errors)
    missing_roles = sorted(required_roles - set(role_map))
    for role in missing_roles:
        errors.append(
            issue(
                "missing_required_evidence_role",
                f"{package_id} is missing required evidence role {role}.",
                field=f"{field}.evidenceLinks",
            )
        )
    for role, entry in role_map.items():
        path_scope = entry.get("pathScope")
        if path_scope not in KNOWN_SELECTED_CANDIDATE_EVIDENCE_PATH_SCOPES:
            errors.append(
                issue(
                    "unsupported_evidence_path_scope",
                    f"{package_id} evidence role {role} has unsupported pathScope.",
                    field=f"{field}.evidenceLinks.{role}.pathScope",
                )
            )
        digest = selected_handoff_digest_value(entry.get("digest"))
        if role == "selected_handoff_dry_run" and digest is None:
            errors.append(
                issue(
                    "missing_selected_handoff_dry_run_digest",
                    f"{package_id} selected_handoff_dry_run evidence must include a digest.",
                    field=f"{field}.evidenceLinks.{role}.digest",
                )
            )
        elif role != "candidate_bundle" and digest is None:
            errors.append(
                issue(
                    "invalid_evidence_digest",
                    f"{package_id} evidence role {role} must include a SHA-256 digest.",
                    field=f"{field}.evidenceLinks.{role}.digest",
                )
            )
        maybe_warn_historical_local_path(entry, role, field, warnings)


def validate_deferred_candidate_record(
    candidate: dict[str, Any],
    index: int,
    is_refreshed: bool,
    errors: list[dict[str, Any]],
) -> None:
    field = f"deferredCandidates[{index}]"
    package_id = candidate_id(candidate) or f"deferred candidate {index}"
    if is_refreshed:
        decision = _mapping_value(candidate.get("candidateLayerDecision"))
        if decision.get("selectedHandoffEligible") is not False:
            errors.append(
                issue(
                    "deferred_candidate_handoff_eligible",
                    f"{package_id} must not be selectedHandoffEligible.",
                    field=f"{field}.candidateLayerDecision.selectedHandoffEligible",
                )
            )
        if decision.get("status") not in {"needs_regeneration", "blocked", "not_for_intake"}:
            errors.append(
                issue(
                    "deferred_candidate_status_invalid",
                    f"{package_id} deferred status must block selected handoff.",
                    field=f"{field}.candidateLayerDecision.status",
                )
            )
        return

    if candidate.get("handoffStatus") != "excluded_from_selected_handoff":
        errors.append(
            issue(
                "deferred_candidate_handoff_status_invalid",
                f"{package_id} must remain excluded_from_selected_handoff.",
                field=f"{field}.handoffStatus",
            )
        )


def validate_selected_handoff_non_authority(
    handoff: dict[str, Any],
    is_refreshed: bool,
    errors: list[dict[str, Any]],
) -> None:
    if is_refreshed:
        flags = _mapping_value(handoff.get("nonAuthority"))
        for key, expected in REQUIRED_REFRESHED_SELECTED_HANDOFF_NON_AUTHORITY_FLAGS.items():
            if flags.get(key) != expected:
                code = (
                    "producer_claims_acceptance"
                    if key != "producerEvidenceOnly" and flags.get(key) is True
                    else "missing_non_authority_statement"
                )
                errors.append(
                    issue(
                        code,
                        f"Selected handoff nonAuthority.{key} must be {expected}.",
                        field=f"nonAuthority.{key}",
                    )
                )
        return

    statements = " ".join(string_list(handoff.get("nonAuthority"))).lower().replace("_", " ")
    for phrase in REQUIRED_LEGACY_SELECTED_HANDOFF_NON_AUTHORITY_PHRASES:
        if phrase not in statements:
            errors.append(
                issue(
                    "missing_non_authority_statement",
                    f"Selected handoff must state: {phrase}.",
                    field="nonAuthority",
                )
            )
    if "registry acceptance" in statements and "not specpm registry acceptance" not in statements:
        errors.append(
            issue(
                "producer_claims_registry_authority",
                "Selected handoff must not claim registry acceptance authority.",
                field="nonAuthority",
            )
        )


def validate_refreshed_selected_handoff_consumer_gate(
    handoff: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    gate = _mapping_value(handoff.get("expectedConsumerGate"))
    if (
        gate.get("repository") != "SpecPM"
        or gate.get("kind") != SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_KIND
        or gate.get("apiVersion") != SELECTED_CANDIDATE_HANDOFF_PREFLIGHT_API_VERSION
        or gate.get("status") != "required_before_acceptance"
        or gate.get("nextTask") != "P32-T6"
    ):
        errors.append(
            issue(
                "selected_handoff_expected_consumer_gate_invalid",
                "Refreshed selected handoff must point to the SpecPM P32-T6 preflight gate.",
                field="expectedConsumerGate",
            )
        )


def validate_refreshed_cupertino_deferral(
    deferred: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    cupertino = next(
        (candidate for candidate in deferred if candidate_id(candidate) == "cupertino.core"),
        None,
    )
    if cupertino is None:
        errors.append(
            issue(
                "cupertino_core_deferral_missing",
                "Refreshed selected handoff must keep cupertino.core deferred.",
                field="deferredCandidates",
            )
        )
        return
    if "refined_summary_missing" not in string_list(cupertino.get("blockers")):
        errors.append(
            issue(
                "cupertino_core_deferral_blocker_missing",
                "cupertino.core deferral must retain refined_summary_missing blocker.",
                field="deferredCandidates.cupertino.core.blockers",
            )
        )


def validate_refreshed_selected_handoff_sources(
    handoff: dict[str, Any],
    errors: list[dict[str, Any]],
    root: Path | None,
) -> int:
    sources = _list_of_mappings(handoff.get("sources"))
    if not sources:
        errors.append(
            issue(
                "selected_handoff_source_missing",
                "Refreshed selected handoff must link source fixtures.",
                field="sources",
            )
        )
        return 0
    digest_verified_count = 0
    for index, source in enumerate(sources):
        field = f"sources[{index}]"
        if source.get("status") != "source_fixture_committed":
            errors.append(
                issue(
                    "selected_handoff_source_status_invalid",
                    "Refreshed selected handoff source status must be source_fixture_committed.",
                    field=f"{field}.status",
                )
            )
        if not non_empty_string(source.get("path")):
            errors.append(
                issue(
                    "selected_handoff_source_missing",
                    "Refreshed selected handoff source path is required.",
                    field=f"{field}.path",
                )
            )
            continue
        if selected_handoff_digest_value(source.get("digest")) is None:
            errors.append(
                issue(
                    "selected_handoff_source_digest_missing",
                    "Refreshed selected handoff source digest is required.",
                    field=f"{field}.digest",
                )
            )
            continue
        if root is not None and verify_selected_handoff_source_digest(
            source,
            root,
            field,
            errors,
        ):
            digest_verified_count += 1
    return digest_verified_count


def validate_legacy_selected_handoff_source(
    handoff: dict[str, Any],
    selected: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    root: Path | None,
) -> int:
    source = _mapping_value(_mapping_value(handoff.get("source")).get("selectedDryRunFixture"))
    if not source:
        errors.append(
            issue(
                "selected_handoff_source_missing",
                "Selected candidate handoff must link source.selectedDryRunFixture.",
                field="source.selectedDryRunFixture",
            )
        )
        return 0
    if source.get("status") != "selected_handoff_dry_run_ready":
        errors.append(
            issue(
                "selected_handoff_source_status_invalid",
                "source.selectedDryRunFixture.status must be selected_handoff_dry_run_ready.",
                field="source.selectedDryRunFixture.status",
            )
        )
    source_digest = selected_handoff_digest_value(source.get("digest"))
    if source_digest is None:
        errors.append(
            issue(
                "selected_handoff_source_digest_missing",
                "source.selectedDryRunFixture.digest is required.",
                field="source.selectedDryRunFixture.digest",
            )
        )
    for index, candidate in enumerate(selected):
        for link in _list_of_mappings(candidate.get("evidenceLinks")):
            if link.get("role") == "selected_handoff_dry_run":
                link_digest = selected_handoff_digest_value(link.get("digest"))
                if (
                    source_digest is not None
                    and link_digest is not None
                    and link_digest != source_digest
                ):
                    errors.append(
                        issue(
                            "selected_handoff_source_digest_mismatch",
                            "selected_handoff_dry_run evidence digest must match source fixture.",
                            field=f"selectedCandidates[{index}].evidenceLinks",
                        )
                    )
    if (
        root is not None
        and source_digest is not None
        and verify_selected_handoff_source_digest(
            source,
            root,
            "source.selectedDryRunFixture",
            errors,
        )
    ):
        return 1
    return 0


def verify_selected_handoff_source_digest(
    source: dict[str, Any],
    root: Path,
    field: str,
    errors: list[dict[str, Any]],
) -> bool:
    path_value = source.get("path")
    if not isinstance(path_value, str) or not path_value:
        errors.append(
            issue(
                "selected_handoff_source_missing",
                "Selected handoff source path is required.",
                field=f"{field}.path",
            )
        )
        return False
    resolved = resolve_handoff_input_path(root, path_value)
    if resolved is None:
        errors.append(
            issue(
                "selected_handoff_source_path_unresolved",
                "Selected handoff source path must resolve within --root.",
                field=f"{field}.path",
            )
        )
        return False
    if not resolved.is_file():
        errors.append(
            issue(
                "selected_handoff_source_missing",
                f"Selected handoff source file is missing: {path_value}.",
                field=f"{field}.path",
            )
        )
        return False
    expected = selected_handoff_digest_value(source.get("digest"))
    if expected is None:
        errors.append(
            issue(
                "selected_handoff_source_digest_missing",
                "Selected handoff source digest is required.",
                field=f"{field}.digest",
            )
        )
        return False
    actual = f"sha256:{sha256_file(resolved)}"
    if actual != expected:
        errors.append(
            issue(
                "selected_handoff_source_digest_mismatch",
                "Selected handoff source digest does not match file bytes.",
                field=f"{field}.digest",
            )
        )
        return False
    return True


def selected_handoff_required_roles(handoff: dict[str, Any]) -> set[str]:
    if handoff.get("kind") == REFRESHED_SELECTED_CANDIDATE_HANDOFF_KIND:
        return set(REQUIRED_REFRESHED_SELECTED_CANDIDATE_EVIDENCE_ROLES)
    roles = {
        role
        for entry in _list_of_mappings(handoff.get("requiredEvidenceRoles"))
        if entry.get("required") is True and isinstance((role := entry.get("role")), str)
    }
    return roles or set(REQUIRED_SELECTED_CANDIDATE_EVIDENCE_ROLES)


def missing_refreshed_selected_candidate_evidence_roles(
    actual_roles: set[str],
    default_required_roles: set[str],
) -> set[str]:
    if default_required_roles <= actual_roles:
        return set()
    if REQUIRED_REFRESHED_SELECTED_CANDIDATE_MEMBER_EVIDENCE_ROLES <= actual_roles:
        return set()
    default_missing = default_required_roles - actual_roles
    member_missing = REQUIRED_REFRESHED_SELECTED_CANDIDATE_MEMBER_EVIDENCE_ROLES - actual_roles
    return default_missing if len(default_missing) <= len(member_missing) else member_missing


def evidence_role_map(
    entries: list[dict[str, Any]],
    *,
    field: str,
    errors: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    role_map: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        role = entry.get("role")
        if not isinstance(role, str) or not role:
            errors.append(
                issue(
                    "missing_required_evidence_role",
                    "Evidence entry role is required.",
                    field=f"{field}[{index}].role",
                )
            )
            continue
        if role in role_map:
            errors.append(
                issue(
                    "duplicate_evidence_role",
                    f"Duplicate evidence role: {role}.",
                    field=f"{field}[{index}].role",
                )
            )
            continue
        role_map[role] = entry
    return role_map


def validate_digest_field(
    value: Any,
    field: str,
    errors: list[dict[str, Any]],
) -> None:
    if selected_handoff_digest_value(value) is None:
        errors.append(
            issue(
                "invalid_evidence_digest",
                "Expected a SHA-256 digest.",
                field=field,
            )
        )


def validate_optional_digest_field(
    value: Any,
    field: str,
    errors: list[dict[str, Any]],
) -> None:
    if value is None:
        return
    validate_digest_field(value, field, errors)


def selected_handoff_digest_value(digest: Any) -> str | None:
    value = digest_value(digest)
    if value is None:
        return None
    hexdigest = value.removeprefix("sha256:")
    if SHA256_HEX_PATTERN.fullmatch(hexdigest):
        return value
    return None


def maybe_warn_historical_local_path(
    entry: dict[str, Any],
    role: str,
    field: str,
    warnings: list[dict[str, Any]],
) -> None:
    path = entry.get("path")
    if (
        entry.get("pathScope") == "local_path"
        and isinstance(path, str)
        and Path(path).is_absolute()
    ):
        warnings.append(
            issue(
                "historical_local_path_missing_nonfatal",
                f"Evidence role {role} uses a historical absolute local path.",
                field=f"{field}.evidenceLinks.{role}.path",
            )
        )


def candidate_id(candidate: dict[str, Any]) -> str | None:
    value = candidate.get("id") or candidate.get("packageId")
    return value if isinstance(value, str) and value else None


def duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    result: set[str] = set()
    for value in values:
        if value in seen:
            result.add(value)
        seen.add(value)
    return result


def validate_baseline_submission_handoff(
    handoff: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> int:
    if handoff.get("apiVersion") != BASELINE_SUBMISSION_HANDOFF_API_VERSION:
        errors.append(
            issue(
                "baseline_handoff_api_version_invalid",
                f"Baseline handoff apiVersion must be {BASELINE_SUBMISSION_HANDOFF_API_VERSION}.",
                field="apiVersion",
            )
        )
    if handoff.get("kind") != BASELINE_SUBMISSION_HANDOFF_KIND:
        errors.append(
            issue(
                "baseline_handoff_kind_invalid",
                f"Baseline handoff kind must be {BASELINE_SUBMISSION_HANDOFF_KIND}.",
                field="kind",
            )
        )
    if handoff.get("schemaVersion") != 1:
        errors.append(
            issue(
                "baseline_handoff_schema_version_invalid",
                "Baseline handoff schemaVersion must be 1.",
                field="schemaVersion",
            )
        )

    status = handoff.get("status")
    reason = handoff.get("reason")
    if status not in VALID_BASELINE_HANDOFF_STATUSES:
        errors.append(
            issue(
                "baseline_handoff_status_invalid",
                "Baseline handoff status must be first_submission_required or "
                "baseline_review_required.",
                field="status",
            )
        )
    if status == "first_submission_required" and reason != "missing_current_generated_baseline":
        errors.append(
            issue(
                "baseline_handoff_reason_invalid",
                "first_submission_required requires reason missing_current_generated_baseline.",
                field="reason",
            )
        )
    if status == "baseline_review_required" and reason != "specpm_prepare_report_not_provided":
        errors.append(
            issue(
                "baseline_handoff_reason_invalid",
                "baseline_review_required requires reason specpm_prepare_report_not_provided.",
                field="reason",
            )
        )

    validate_baseline_handoff_source(_mapping_value(handoff.get("source")), errors)
    package_set = _mapping_value(handoff.get("packageSet"))
    validate_baseline_handoff_package_set(package_set, errors)
    validate_baseline_handoff_prepare_report(
        _mapping_value(handoff.get("specpmPrepareReport")),
        status,
        errors,
        warnings,
    )
    validate_baseline_handoff_workflow(_mapping_value(handoff.get("baselineWorkflow")), errors)
    validate_baseline_handoff_authority(_mapping_value(handoff.get("authority")), errors)
    validate_baseline_handoff_non_goals(handoff.get("nonGoals"), errors)
    return validate_baseline_handoff_inputs(handoff, errors, warnings, root)


def validate_baseline_handoff_source(
    source: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if not non_empty_string(source.get("repository")):
        errors.append(
            issue(
                "baseline_handoff_source_repository_missing",
                "Baseline handoff source.repository is required.",
                field="source.repository",
            )
        )
    revision = source.get("revision")
    if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40}", revision):
        errors.append(
            issue(
                "baseline_handoff_source_revision_invalid",
                "Baseline handoff source.revision must be a 40-character commit SHA.",
                field="source.revision",
            )
        )


def validate_baseline_handoff_package_set(
    package_set: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    package_set_id = package_set.get("id")
    if not non_empty_string(package_set_id):
        errors.append(
            issue(
                "baseline_handoff_package_set_id_missing",
                "Baseline handoff packageSet.id is required.",
                field="packageSet.id",
            )
        )
    member_ids = string_list(package_set.get("memberPackageIds"))
    if not member_ids:
        errors.append(
            issue(
                "baseline_handoff_member_package_ids_missing",
                "Baseline handoff packageSet.memberPackageIds must list generated candidates.",
                field="packageSet.memberPackageIds",
            )
        )
    elif non_empty_string(package_set_id) and package_set_id not in member_ids:
        errors.append(
            issue(
                "baseline_handoff_package_set_id_not_listed",
                "Baseline handoff packageSet.id must appear in memberPackageIds.",
                field="packageSet.memberPackageIds",
            )
        )
    candidate_count = package_set.get("candidateCount")
    if candidate_count != len(member_ids):
        errors.append(
            issue(
                "baseline_handoff_candidate_count_mismatch",
                "Baseline handoff packageSet.candidateCount must match memberPackageIds length.",
                field="packageSet.candidateCount",
            )
        )
    contract_file_count = package_set.get("contractFileCount")
    if not isinstance(contract_file_count, int) or contract_file_count <= 0:
        errors.append(
            issue(
                "baseline_handoff_contract_file_count_invalid",
                "Baseline handoff packageSet.contractFileCount must be a positive integer.",
                field="packageSet.contractFileCount",
            )
        )
    elif member_ids and contract_file_count < len(member_ids):
        errors.append(
            issue(
                "baseline_handoff_contract_file_count_too_low",
                "Baseline handoff contractFileCount cannot be lower than candidate count.",
                field="packageSet.contractFileCount",
            )
        )


def validate_baseline_handoff_prepare_report(
    prepare_report: dict[str, Any],
    status: Any,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    report_status = prepare_report.get("status")
    count = prepare_report.get("missingBaselineDiagnosticCount")
    if prepare_report.get("diagnosticCode") != MISSING_BASELINE_DIAGNOSTIC:
        errors.append(
            issue(
                "baseline_handoff_diagnostic_code_invalid",
                f"Baseline handoff diagnosticCode must be {MISSING_BASELINE_DIAGNOSTIC}.",
                field="specpmPrepareReport.diagnosticCode",
            )
        )
    if status == "first_submission_required":
        if report_status != "missing_baseline":
            errors.append(
                issue(
                    "baseline_handoff_prepare_status_invalid",
                    "first_submission_required requires specpmPrepareReport.status "
                    "missing_baseline.",
                    field="specpmPrepareReport.status",
                )
            )
        if not isinstance(count, int) or count <= 0:
            errors.append(
                issue(
                    "baseline_handoff_missing_diagnostic_count_invalid",
                    "first_submission_required requires at least one missing-baseline diagnostic.",
                    field="specpmPrepareReport.missingBaselineDiagnosticCount",
                )
            )
    elif status == "baseline_review_required":
        if report_status != "not_provided":
            errors.append(
                issue(
                    "baseline_handoff_prepare_status_invalid",
                    "baseline_review_required requires specpmPrepareReport.status not_provided.",
                    field="specpmPrepareReport.status",
                )
            )
        if count not in (0, None):
            errors.append(
                issue(
                    "baseline_handoff_missing_diagnostic_count_invalid",
                    "baseline_review_required must not claim missing-baseline diagnostics.",
                    field="specpmPrepareReport.missingBaselineDiagnosticCount",
                )
            )
        warnings.append(
            issue(
                "baseline_handoff_prepare_report_not_provided",
                "SpecPM prepare-report diagnostics were not confirmed in this handoff.",
                field="specpmPrepareReport.status",
            )
        )


def validate_baseline_handoff_workflow(
    workflow: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if workflow.get("blockedRefreshDecision") is not True:
        errors.append(
            issue(
                "baseline_handoff_blocked_refresh_flag_invalid",
                "Baseline handoff must block refresh decisions until baseline review.",
                field="baselineWorkflow.blockedRefreshDecision",
            )
        )
    if workflow.get("requiredBefore") != "specpm_refresh_decision":
        errors.append(
            issue(
                "baseline_handoff_required_before_invalid",
                "Baseline handoff baselineWorkflow.requiredBefore must be specpm_refresh_decision.",
                field="baselineWorkflow.requiredBefore",
            )
        )
    action_ids = {
        action_id
        for action in _list_of_mappings(workflow.get("maintainerActions"))
        if isinstance((action_id := action.get("id")), str) and action_id
    }
    missing = REQUIRED_BASELINE_HANDOFF_ACTIONS - action_ids
    if missing:
        errors.append(
            issue(
                "baseline_handoff_maintainer_actions_missing",
                f"Baseline handoff maintainerActions must include {', '.join(sorted(missing))}.",
                field="baselineWorkflow.maintainerActions",
            )
        )


def validate_baseline_handoff_authority(
    authority: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if authority.get("producerEvidenceAuthority") != "evidence_only":
        errors.append(
            issue(
                "baseline_handoff_producer_authority_invalid",
                "Baseline handoff producerEvidenceAuthority must be evidence_only.",
                field="authority.producerEvidenceAuthority",
            )
        )
    if authority.get("registryAuthority") != "SpecPM maintainer review":
        errors.append(
            issue(
                "baseline_handoff_registry_authority_invalid",
                "Baseline handoff registryAuthority must be SpecPM maintainer review.",
                field="authority.registryAuthority",
            )
        )
    if authority.get("noRegistryMutation") is not True:
        errors.append(
            issue(
                "baseline_handoff_registry_mutation_flag_invalid",
                "Baseline handoff noRegistryMutation must be true.",
                field="authority.noRegistryMutation",
            )
        )
    if authority.get("notRefreshDecision") is not True:
        errors.append(
            issue(
                "baseline_handoff_not_refresh_decision_flag_invalid",
                "Baseline handoff notRefreshDecision must be true.",
                field="authority.notRefreshDecision",
            )
        )


def validate_baseline_handoff_non_goals(value: Any, errors: list[dict[str, Any]]) -> None:
    non_goals = set(string_list(value))
    missing = REQUIRED_BASELINE_HANDOFF_NON_GOALS - non_goals
    if missing:
        errors.append(
            issue(
                "baseline_handoff_non_goals_missing",
                f"Baseline handoff nonGoals must include {', '.join(sorted(missing))}.",
                field="nonGoals",
            )
        )


def validate_baseline_handoff_inputs(
    handoff: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> int:
    inputs = _mapping_value(handoff.get("inputs"))
    fresh_input = _mapping_value(inputs.get("freshCandidateRefreshRun"))
    prepare_input = _mapping_value(inputs.get("specpmPrepareReport"))
    prepare_report_summary = _mapping_value(handoff.get("specpmPrepareReport"))
    fresh_input_valid = False
    prepare_input_valid = False
    if not fresh_input:
        errors.append(
            issue(
                "baseline_handoff_fresh_run_input_missing",
                "Baseline handoff inputs.freshCandidateRefreshRun is required.",
                field="inputs.freshCandidateRefreshRun",
            )
        )
    else:
        fresh_input_valid = validate_baseline_handoff_input_reference(
            fresh_input,
            "inputs.freshCandidateRefreshRun",
            "fresh run",
            errors,
        )
    if fresh_input and fresh_input.get("apiVersion") != FRESH_CANDIDATE_REFRESH_RUN_API_VERSION:
        errors.append(
            issue(
                "baseline_handoff_fresh_run_api_version_invalid",
                f"Fresh run input apiVersion must be {FRESH_CANDIDATE_REFRESH_RUN_API_VERSION}.",
                field="inputs.freshCandidateRefreshRun.apiVersion",
            )
        )
    if fresh_input and fresh_input.get("kind") != FRESH_CANDIDATE_REFRESH_RUN_KIND:
        errors.append(
            issue(
                "baseline_handoff_fresh_run_kind_invalid",
                f"Fresh run input kind must be {FRESH_CANDIDATE_REFRESH_RUN_KIND}.",
                field="inputs.freshCandidateRefreshRun.kind",
            )
        )

    if prepare_report_summary.get("status") == "missing_baseline":
        if not prepare_input:
            errors.append(
                issue(
                    "baseline_handoff_prepare_report_input_missing",
                    "Missing-baseline handoff must link the SpecPM prepare report input.",
                    field="inputs.specpmPrepareReport",
                )
            )
        else:
            prepare_input_valid = validate_baseline_handoff_input_reference(
                prepare_input,
                "inputs.specpmPrepareReport",
                "SpecPM prepare report",
                errors,
            )
    elif prepare_input:
        warnings.append(
            issue(
                "baseline_handoff_prepare_report_input_unexpected",
                "baseline_review_required handoff should not link a SpecPM prepare report.",
                field="inputs.specpmPrepareReport",
            )
        )
        prepare_input_valid = validate_baseline_handoff_input_reference(
            prepare_input,
            "inputs.specpmPrepareReport",
            "SpecPM prepare report",
            errors,
        )

    digest_verified_count = 0
    if root is None:
        return digest_verified_count

    if fresh_input_valid:
        fresh_run = load_and_verify_baseline_handoff_input(
            fresh_input,
            root,
            "inputs.freshCandidateRefreshRun",
            "fresh run",
            errors,
        )
        if fresh_run is not None:
            digest_verified_count += 1
            validate_linked_fresh_candidate_refresh_run(
                fresh_run,
                _mapping_value(handoff.get("packageSet")),
                _mapping_value(handoff.get("source")),
                errors,
            )

    if prepare_report_summary.get("status") == "missing_baseline" and prepare_input_valid:
        prepare_report = load_and_verify_baseline_handoff_input(
            prepare_input,
            root,
            "inputs.specpmPrepareReport",
            "SpecPM prepare report",
            errors,
        )
        if prepare_report is not None:
            digest_verified_count += 1
            validate_linked_baseline_prepare_report(
                prepare_report,
                prepare_report_summary,
                errors,
            )
    return digest_verified_count


def validate_baseline_handoff_input_reference(
    input_record: dict[str, Any],
    field: str,
    label: str,
    errors: list[dict[str, Any]],
) -> bool:
    valid = True
    path_value = input_record.get("path")
    if not isinstance(path_value, str) or not path_value:
        valid = False
        errors.append(
            issue(
                "baseline_handoff_input_path_missing",
                f"Baseline handoff {label} input path is required.",
                field=f"{field}.path",
            )
        )
    if digest_value(input_record.get("digest")) is None:
        valid = False
        errors.append(
            issue(
                "baseline_handoff_input_digest_invalid",
                f"Baseline handoff {label} input must include a SHA-256 digest.",
                field=f"{field}.digest",
            )
        )
    return valid


def load_and_verify_baseline_handoff_input(
    input_record: dict[str, Any],
    root: Path,
    field: str,
    label: str,
    errors: list[dict[str, Any]],
) -> dict[str, Any] | None:
    path_value = input_record.get("path")
    if not isinstance(path_value, str) or not path_value:
        errors.append(
            issue(
                "baseline_handoff_input_path_missing",
                f"Baseline handoff {label} input path is required.",
                field=f"{field}.path",
            )
        )
        return None
    resolved = resolve_handoff_input_path(root, path_value)
    if resolved is None:
        errors.append(
            issue(
                "baseline_handoff_input_path_unresolved",
                f"Baseline handoff {label} input path must resolve within --root.",
                field=f"{field}.path",
            )
        )
        return None
    if not resolved.is_file():
        errors.append(
            issue(
                "baseline_handoff_input_file_missing",
                f"Baseline handoff {label} input file is missing: {path_value}.",
                field=f"{field}.path",
            )
        )
        return None
    expected = digest_value(input_record.get("digest"))
    if expected is None:
        errors.append(
            issue(
                "baseline_handoff_input_digest_invalid",
                f"Baseline handoff {label} input must include a SHA-256 digest.",
                field=f"{field}.digest",
            )
        )
        return None
    actual = f"sha256:{sha256_file(resolved)}"
    if expected != actual:
        errors.append(
            issue(
                "baseline_handoff_input_digest_mismatch",
                f"Baseline handoff {label} input digest does not match file bytes.",
                field=f"{field}.digest",
            )
        )
        return None
    try:
        loaded = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            issue(
                "baseline_handoff_input_unreadable",
                f"Baseline handoff {label} input could not be read as JSON: {exc}.",
                field=f"{field}.path",
            )
        )
        return None
    if not isinstance(loaded, dict):
        errors.append(
            issue(
                "baseline_handoff_input_invalid",
                f"Baseline handoff {label} input must be a JSON object.",
                field=f"{field}.path",
            )
        )
        return None
    return loaded


def validate_linked_fresh_candidate_refresh_run(
    fresh_run: dict[str, Any],
    package_set: dict[str, Any],
    source: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if fresh_run.get("apiVersion") != FRESH_CANDIDATE_REFRESH_RUN_API_VERSION:
        errors.append(
            issue(
                "baseline_handoff_input_fresh_run_api_version_invalid",
                "Linked fresh run apiVersion does not match the SpecHarvester contract.",
                field="inputs.freshCandidateRefreshRun",
            )
        )
    if fresh_run.get("kind") != FRESH_CANDIDATE_REFRESH_RUN_KIND:
        errors.append(
            issue(
                "baseline_handoff_input_fresh_run_kind_invalid",
                "Linked fresh run kind does not match the SpecHarvester contract.",
                field="inputs.freshCandidateRefreshRun",
            )
        )
    if fresh_run.get("schemaVersion") != 1:
        errors.append(
            issue(
                "baseline_handoff_input_fresh_run_schema_version_invalid",
                "Linked fresh run schemaVersion must be 1.",
                field="inputs.freshCandidateRefreshRun.schemaVersion",
            )
        )
    fresh_source = _mapping_value(fresh_run.get("source"))
    for key in ("repository", "revision"):
        if fresh_source.get(key) != source.get(key):
            errors.append(
                issue(
                    "baseline_handoff_input_fresh_run_source_mismatch",
                    f"Linked fresh run source.{key} must match handoff source.{key}.",
                    field=f"source.{key}",
                )
            )
    fresh_package_set = _mapping_value(fresh_run.get("packageSet"))
    if fresh_package_set.get("id") != package_set.get("id"):
        errors.append(
            issue(
                "baseline_handoff_input_fresh_run_package_set_mismatch",
                "Linked fresh run packageSet.id must match handoff packageSet.id.",
                field="packageSet.id",
            )
        )
    fresh_member_ids = string_list(fresh_package_set.get("memberPackageIds"))
    handoff_member_ids = string_list(package_set.get("memberPackageIds"))
    if fresh_member_ids != handoff_member_ids:
        errors.append(
            issue(
                "baseline_handoff_input_fresh_run_members_mismatch",
                "Linked fresh run packageSet.memberPackageIds must match the handoff.",
                field="packageSet.memberPackageIds",
            )
        )
    if fresh_package_set.get("candidateCount") != package_set.get("candidateCount"):
        errors.append(
            issue(
                "baseline_handoff_input_fresh_run_candidate_count_mismatch",
                "Linked fresh run candidateCount must match the handoff.",
                field="packageSet.candidateCount",
            )
        )
    packages = _list_of_mappings(fresh_run.get("packages"))
    contract_file_count = sum(
        len(_list_of_mappings(package.get("contractFiles"))) for package in packages
    )
    if contract_file_count != package_set.get("contractFileCount"):
        errors.append(
            issue(
                "baseline_handoff_input_fresh_run_contract_count_mismatch",
                "Linked fresh run contract file count must match the handoff.",
                field="packageSet.contractFileCount",
            )
        )


def validate_linked_baseline_prepare_report(
    prepare_report: dict[str, Any],
    summary: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if prepare_report.get("kind") != REFRESH_DECISION_PREPARE_KIND:
        errors.append(
            issue(
                "baseline_handoff_input_prepare_report_kind_invalid",
                f"Linked prepare report kind must be {REFRESH_DECISION_PREPARE_KIND}.",
                field="inputs.specpmPrepareReport.kind",
            )
        )
    if prepare_report.get("schemaVersion") != REFRESH_DECISION_PREPARE_SCHEMA_VERSION:
        errors.append(
            issue(
                "baseline_handoff_input_prepare_report_schema_version_invalid",
                "Linked prepare report schemaVersion must be 1.",
                field="inputs.specpmPrepareReport.schemaVersion",
            )
        )
    missing_errors = [
        item
        for item in _list_of_mappings(prepare_report.get("errors"))
        if item.get("code") == MISSING_BASELINE_DIAGNOSTIC
    ]
    if len(missing_errors) != summary.get("missingBaselineDiagnosticCount"):
        errors.append(
            issue(
                "baseline_handoff_input_prepare_report_diagnostic_count_mismatch",
                "Linked prepare report missing-baseline diagnostic count must match handoff.",
                field="specpmPrepareReport.missingBaselineDiagnosticCount",
            )
        )
    decision = _mapping_value(_mapping_value(prepare_report.get("decision")).get("decision"))
    if decision.get("status") != summary.get("decisionStatus"):
        errors.append(
            issue(
                "baseline_handoff_input_prepare_report_decision_status_mismatch",
                "Linked prepare report decision.status must match handoff summary.",
                field="specpmPrepareReport.decisionStatus",
            )
        )
    if decision.get("reason") != summary.get("decisionReason"):
        errors.append(
            issue(
                "baseline_handoff_input_prepare_report_decision_reason_mismatch",
                "Linked prepare report decision.reason must match handoff summary.",
                field="specpmPrepareReport.decisionReason",
            )
        )


def resolve_handoff_input_path(root: Path, path: str) -> Path | None:
    root_resolved = root.resolve(strict=False)
    raw = Path(path)
    candidate = (
        raw.resolve(strict=False)
        if raw.is_absolute()
        else (root_resolved / raw).resolve(strict=False)
    )
    if not candidate.is_relative_to(root_resolved):
        return None
    return candidate


def validate_refresh_relative_path(
    path: str,
    errors: list[dict[str, Any]],
    field: str,
) -> None:
    if not is_safe_relative_path(path):
        errors.append(
            issue(
                "refresh_decision_path_unsafe",
                "Refresh decision paths must be safe repo-relative paths.",
                field=field,
            )
        )


def load_package_set_handoff(path: Path) -> dict[str, Any]:
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    payloads = _extract_json_payloads(body)
    handoff = _find_package_set_handoff_payload(payloads)
    if handoff is None:
        return {}
    return handoff


def build_package_materialization_candidate(
    package_id: str,
    member: dict[str, Any],
    root: Path,
    output_root: Path,
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_path = member.get("candidatePath")
    if not isinstance(candidate_path, str) or not candidate_path:
        errors.append(
            issue(
                "package_set_materialization_candidate_path_missing",
                f"Selected package {package_id} does not declare candidatePath.",
                field="packageSetHandoff.members[].candidatePath",
            )
        )
        return {"package_id": package_id, "status": "invalid"}
    source_path = resolve_package_set_path(root, candidate_path)
    if source_path is None or not source_path.is_dir():
        errors.append(
            issue(
                "package_set_materialization_candidate_missing",
                f"Selected package {package_id} candidate directory is missing.",
                field="packageSetHandoff.members[].candidatePath",
            )
        )
        return {"package_id": package_id, "status": "invalid"}
    if candidate_tree_contains_symlink(source_path):
        errors.append(
            issue(
                "package_set_materialization_candidate_symlink",
                f"Selected package {package_id} candidate directory contains a symlink.",
                field="packageSetHandoff.members[].candidatePath",
            )
        )

    manifest_path = source_path / "specpm.yaml"
    metadata = read_manifest_metadata(manifest_path, errors, package_id)
    version = metadata.get("version") or "unknown"
    if metadata.get("package_id") != package_id:
        errors.append(
            issue(
                "package_set_materialization_manifest_id_mismatch",
                f"Selected package {package_id} manifest identity is {metadata.get('package_id')}.",
                field="specpm.yaml.metadata.id",
            )
        )
    if version == "unknown":
        errors.append(
            issue(
                "package_set_materialization_manifest_version_missing",
                f"Selected package {package_id} manifest metadata.version is missing.",
                field="specpm.yaml.metadata.version",
            )
        )

    safe_output = package_output_path(output_root, package_id, version, errors)
    source = {"path": safe_output.as_posix()}
    return {
        "package_id": package_id,
        "version": version,
        "sourcePath": candidate_path,
        "resolvedSourcePath": str(source_path),
        "acceptedSourcePath": safe_output.as_posix(),
        "resolvedOutputPath": str(safe_output),
        "source": source,
        "copyStatus": "planned",
        "manifestStatus": "planned",
    }


def build_relation_materialization_candidate(
    relation_id: str,
    relation: dict[str, Any],
    selected_package_ids: set[str],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    source_id = _mapping_value(relation.get("source")).get("packageId")
    target_id = _mapping_value(relation.get("target")).get("packageId")
    relation_type = relation.get("type")
    if source_id not in selected_package_ids or target_id not in selected_package_ids:
        errors.append(
            issue(
                "package_set_materialization_relation_endpoint_not_selected",
                f"Selected relation {relation_id} requires selected source and target packages.",
                field="selection.relationIds",
            )
        )
    return {
        "id": relation_id,
        "type": relation_type,
        "source": source_id,
        "target": target_id,
        "reviewStatus": "selected_for_maintainer_review",
    }


def render_package_set_materialization_manifest_candidate(report: dict[str, Any]) -> str:
    return yaml.safe_dump(report["manifest"]["candidate"], sort_keys=False)


def render_package_set_materialization_pr_body(report: dict[str, Any]) -> str:
    package_lines = []
    for item in report.get("packages", []):
        package_lines.append(
            "- "
            f"`{item.get('package_id', 'unknown')}@{item.get('version', 'unknown')}` "
            f"from `{item.get('sourcePath', 'unknown')}` -> "
            f"`{item.get('acceptedSourcePath', 'unknown')}`"
        )
    if not package_lines:
        package_lines.append("- No package candidates were selected.")

    relation_lines = []
    for item in report.get("relations", []):
        relation_lines.append(
            "- "
            f"`{item.get('id', 'unknown')}`: `{item.get('source', 'unknown')}` "
            f"{item.get('type', 'related')} `{item.get('target', 'unknown')}`"
        )
    if not relation_lines:
        relation_lines.append("- No relation proposals were selected.")

    return (
        "\n".join(
            [
                "## Motivation",
                "",
                "Materialize maintainer-selected package-set candidates for "
                "accepted-source review.",
                "",
                f"Handoff: `{report['handoff']['path']}`",
                f"Helper report status: `{report['status']}`",
                "",
                "## Selected Packages",
                "",
                *package_lines,
                "",
                "## Selected Relations",
                "",
                *relation_lines,
                "",
                "## Boundaries",
                "",
                "- A passing package-set preflight is review evidence, not registry acceptance.",
                "- Only the selected package IDs and relation IDs are proposed for review.",
                "- Maintainers must still review the generated accepted-source diff before merge.",
            ]
        )
        + "\n"
    )


def validate_producer_evidence_links(
    producer_links: list[Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> dict[str, dict[str, Any]]:
    role_map: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(producer_links):
        if not isinstance(entry, dict):
            errors.append(
                issue(
                    "producer_evidence_entry_invalid",
                    "producerEvidenceLinks entries must be objects.",
                    field=f"producerEvidenceLinks[{index}]",
                )
            )
            continue
        role = entry.get("role")
        if not isinstance(role, str) or not role:
            errors.append(
                issue(
                    "producer_evidence_role_missing",
                    "producerEvidenceLinks entry must include a role.",
                    field=f"producerEvidenceLinks[{index}].role",
                )
            )
            continue
        if role in role_map:
            errors.append(
                issue(
                    "producer_evidence_role_duplicate",
                    f"Duplicate producerEvidenceLinks role: {role}.",
                    field=f"producerEvidenceLinks[{index}].role",
                )
            )
            continue
        role_map[role] = entry
        validate_evidence_entry(role, entry, errors, warnings, root)

    missing_roles = sorted(REQUIRED_PRODUCER_EVIDENCE_ROLES - set(role_map))
    for role in missing_roles:
        errors.append(
            issue(
                "producer_evidence_role_missing",
                f"Missing required producer evidence role: {role}.",
                field="producerEvidenceLinks",
            )
        )
    return role_map


def validate_evidence_entry(
    role: str,
    entry: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> None:
    path_scope = entry.get("pathScope")
    if path_scope not in KNOWN_PATH_SCOPES:
        errors.append(
            issue(
                "producer_evidence_path_scope_invalid",
                f"Producer evidence role {role} must use a known pathScope.",
                field=f"producerEvidenceLinks.{role}.pathScope",
            )
        )
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        errors.append(
            issue(
                "producer_evidence_path_missing",
                f"Producer evidence role {role} must include a path.",
                field=f"producerEvidenceLinks.{role}.path",
            )
        )
    required = entry.get("required")
    if required is not True and role in REQUIRED_PRODUCER_EVIDENCE_ROLES:
        errors.append(
            issue(
                "producer_evidence_required_flag_invalid",
                f"Required producer evidence role {role} must set required: true.",
                field=f"producerEvidenceLinks.{role}.required",
            )
        )
    status = entry.get("status")
    if status not in {"expected", "present", "missing"}:
        errors.append(
            issue(
                "producer_evidence_status_invalid",
                f"Producer evidence role {role} must use status expected, present, or missing.",
                field=f"producerEvidenceLinks.{role}.status",
            )
        )
    if role in REQUIRED_PRODUCER_EVIDENCE_ROLES and status == "missing":
        errors.append(
            issue(
                "producer_evidence_required_missing",
                f"Required producer evidence role {role} is marked missing.",
                field=f"producerEvidenceLinks.{role}.status",
            )
        )
    if role in OPTIONAL_PRODUCER_EVIDENCE_ROLES and status == "missing":
        warnings.append(
            issue(
                "producer_evidence_optional_missing",
                f"Optional producer evidence role {role} is marked missing.",
                field=f"producerEvidenceLinks.{role}.status",
            )
        )
    if root is not None and status != "missing":
        validate_evidence_path(root, role, entry, errors, warnings)


def validate_evidence_path(
    root: Path,
    role: str,
    entry: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    path_scope = entry.get("pathScope")
    path = entry.get("path")
    if path_scope == "pull_request" or not isinstance(path, str):
        return
    evidence_path = (root / path).resolve()
    root_resolved = root.resolve()
    if not evidence_path.is_relative_to(root_resolved):
        errors.append(
            issue(
                "producer_evidence_path_escape",
                f"Producer evidence role {role} path escapes the preflight root.",
                field=f"producerEvidenceLinks.{role}.path",
            )
        )
        return
    if not evidence_path.exists():
        target = errors if role in REQUIRED_PRODUCER_EVIDENCE_ROLES else warnings
        target.append(
            issue(
                "producer_evidence_file_missing",
                f"Producer evidence role {role} path does not exist: {path}.",
                field=f"producerEvidenceLinks.{role}.path",
            )
        )
        return
    digest = entry.get("digest")
    if isinstance(digest, str) and digest.startswith("sha256:"):
        if not evidence_path.is_file():
            errors.append(
                issue(
                    "producer_evidence_digest_target_invalid",
                    f"Producer evidence role {role} digest target must be a file.",
                    field=f"producerEvidenceLinks.{role}.digest",
                )
            )
            return
        actual = f"sha256:{sha256_file(evidence_path)}"
        if digest != actual:
            errors.append(
                issue(
                    "producer_evidence_digest_mismatch",
                    f"Producer evidence role {role} digest does not match file bytes.",
                    field=f"producerEvidenceLinks.{role}.digest",
                )
            )


def validate_registry_acceptance_decision(
    decision: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    status = decision.get("status")
    if status not in VALID_DECISION_STATUSES:
        errors.append(
            issue(
                "registry_acceptance_decision_status_invalid",
                "registryAcceptanceDecision.status must be external_required "
                "or a known decision status.",
                field="registryAcceptanceDecision.status",
            )
        )
    if decision.get("recordKind") != "SpecPMRegistryAcceptanceDecision":
        errors.append(
            issue(
                "registry_acceptance_decision_kind_invalid",
                "registryAcceptanceDecision.recordKind must be SpecPMRegistryAcceptanceDecision.",
                field="registryAcceptanceDecision.recordKind",
            )
        )
    if decision.get("producerReceiptAuthority") != "evidence_only":
        errors.append(
            issue(
                "registry_acceptance_decision_authority_invalid",
                "registryAcceptanceDecision must keep producer receipts as evidence_only.",
                field="registryAcceptanceDecision.producerReceiptAuthority",
            )
        )
    required_for = decision.get("requiredFor")
    if not isinstance(required_for, list) or "public_index_acceptance" not in required_for:
        errors.append(
            issue(
                "registry_acceptance_decision_required_for_missing",
                "registryAcceptanceDecision.requiredFor must include public_index_acceptance.",
                field="registryAcceptanceDecision.requiredFor",
            )
        )
    if status == "approved":
        warnings.append(
            issue(
                "registry_acceptance_decision_approved_review_required",
                "Approved registry decisions must be verified against "
                "SpecPM maintainer review records.",
                field="registryAcceptanceDecision.status",
            )
        )


def validate_package_set_handoff(
    handoff: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> dict[str, Any]:
    if handoff.get("apiVersion") != PACKAGE_SET_HANDOFF_API_VERSION:
        errors.append(
            issue(
                "package_set_handoff_api_version_invalid",
                f"Package-set handoff apiVersion must be {PACKAGE_SET_HANDOFF_API_VERSION}.",
                field="packageSetHandoff.apiVersion",
            )
        )
    if handoff.get("kind") != PACKAGE_SET_HANDOFF_KIND:
        errors.append(
            issue(
                "package_set_handoff_kind_invalid",
                f"Package-set handoff kind must be {PACKAGE_SET_HANDOFF_KIND}.",
                field="packageSetHandoff.kind",
            )
        )
    if handoff.get("schemaVersion") != 1:
        errors.append(
            issue(
                "package_set_handoff_schema_version_invalid",
                "Package-set handoff schemaVersion must be 1.",
                field="packageSetHandoff.schemaVersion",
            )
        )
    if handoff.get("status") != "ok":
        errors.append(
            issue(
                "package_set_handoff_status_invalid",
                "Package-set handoff status must be ok before SpecPM intake preflight.",
                field="packageSetHandoff.status",
            )
        )

    package_set = _mapping_value(handoff.get("packageSet"))
    members = _list_of_mappings(handoff.get("members"))
    relations = _list_of_mappings(handoff.get("relations"))
    evidence_links = _list_of_mappings(handoff.get("evidenceLinks"))
    decision = _mapping_value(handoff.get("registryAcceptanceDecision"))

    package_set_id = package_set.get("id")
    if not isinstance(package_set_id, str) or not package_set_id:
        errors.append(
            issue(
                "package_set_id_missing",
                "Package-set handoff must identify packageSet.id.",
                field="packageSetHandoff.packageSet.id",
            )
        )
    if package_set.get("candidateCount") != len(members):
        errors.append(
            issue(
                "package_set_candidate_count_mismatch",
                "Package-set candidateCount must match members length.",
                field="packageSetHandoff.packageSet.candidateCount",
            )
        )
    if package_set.get("relationCount") != len(relations):
        errors.append(
            issue(
                "package_set_relation_count_mismatch",
                "Package-set relationCount must match relations length.",
                field="packageSetHandoff.packageSet.relationCount",
            )
        )

    member_ids = validate_package_set_members(members, errors, warnings, root)
    validate_package_set_relations(relations, member_ids, package_set_id, errors)
    validate_package_set_evidence_links(evidence_links, errors, warnings, root)
    validate_package_set_member_bundle_links(members, evidence_links, errors)
    validate_package_set_member_evidence(members, errors, warnings, root)
    validate_package_set_preflight_record(handoff, len(members), len(relations), errors, warnings)
    validate_package_set_acceptance_decision(decision, errors, warnings, len(relations))

    return {
        "id": package_set_id,
        "memberCount": len(members),
        "relationCount": len(relations),
        "evidenceRoleCount": len(
            {
                role
                for link in evidence_links
                if isinstance((role := link.get("role")), str) and role
            }
        ),
        "preflightStatus": _mapping_value(handoff.get("preflight")).get("status"),
        "registryAcceptanceStatus": decision.get("status"),
    }


def validate_package_set_members(
    members: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> set[str]:
    ids: set[str] = set()
    if not members:
        errors.append(
            issue(
                "package_set_members_missing",
                "Package-set handoff must include at least one member candidate.",
                field="packageSetHandoff.members",
            )
        )
    for index, member in enumerate(members):
        field = f"packageSetHandoff.members[{index}]"
        package_id = member.get("packageId")
        if not isinstance(package_id, str) or not package_id:
            errors.append(
                issue(
                    "package_set_member_id_missing",
                    "Package-set member must include packageId.",
                    field=f"{field}.packageId",
                )
            )
            continue
        if package_id in ids:
            errors.append(
                issue(
                    "package_set_member_id_duplicate",
                    f"Duplicate package-set member packageId: {package_id}.",
                    field=f"{field}.packageId",
                )
            )
        ids.add(package_id)
        for key in (
            "candidatePath",
            "manifestPath",
            "producerReceiptPath",
            "validationReportPath",
            "diagnosticsReportPath",
        ):
            if not isinstance(member.get(key), str) or not member[key]:
                errors.append(
                    issue(
                        "package_set_member_path_missing",
                        f"Package-set member {package_id} must include {key}.",
                        field=f"{field}.{key}",
                    )
                )
        manifest_path = member.get("manifestPath")
        if root is not None and isinstance(manifest_path, str):
            manifest = resolve_package_set_path(root, manifest_path)
            if manifest is None:
                errors.append(
                    issue(
                        "package_set_member_path_escape",
                        f"Package-set member {package_id} manifest path escapes the root.",
                        field=f"{field}.manifestPath",
                    )
                )
            elif manifest.is_file():
                manifest_id = read_manifest_package_id(manifest, warnings, f"{field}.manifestPath")
                if manifest_id is not None and manifest_id != package_id:
                    errors.append(
                        issue(
                            "package_set_member_manifest_id_mismatch",
                            f"Member {package_id} manifest metadata.id is {manifest_id}.",
                            field=f"{field}.manifestPath",
                        )
                    )
            else:
                errors.append(
                    issue(
                        "package_set_member_manifest_missing",
                        f"Package-set member {package_id} manifest file is missing.",
                        field=f"{field}.manifestPath",
                    )
                )
    return ids


def validate_package_set_relations(
    relations: list[dict[str, Any]],
    member_ids: set[str],
    package_set_id: Any,
    errors: list[dict[str, Any]],
) -> None:
    for index, relation in enumerate(relations):
        field = f"packageSetHandoff.relations[{index}]"
        relation_type = relation.get("type")
        source_id = _mapping_value(relation.get("source")).get("packageId")
        target_id = _mapping_value(relation.get("target")).get("packageId")
        if relation_type != "contains":
            errors.append(
                issue(
                    "package_set_relation_type_unsupported",
                    "Package-set preflight currently supports contains relation proposals only.",
                    field=f"{field}.type",
                )
            )
        if source_id not in member_ids:
            errors.append(
                issue(
                    "package_set_relation_source_missing",
                    f"Relation source package is not declared as a handoff member: {source_id}.",
                    field=f"{field}.source.packageId",
                )
            )
        if target_id not in member_ids:
            errors.append(
                issue(
                    "package_set_relation_target_missing",
                    f"Relation target package is not declared as a handoff member: {target_id}.",
                    field=f"{field}.target.packageId",
                )
            )
        if source_id == target_id and source_id is not None:
            errors.append(
                issue(
                    "package_set_relation_self_reference",
                    "Relation source and target must be different package IDs.",
                    field=field,
                )
            )
        if (
            isinstance(package_set_id, str)
            and relation_type == "contains"
            and source_id != package_set_id
        ):
            errors.append(
                issue(
                    "package_set_relation_source_not_package_set",
                    "Contains relation source must be the package-set aggregate package ID.",
                    field=f"{field}.source.packageId",
                )
            )


def validate_package_set_evidence_links(
    links: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> None:
    role_map: dict[str, list[dict[str, Any]]] = {}
    for index, link in enumerate(links):
        field = f"packageSetHandoff.evidenceLinks[{index}]"
        role = link.get("role")
        if not isinstance(role, str) or not role:
            errors.append(
                issue(
                    "package_set_evidence_role_missing",
                    "Package-set evidence link must include role.",
                    field=f"{field}.role",
                )
            )
            continue
        role_map.setdefault(role, []).append(link)
        validate_package_set_evidence_link(link, errors, warnings, root, field)
    for role in sorted(REQUIRED_PACKAGE_SET_EVIDENCE_ROLES - set(role_map)):
        errors.append(
            issue(
                "package_set_evidence_role_missing",
                f"Missing required package-set evidence role: {role}.",
                field="packageSetHandoff.evidenceLinks",
            )
        )
    for role in sorted(REQUIRED_PACKAGE_SET_EVIDENCE_ROLES & set(role_map)):
        for link in role_map[role]:
            if link.get("status") == "missing":
                errors.append(
                    issue(
                        "package_set_evidence_required_missing",
                        f"Required package-set evidence role {role} is marked missing.",
                        field="packageSetHandoff.evidenceLinks",
                    )
                )


def validate_package_set_member_evidence(
    members: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
) -> None:
    for member_index, member in enumerate(members):
        package_id = member.get("packageId") or f"member[{member_index}]"
        links = _list_of_mappings(member.get("evidenceLinks"))
        roles = {role for link in links if isinstance((role := link.get("role")), str) and role}
        for role in sorted(REQUIRED_MEMBER_EVIDENCE_ROLES - roles):
            errors.append(
                issue(
                    "package_set_member_evidence_role_missing",
                    f"Member {package_id} is missing evidence role: {role}.",
                    field=f"packageSetHandoff.members[{member_index}].evidenceLinks",
                )
            )
        for link_index, link in enumerate(links):
            validate_package_set_evidence_link(
                link,
                errors,
                warnings,
                root,
                f"packageSetHandoff.members[{member_index}].evidenceLinks[{link_index}]",
            )
            role = link.get("role")
            if role in REQUIRED_MEMBER_EVIDENCE_ROLES and link.get("status") == "missing":
                errors.append(
                    issue(
                        "package_set_member_evidence_required_missing",
                        f"Member {package_id} evidence role {role} is marked missing.",
                        field=f"packageSetHandoff.members[{member_index}].evidenceLinks[{link_index}].status",
                    )
                )


def validate_package_set_member_bundle_links(
    members: list[dict[str, Any]],
    evidence_links: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    bundle_links = [
        link for link in evidence_links if link.get("role") == "member_candidate_bundle"
    ]
    for member_index, member in enumerate(members):
        package_id = member.get("packageId")
        candidate_path = member.get("candidatePath")
        matching = [
            link
            for link in bundle_links
            if link.get("packageId") == package_id and link.get("path") == candidate_path
        ]
        if not matching:
            errors.append(
                issue(
                    "package_set_member_bundle_evidence_missing",
                    f"Member {package_id} is missing top-level member_candidate_bundle evidence.",
                    field=f"packageSetHandoff.members[{member_index}].candidatePath",
                )
            )


def validate_package_set_evidence_link(
    link: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
    field: str,
) -> None:
    path_scope = link.get("pathScope")
    path = link.get("path")
    status = link.get("status")
    if path_scope not in KNOWN_PACKAGE_SET_EVIDENCE_PATH_SCOPES:
        errors.append(
            issue(
                "package_set_evidence_path_scope_invalid",
                "Package-set evidence link must use a known pathScope.",
                field=f"{field}.pathScope",
            )
        )
    if not isinstance(path, str) or not path:
        errors.append(
            issue(
                "package_set_evidence_path_missing",
                "Package-set evidence link must include path.",
                field=f"{field}.path",
            )
        )
        return
    if status not in {"present", "expected", "missing", "rejected"}:
        errors.append(
            issue(
                "package_set_evidence_status_invalid",
                "Package-set evidence status must be present, expected, missing, or rejected.",
                field=f"{field}.status",
            )
        )
    if status == "rejected":
        errors.append(
            issue(
                "package_set_evidence_rejected",
                "Rejected package-set evidence cannot pass SpecPM intake preflight.",
                field=f"{field}.status",
            )
        )
    if root is None or path_scope == "local_path":
        return
    resolved = resolve_package_set_path(root, path)
    if resolved is None:
        errors.append(
            issue(
                "package_set_evidence_path_escape",
                "Package-set evidence path escapes the preflight root.",
                field=f"{field}.path",
            )
        )
        return
    if status not in {"missing", "expected"} and not resolved.exists():
        errors.append(
            issue(
                "package_set_evidence_file_missing",
                f"Package-set evidence file is missing: {path}.",
                field=f"{field}.path",
            )
        )
        return
    digest = link.get("digest")
    if isinstance(digest, str) and digest.startswith("sha256:") and resolved.is_file():
        actual = f"sha256:{sha256_file(resolved)}"
        if digest != actual:
            errors.append(
                issue(
                    "package_set_evidence_digest_mismatch",
                    "Package-set evidence digest does not match file bytes.",
                    field=f"{field}.digest",
                )
            )


def validate_package_set_preflight_record(
    handoff: dict[str, Any],
    member_count: int,
    relation_count: int,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    preflight = _mapping_value(handoff.get("preflight"))
    status = preflight.get("status")
    if status == "not_provided":
        warnings.append(
            issue(
                "package_set_bundle_preflight_missing",
                "Package-set handoff did not include bundle-set preflight evidence.",
                field="packageSetHandoff.preflight.status",
            )
        )
        return
    if status != "passed":
        errors.append(
            issue(
                "package_set_bundle_preflight_not_passed",
                "Package-set bundle-set preflight status must be passed.",
                field="packageSetHandoff.preflight.status",
            )
        )
    for key, expected in (("candidateCount", member_count), ("relationCount", relation_count)):
        if preflight.get(key) != expected:
            errors.append(
                issue(
                    "package_set_bundle_preflight_count_mismatch",
                    f"Package-set preflight {key} must match handoff counts.",
                    field=f"packageSetHandoff.preflight.{key}",
                )
            )
    if preflight.get("errorCount") not in (0, None):
        errors.append(
            issue(
                "package_set_bundle_preflight_errors_present",
                "Package-set bundle-set preflight must not report errors.",
                field="packageSetHandoff.preflight.errorCount",
            )
        )


def validate_package_set_acceptance_decision(
    decision: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    relation_count: int,
) -> None:
    status = decision.get("status")
    if status not in VALID_DECISION_STATUSES:
        errors.append(
            issue(
                "package_set_acceptance_decision_status_invalid",
                "Package-set registryAcceptanceDecision.status must be a known status.",
                field="packageSetHandoff.registryAcceptanceDecision.status",
            )
        )
    if status == "approved":
        errors.append(
            issue(
                "package_set_acceptance_decision_approved_not_allowed",
                "Package-set dry-run handoff must not mark registry acceptance approved.",
                field="packageSetHandoff.registryAcceptanceDecision.status",
            )
        )
    if decision.get("recordKind") != "SpecPMRegistryAcceptanceDecision":
        errors.append(
            issue(
                "package_set_acceptance_decision_kind_invalid",
                "Package-set registryAcceptanceDecision.recordKind is invalid.",
                field="packageSetHandoff.registryAcceptanceDecision.recordKind",
            )
        )
    authority = decision.get("producerReceiptAuthority") or decision.get("producerAuthority")
    if authority != "evidence_only":
        errors.append(
            issue(
                "package_set_acceptance_decision_authority_invalid",
                "Package-set producer authority must remain evidence_only.",
                field="packageSetHandoff.registryAcceptanceDecision.producerAuthority",
            )
        )
    required_for = decision.get("requiredFor")
    if not isinstance(required_for, list) or "public_index_acceptance" not in required_for:
        errors.append(
            issue(
                "package_set_acceptance_decision_required_for_missing",
                "Package-set registryAcceptanceDecision.requiredFor must include "
                "public_index_acceptance.",
                field="packageSetHandoff.registryAcceptanceDecision.requiredFor",
            )
        )
    if (
        relation_count > 0
        and isinstance(required_for, list)
        and "package_relation_acceptance" not in required_for
    ):
        warnings.append(
            issue(
                "package_set_acceptance_decision_relation_scope_missing",
                "Package-set registryAcceptanceDecision.requiredFor should include "
                "package_relation_acceptance when relation proposals are present.",
                field="packageSetHandoff.registryAcceptanceDecision.requiredFor",
            )
        )


def validate_package_set_ai_enrichment(
    enrichment: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
    handoff: dict[str, Any],
    handoff_member_ids: set[str],
) -> None:
    if enrichment.get("apiVersion") != PACKAGE_SET_AI_ENRICHMENT_API_VERSION:
        errors.append(
            issue(
                "ai_enrichment_api_version_invalid",
                f"AI enrichment apiVersion must be {PACKAGE_SET_AI_ENRICHMENT_API_VERSION}.",
                field="aiEnrichment.apiVersion",
            )
        )
    if enrichment.get("kind") != PACKAGE_SET_AI_ENRICHMENT_KIND:
        errors.append(
            issue(
                "ai_enrichment_kind_invalid",
                f"AI enrichment kind must be {PACKAGE_SET_AI_ENRICHMENT_KIND}.",
                field="aiEnrichment.kind",
            )
        )
    if enrichment.get("schemaVersion") != 1:
        errors.append(
            issue(
                "ai_enrichment_schema_version_invalid",
                "AI enrichment schemaVersion must be 1.",
                field="aiEnrichment.schemaVersion",
            )
        )
    artifact_status = enrichment.get("status")
    if artifact_status == "failed":
        errors.append(
            issue(
                "ai_enrichment_status_failed",
                "Failed AI enrichment artifacts cannot pass SpecPM preflight.",
                field="aiEnrichment.status",
            )
        )
    elif artifact_status not in AI_ENRICHMENT_ALLOWED_ARTIFACT_STATUSES:
        errors.append(
            issue(
                "ai_enrichment_status_invalid",
                "AI enrichment status must be completed or warning.",
                field="aiEnrichment.status",
            )
        )
    elif artifact_status == "warning":
        warnings.append(
            issue(
                "ai_enrichment_artifact_warning",
                "AI enrichment artifact completed with producer-side warnings.",
                field="aiEnrichment.status",
            )
        )
    if enrichment.get("authority") != "proposal_only_not_registry_acceptance":
        errors.append(
            issue(
                "ai_enrichment_authority_invalid",
                "AI enrichment authority must remain proposal_only_not_registry_acceptance.",
                field="aiEnrichment.authority",
            )
        )

    validate_ai_enrichment_no_acceptance_decision(enrichment, errors)
    validate_ai_enrichment_privacy(_mapping_value(enrichment.get("privacy")), errors)
    validate_ai_enrichment_trust_boundary(enrichment, errors)
    validate_ai_enrichment_non_goals(enrichment, errors)
    validate_ai_enrichment_provider(_mapping_value(enrichment.get("provider")), errors)
    validate_ai_enrichment_inputs(enrichment, errors, root)

    proposals = _list_of_mappings(enrichment.get("proposals"))
    package_set = _mapping_value(enrichment.get("packageSet"))
    package_set_id = package_set.get("id")
    if not isinstance(package_set_id, str) or not package_set_id:
        errors.append(
            issue(
                "ai_enrichment_package_set_id_missing",
                "AI enrichment packageSet.id must be present.",
                field="aiEnrichment.packageSet.id",
            )
        )
    handoff_package_set_id = _mapping_value(handoff.get("packageSet")).get("id")
    if (
        isinstance(package_set_id, str)
        and isinstance(handoff_package_set_id, str)
        and package_set_id != handoff_package_set_id
    ):
        errors.append(
            issue(
                "ai_enrichment_package_set_id_mismatch",
                "AI enrichment packageSet.id must match the package-set handoff id.",
                field="aiEnrichment.packageSet.id",
            )
        )
    if package_set.get("candidateCount") != len(proposals):
        errors.append(
            issue(
                "ai_enrichment_candidate_count_mismatch",
                "AI enrichment packageSet.candidateCount must match proposals length.",
                field="aiEnrichment.packageSet.candidateCount",
            )
        )
    summary = _mapping_value(enrichment.get("summary"))
    if summary.get("proposalCount") != len(proposals):
        errors.append(
            issue(
                "ai_enrichment_summary_proposal_count_mismatch",
                "AI enrichment summary.proposalCount must match proposals length.",
                field="aiEnrichment.summary.proposalCount",
            )
        )
    if summary.get("errorCount") not in (0, None):
        errors.append(
            issue(
                "ai_enrichment_summary_errors_present",
                "AI enrichment summary.errorCount must be zero before SpecPM review use.",
                field="aiEnrichment.summary.errorCount",
            )
        )

    allowed_paths = ai_enrichment_allowed_evidence_paths(enrichment)
    if not allowed_paths:
        errors.append(
            issue(
                "ai_enrichment_allowed_evidence_missing",
                "AI enrichment inputs must include compact_model_input evidencePaths.",
                field="aiEnrichment.inputs",
            )
        )
    validate_ai_enrichment_proposals(
        proposals,
        errors,
        warnings,
        allowed_paths,
        handoff,
        handoff_member_ids,
    )
    validate_ai_enrichment_diagnostics(enrichment, errors, warnings)


def validate_ai_enrichment_no_acceptance_decision(
    enrichment: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    for key in ("registryAcceptanceDecision", "acceptanceDecision"):
        if key in enrichment:
            errors.append(
                issue(
                    "ai_enrichment_acceptance_decision_not_allowed",
                    "AI enrichment artifacts must not carry registry acceptance decisions.",
                    field=f"aiEnrichment.{key}",
                )
            )


def validate_ai_enrichment_privacy(
    privacy: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    for key in sorted(AI_ENRICHMENT_REQUIRED_PRIVACY_FLAGS):
        if privacy.get(key) is not False:
            errors.append(
                issue(
                    "ai_enrichment_privacy_flag_invalid",
                    f"AI enrichment privacy.{key} must be false.",
                    field=f"aiEnrichment.privacy.{key}",
                )
            )


def validate_ai_enrichment_trust_boundary(
    enrichment: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    notes = [item for item in list_value(enrichment.get("trustBoundary")) if isinstance(item, str)]
    joined = "\n".join(notes).lower()
    if "proposal evidence only" not in joined or "specpm remains" not in joined:
        errors.append(
            issue(
                "ai_enrichment_trust_boundary_invalid",
                "AI enrichment trustBoundary must keep output proposal-only "
                "and SpecPM authoritative.",
                field="aiEnrichment.trustBoundary",
            )
        )


def validate_ai_enrichment_non_goals(
    enrichment: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    non_goals = {item for item in list_value(enrichment.get("nonGoals")) if isinstance(item, str)}
    missing = sorted(AI_ENRICHMENT_REQUIRED_NON_GOALS - non_goals)
    if missing:
        errors.append(
            issue(
                "ai_enrichment_non_goals_missing",
                "AI enrichment nonGoals must exclude acceptance and registry publication: "
                + ", ".join(missing),
                field="aiEnrichment.nonGoals",
            )
        )


def validate_ai_enrichment_provider(
    provider: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if not isinstance(provider.get("kind"), str) or not provider["kind"]:
        errors.append(
            issue(
                "ai_enrichment_provider_kind_missing",
                "AI enrichment provider.kind must be present for provenance.",
                field="aiEnrichment.provider.kind",
            )
        )
    if provider.get("execution") not in {"operator_opt_in_local", "not_run_by_spec_harvester"}:
        errors.append(
            issue(
                "ai_enrichment_provider_execution_invalid",
                "AI enrichment provider.execution must describe local opt-in or external output.",
                field="aiEnrichment.provider.execution",
            )
        )


def validate_ai_enrichment_inputs(
    enrichment: dict[str, Any],
    errors: list[dict[str, Any]],
    root: Path | None,
) -> None:
    for index, item in enumerate(_list_of_mappings(enrichment.get("inputs"))):
        field = f"aiEnrichment.inputs[{index}]"
        role = item.get("role")
        if not isinstance(role, str) or not role:
            errors.append(
                issue(
                    "ai_enrichment_input_role_missing",
                    "AI enrichment input record must include role.",
                    field=f"{field}.role",
                )
            )
        path = item.get("path")
        path_scope = item.get("pathScope")
        if path is None:
            continue
        if not isinstance(path, str) or not path:
            errors.append(
                issue(
                    "ai_enrichment_input_path_invalid",
                    "AI enrichment input path must be a non-empty string.",
                    field=f"{field}.path",
                )
            )
            continue
        if path_scope not in KNOWN_PACKAGE_SET_EVIDENCE_PATH_SCOPES:
            errors.append(
                issue(
                    "ai_enrichment_input_path_scope_invalid",
                    "AI enrichment input path must use a known pathScope.",
                    field=f"{field}.pathScope",
                )
            )
        if path_scope == "bundle_relative" and root is not None:
            validate_ai_enrichment_input_file(root, item, errors, field)
        if role == "compact_model_input":
            for evidence_index, evidence_path in enumerate(list_value(item.get("evidencePaths"))):
                if not isinstance(evidence_path, str) or not evidence_path:
                    errors.append(
                        issue(
                            "ai_enrichment_allowed_evidence_path_invalid",
                            "AI enrichment compact_model_input evidencePaths must be "
                            "non-empty strings.",
                            field=f"{field}.evidencePaths[{evidence_index}]",
                        )
                    )
                elif not is_safe_relative_path(evidence_path):
                    errors.append(
                        issue(
                            "ai_enrichment_allowed_evidence_path_unsafe",
                            "AI enrichment compact_model_input evidencePaths must be "
                            "safe relative paths.",
                            field=f"{field}.evidencePaths[{evidence_index}]",
                        )
                    )


def validate_ai_enrichment_input_file(
    root: Path,
    item: dict[str, Any],
    errors: list[dict[str, Any]],
    field: str,
) -> None:
    path = item.get("path")
    if not isinstance(path, str):
        return
    resolved = resolve_package_set_path(root, path)
    if resolved is None:
        errors.append(
            issue(
                "ai_enrichment_input_path_escape",
                "AI enrichment bundle-relative input path escapes the preflight root.",
                field=f"{field}.path",
            )
        )
        return
    if not resolved.is_file():
        errors.append(
            issue(
                "ai_enrichment_input_file_missing",
                f"AI enrichment input file is missing: {path}.",
                field=f"{field}.path",
            )
        )
        return
    digest = item.get("digest")
    expected = digest_value(digest)
    if expected is not None:
        actual = f"sha256:{sha256_file(resolved)}"
        if expected != actual:
            errors.append(
                issue(
                    "ai_enrichment_input_digest_mismatch",
                    "AI enrichment input digest does not match file bytes.",
                    field=f"{field}.digest",
                )
            )


def validate_ai_enrichment_proposals(
    proposals: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    allowed_paths: set[str],
    handoff: dict[str, Any],
    handoff_member_ids: set[str],
) -> None:
    ids: set[str] = set()
    if not proposals:
        errors.append(
            issue(
                "ai_enrichment_proposals_missing",
                "AI enrichment artifact must include at least one proposal.",
                field="aiEnrichment.proposals",
            )
        )
    for index, proposal in enumerate(proposals):
        field = f"aiEnrichment.proposals[{index}]"
        package_id = proposal.get("packageId")
        if not isinstance(package_id, str) or not package_id:
            errors.append(
                issue(
                    "ai_enrichment_proposal_package_id_missing",
                    "AI enrichment proposal must include packageId.",
                    field=f"{field}.packageId",
                )
            )
            continue
        if package_id in ids:
            errors.append(
                issue(
                    "ai_enrichment_proposal_package_id_duplicate",
                    f"Duplicate AI enrichment proposal packageId: {package_id}.",
                    field=f"{field}.packageId",
                )
            )
        ids.add(package_id)
        if handoff_member_ids and package_id not in handoff_member_ids:
            errors.append(
                issue(
                    "ai_enrichment_package_id_not_in_handoff",
                    "AI enrichment proposal packageId is not present in handoff members: "
                    f"{package_id}.",
                    field=f"{field}.packageId",
                )
            )
        status = proposal.get("status")
        if status not in AI_ENRICHMENT_PROPOSAL_STATUSES:
            errors.append(
                issue(
                    "ai_enrichment_proposal_status_invalid",
                    "AI enrichment proposal status must be proposed or missing_model_output.",
                    field=f"{field}.status",
                )
            )
        if status == "missing_model_output":
            errors.append(
                issue(
                    "ai_enrichment_model_output_missing",
                    f"AI enrichment proposal for {package_id} is missing model output.",
                    field=f"{field}.status",
                )
            )
        validate_ai_enrichment_records(
            package_id,
            _list_of_mappings(proposal.get("capabilities")),
            errors,
            warnings,
            allowed_paths,
            f"{field}.capabilities",
            require_interface_kind=False,
        )
        validate_ai_enrichment_records(
            package_id,
            _list_of_mappings(proposal.get("interfaces")),
            errors,
            warnings,
            allowed_paths,
            f"{field}.interfaces",
            require_interface_kind=True,
        )
        validate_ai_enrichment_provider_receipt(
            package_id,
            _mapping_value(proposal.get("providerReceipt")),
            errors,
            field,
        )
    if handoff_member_ids and ids != handoff_member_ids:
        missing = sorted(handoff_member_ids - ids)
        extra = sorted(ids - handoff_member_ids)
        errors.append(
            issue(
                "ai_enrichment_handoff_package_set_mismatch",
                "AI enrichment proposal package IDs must match handoff member IDs. "
                f"Missing: {', '.join(missing) or 'none'}; extra: {', '.join(extra) or 'none'}.",
                field="aiEnrichment.proposals",
            )
        )


def validate_ai_enrichment_records(
    package_id: str,
    records: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    allowed_paths: set[str],
    field: str,
    *,
    require_interface_kind: bool,
) -> None:
    for index, record in enumerate(records):
        record_field = f"{field}[{index}]"
        if not isinstance(record.get("id"), str) or not record["id"]:
            errors.append(
                issue(
                    "ai_enrichment_record_id_missing",
                    f"AI enrichment record for {package_id} must include id.",
                    field=f"{record_field}.id",
                )
            )
        if not isinstance(record.get("summary"), str) or not record["summary"]:
            warnings.append(
                issue(
                    "ai_enrichment_record_summary_missing",
                    f"AI enrichment record for {package_id} should include summary.",
                    field=f"{record_field}.summary",
                )
            )
        if require_interface_kind and (
            not isinstance(record.get("kind"), str) or not record["kind"]
        ):
            errors.append(
                issue(
                    "ai_enrichment_interface_kind_missing",
                    f"AI enrichment interface proposal for {package_id} must preserve kind.",
                    field=f"{record_field}.kind",
                )
            )
        evidence_paths = [
            path
            for path in list_value(record.get("evidencePaths"))
            if isinstance(path, str) and path
        ]
        if not evidence_paths:
            warnings.append(
                issue(
                    "ai_enrichment_record_evidence_missing",
                    f"AI enrichment record for {package_id} should cite evidencePaths.",
                    field=f"{record_field}.evidencePaths",
                )
            )
        for path in evidence_paths:
            if not is_safe_relative_path(path):
                errors.append(
                    issue(
                        "ai_enrichment_evidence_path_unsafe",
                        "AI enrichment evidencePaths must be safe relative paths.",
                        field=f"{record_field}.evidencePaths",
                    )
                )
            elif path not in allowed_paths:
                errors.append(
                    issue(
                        "ai_enrichment_evidence_path_not_allowlisted",
                        "AI enrichment evidencePath is not present in compact_model_input "
                        "allowlist.",
                        field=f"{record_field}.evidencePaths",
                    )
                )


def validate_ai_enrichment_provider_receipt(
    package_id: str,
    receipt: dict[str, Any],
    errors: list[dict[str, Any]],
    field: str,
) -> None:
    if not receipt:
        errors.append(
            issue(
                "ai_enrichment_provider_receipt_missing",
                f"AI enrichment proposal for {package_id} must include providerReceipt provenance.",
                field=f"{field}.providerReceipt",
            )
        )
        return
    for key in ("rawPromptPersisted", "rawResponsePersisted", "chainOfThoughtPersisted"):
        if key in receipt and receipt[key] is not False:
            errors.append(
                issue(
                    "ai_enrichment_provider_receipt_privacy_invalid",
                    f"AI enrichment providerReceipt.{key} must be false when present.",
                    field=f"{field}.providerReceipt.{key}",
                )
            )
    if receipt.get("authority") in {"accepted", "registry_authority", "truth"}:
        errors.append(
            issue(
                "ai_enrichment_provider_receipt_authority_invalid",
                "AI enrichment providerReceipt is provenance only, not semantic authority.",
                field=f"{field}.providerReceipt.authority",
            )
        )


def validate_ai_enrichment_diagnostics(
    enrichment: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    diagnostics = _list_of_mappings(enrichment.get("diagnostics"))
    severity_counts = {"error": 0, "warning": 0}
    for index, diagnostic in enumerate(diagnostics):
        severity = diagnostic.get("severity")
        if severity == "error":
            severity_counts["error"] += 1
            errors.append(
                issue(
                    "ai_enrichment_diagnostic_error",
                    "AI enrichment producer diagnostics include an error.",
                    field=f"aiEnrichment.diagnostics[{index}]",
                )
            )
        elif severity == "warning":
            severity_counts["warning"] += 1
            warnings.append(
                issue(
                    "ai_enrichment_diagnostic_warning",
                    "AI enrichment producer diagnostics include a warning.",
                    field=f"aiEnrichment.diagnostics[{index}]",
                )
            )
        elif severity is not None:
            warnings.append(
                issue(
                    "ai_enrichment_diagnostic_severity_unknown",
                    "AI enrichment diagnostic severity is not recognized.",
                    field=f"aiEnrichment.diagnostics[{index}].severity",
                )
            )
    summary = _mapping_value(enrichment.get("summary"))
    if summary.get("warningCount") not in (None, severity_counts["warning"]):
        warnings.append(
            issue(
                "ai_enrichment_summary_warning_count_mismatch",
                "AI enrichment summary.warningCount does not match diagnostics.",
                field="aiEnrichment.summary.warningCount",
            )
        )


def ai_enrichment_allowed_evidence_paths(enrichment: dict[str, Any]) -> set[str]:
    allowed: set[str] = set()
    for item in _list_of_mappings(enrichment.get("inputs")):
        if item.get("role") != "compact_model_input":
            continue
        for path in list_value(item.get("evidencePaths")):
            if isinstance(path, str) and path:
                allowed.add(path)
    return allowed


def validate_package_set_ai_draft(
    draft: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    root: Path | None,
    inventory: dict[str, Any],
) -> None:
    if draft.get("apiVersion") != PACKAGE_SET_AI_DRAFT_API_VERSION:
        errors.append(
            issue(
                "ai_draft_api_version_invalid",
                f"AI draft apiVersion must be {PACKAGE_SET_AI_DRAFT_API_VERSION}.",
                field="aiDraft.apiVersion",
            )
        )
    if draft.get("kind") != PACKAGE_SET_AI_DRAFT_KIND:
        errors.append(
            issue(
                "ai_draft_kind_invalid",
                f"AI draft kind must be {PACKAGE_SET_AI_DRAFT_KIND}.",
                field="aiDraft.kind",
            )
        )
    if draft.get("schemaVersion") != 1:
        errors.append(
            issue(
                "ai_draft_schema_version_invalid",
                "AI draft schemaVersion must be 1.",
                field="aiDraft.schemaVersion",
            )
        )

    artifact_status = draft.get("status")
    if artifact_status == "failed":
        errors.append(
            issue(
                "ai_draft_status_failed",
                "Failed AI draft artifacts cannot pass SpecPM preflight.",
                field="aiDraft.status",
            )
        )
    elif artifact_status not in AI_DRAFT_ALLOWED_ARTIFACT_STATUSES:
        errors.append(
            issue(
                "ai_draft_status_invalid",
                "AI draft status must be completed or warning.",
                field="aiDraft.status",
            )
        )
    elif artifact_status == "warning":
        warnings.append(
            issue(
                "ai_draft_artifact_warning",
                "AI draft artifact completed with producer-side warnings.",
                field="aiDraft.status",
            )
        )

    if draft.get("authority") != "proposal_only_not_registry_acceptance":
        errors.append(
            issue(
                "ai_draft_authority_invalid",
                "AI draft authority must remain proposal_only_not_registry_acceptance.",
                field="aiDraft.authority",
            )
        )

    validate_ai_draft_no_acceptance_decision(draft, errors)
    validate_ai_draft_privacy(_mapping_value(draft.get("privacy")), errors)
    validate_ai_draft_trust_boundary(draft, errors)
    validate_ai_draft_non_goals(draft, errors)
    validate_ai_draft_provider(_mapping_value(draft.get("provider")), errors)
    validate_ai_draft_provider_receipt(_mapping_value(draft.get("providerReceipt")), errors)
    validate_ai_draft_inputs(draft, errors, root)

    package_set = _mapping_value(draft.get("packageSet"))
    package_set_id = package_set.get("packageId")
    if not isinstance(package_set_id, str) or not package_set_id:
        errors.append(
            issue(
                "ai_draft_package_set_id_missing",
                "AI draft packageSet.packageId must be present.",
                field="aiDraft.packageSet.packageId",
            )
        )

    inventory_by_id = ai_draft_inventory_by_package_id(inventory)
    inventory_package_set_id = ai_draft_inventory_package_set_id(inventory_by_id)
    if (
        isinstance(package_set_id, str)
        and isinstance(inventory_package_set_id, str)
        and package_set_id != inventory_package_set_id
    ):
        errors.append(
            issue(
                "ai_draft_package_set_id_mismatch",
                "AI draft packageSet.packageId must match the workspace inventory aggregate id.",
                field="aiDraft.packageSet.packageId",
            )
        )

    selected_members = _list_of_mappings(draft.get("selectedMembers"))
    excluded_packages = _list_of_mappings(draft.get("excludedPackages"))
    relations = _list_of_mappings(draft.get("relations"))
    summary = _mapping_value(draft.get("summary"))
    for key, expected in (
        ("selectedMemberCount", len(selected_members)),
        ("excludedPackageCount", len(excluded_packages)),
        ("relationCount", len(relations)),
    ):
        if summary.get(key) != expected:
            errors.append(
                issue(
                    "ai_draft_summary_count_mismatch",
                    f"AI draft summary.{key} must match proposal record counts.",
                    field=f"aiDraft.summary.{key}",
                )
            )
    if summary.get("errorCount") not in (0, None):
        errors.append(
            issue(
                "ai_draft_summary_errors_present",
                "AI draft summary.errorCount must be zero before SpecPM review use.",
                field="aiDraft.summary.errorCount",
            )
        )

    allowed_paths = ai_draft_allowed_evidence_paths(draft)
    if not allowed_paths:
        errors.append(
            issue(
                "ai_draft_allowed_evidence_missing",
                "AI draft inputs must include compact_model_input evidencePaths.",
                field="aiDraft.inputs",
            )
        )

    validate_ai_draft_evidence_paths(
        list_value(package_set.get("evidencePaths")),
        allowed_paths,
        errors,
        warnings,
        "aiDraft.packageSet.evidencePaths",
    )
    selected_ids = validate_ai_draft_selected_members(
        selected_members,
        inventory_by_id,
        allowed_paths,
        errors,
        warnings,
    )
    excluded_ids = validate_ai_draft_excluded_packages(
        excluded_packages,
        inventory_by_id,
        selected_ids,
        allowed_paths,
        errors,
        warnings,
    )
    validate_ai_draft_relations(
        relations,
        package_set_id,
        selected_ids,
        allowed_paths,
        errors,
        warnings,
    )
    if selected_ids & excluded_ids:
        errors.append(
            issue(
                "ai_draft_package_selected_and_excluded",
                "AI draft packages cannot be both selected and excluded.",
                field="aiDraft.excludedPackages",
            )
        )
    validate_ai_draft_diagnostics(draft, errors, warnings)


def validate_ai_draft_no_acceptance_decision(
    draft: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    for key in ("registryAcceptanceDecision", "acceptanceDecision"):
        if key in draft:
            errors.append(
                issue(
                    "ai_draft_acceptance_decision_not_allowed",
                    "AI draft artifacts must not carry registry acceptance decisions.",
                    field=f"aiDraft.{key}",
                )
            )


def validate_ai_draft_privacy(
    privacy: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    for key in sorted(AI_ENRICHMENT_REQUIRED_PRIVACY_FLAGS):
        if privacy.get(key) is not False:
            errors.append(
                issue(
                    "ai_draft_privacy_flag_invalid",
                    f"AI draft privacy.{key} must be false.",
                    field=f"aiDraft.privacy.{key}",
                )
            )


def validate_ai_draft_trust_boundary(
    draft: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    notes = [item for item in list_value(draft.get("trustBoundary")) if isinstance(item, str)]
    joined = "\n".join(notes).lower()
    if "proposal" not in joined or "specpm remains" not in joined:
        errors.append(
            issue(
                "ai_draft_trust_boundary_invalid",
                "AI draft trustBoundary must keep output proposal-only and SpecPM authoritative.",
                field="aiDraft.trustBoundary",
            )
        )


def validate_ai_draft_non_goals(
    draft: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    non_goals = {item for item in list_value(draft.get("nonGoals")) if isinstance(item, str)}
    missing = sorted(AI_DRAFT_REQUIRED_NON_GOALS - non_goals)
    if missing:
        errors.append(
            issue(
                "ai_draft_non_goals_missing",
                "AI draft nonGoals must exclude generation, acceptance, mutation, and publication: "
                + ", ".join(missing),
                field="aiDraft.nonGoals",
            )
        )


def validate_ai_draft_provider(
    provider: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if not isinstance(provider.get("kind"), str) or not provider["kind"]:
        errors.append(
            issue(
                "ai_draft_provider_kind_missing",
                "AI draft provider.kind must be present for provenance.",
                field="aiDraft.provider.kind",
            )
        )
    if provider.get("execution") not in {"operator_opt_in_local", "not_run_by_spec_harvester"}:
        errors.append(
            issue(
                "ai_draft_provider_execution_invalid",
                "AI draft provider.execution must describe local opt-in or external output.",
                field="aiDraft.provider.execution",
            )
        )


def validate_ai_draft_provider_receipt(
    receipt: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    if not receipt:
        errors.append(
            issue(
                "ai_draft_provider_receipt_missing",
                "AI draft artifacts must include providerReceipt provenance.",
                field="aiDraft.providerReceipt",
            )
        )
        return
    for key in ("rawPromptPersisted", "rawResponsePersisted", "chainOfThoughtPersisted"):
        if key in receipt and receipt[key] is not False:
            errors.append(
                issue(
                    "ai_draft_provider_receipt_privacy_invalid",
                    f"AI draft providerReceipt.{key} must be false when present.",
                    field=f"aiDraft.providerReceipt.{key}",
                )
            )
    if receipt.get("authority") in {"accepted", "registry_authority", "truth"}:
        errors.append(
            issue(
                "ai_draft_provider_receipt_authority_invalid",
                "AI draft providerReceipt is provenance only, not semantic authority.",
                field="aiDraft.providerReceipt.authority",
            )
        )


def validate_ai_draft_inputs(
    draft: dict[str, Any],
    errors: list[dict[str, Any]],
    root: Path | None,
) -> None:
    roles = set()
    for index, item in enumerate(_list_of_mappings(draft.get("inputs"))):
        field = f"aiDraft.inputs[{index}]"
        role = item.get("role")
        if not isinstance(role, str) or not role:
            errors.append(
                issue(
                    "ai_draft_input_role_missing",
                    "AI draft input record must include role.",
                    field=f"{field}.role",
                )
            )
            continue
        roles.add(role)
        path = item.get("path")
        path_scope = item.get("pathScope")
        if path is not None:
            if not isinstance(path, str) or not path:
                errors.append(
                    issue(
                        "ai_draft_input_path_invalid",
                        "AI draft input path must be a non-empty string.",
                        field=f"{field}.path",
                    )
                )
                continue
            if path_scope not in AI_DRAFT_INPUT_PATH_SCOPES:
                errors.append(
                    issue(
                        "ai_draft_input_path_scope_invalid",
                        "AI draft input path must use a known pathScope.",
                        field=f"{field}.pathScope",
                    )
                )
            elif path_scope == "local_path":
                errors.append(
                    issue(
                        "ai_draft_input_path_scope_invalid",
                        "AI draft preflight does not read untrusted local_path inputs.",
                        field=f"{field}.pathScope",
                    )
                )
            elif root is not None:
                validate_ai_draft_input_file(root, item, errors, field)
        if role == "compact_model_input":
            for evidence_index, evidence_path in enumerate(list_value(item.get("evidencePaths"))):
                validate_ai_draft_allowed_path(
                    evidence_path,
                    errors,
                    f"{field}.evidencePaths[{evidence_index}]",
                )
    for role in ("workspace_inventory", "compact_model_input"):
        if role not in roles:
            errors.append(
                issue(
                    "ai_draft_input_role_missing",
                    f"AI draft inputs must include role: {role}.",
                    field="aiDraft.inputs",
                )
            )


def validate_ai_draft_input_file(
    root: Path,
    item: dict[str, Any],
    errors: list[dict[str, Any]],
    field: str,
) -> None:
    path = item.get("path")
    if not isinstance(path, str):
        return
    resolved = resolve_package_set_path(root, path)
    if resolved is None:
        errors.append(
            issue(
                "ai_draft_input_path_escape",
                "AI draft input path escapes the preflight root.",
                field=f"{field}.path",
            )
        )
        return
    if not resolved.is_file():
        errors.append(
            issue(
                "ai_draft_input_file_missing",
                f"AI draft input file is missing: {path}.",
                field=f"{field}.path",
            )
        )
        return
    expected = digest_value(item.get("digest"))
    if expected is not None:
        actual = f"sha256:{sha256_file(resolved)}"
        if expected != actual:
            errors.append(
                issue(
                    "ai_draft_input_digest_mismatch",
                    "AI draft input digest does not match file bytes.",
                    field=f"{field}.digest",
                )
            )


def validate_ai_draft_allowed_path(
    path: Any,
    errors: list[dict[str, Any]],
    field: str,
) -> None:
    if not isinstance(path, str) or not path:
        errors.append(
            issue(
                "ai_draft_allowed_evidence_path_invalid",
                "AI draft compact_model_input evidencePaths must be non-empty strings.",
                field=field,
            )
        )
    elif not is_safe_relative_path(path):
        errors.append(
            issue(
                "ai_draft_allowed_evidence_path_unsafe",
                "AI draft compact_model_input evidencePaths must be safe relative paths.",
                field=field,
            )
        )


def validate_ai_draft_selected_members(
    selected_members: list[dict[str, Any]],
    inventory_by_id: dict[str, dict[str, Any]],
    allowed_paths: set[str],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> set[str]:
    ids: set[str] = set()
    if not selected_members:
        errors.append(
            issue(
                "ai_draft_selected_members_missing",
                "AI draft artifacts must include at least one selected member.",
                field="aiDraft.selectedMembers",
            )
        )
    for index, member in enumerate(selected_members):
        field = f"aiDraft.selectedMembers[{index}]"
        package_id = member.get("packageId")
        if not isinstance(package_id, str) or not package_id:
            errors.append(
                issue(
                    "ai_draft_selected_member_id_missing",
                    "AI draft selected member must include packageId.",
                    field=f"{field}.packageId",
                )
            )
            continue
        if package_id in ids:
            errors.append(
                issue(
                    "ai_draft_selected_member_duplicate",
                    f"Duplicate AI draft selected member packageId: {package_id}.",
                    field=f"{field}.packageId",
                )
            )
        ids.add(package_id)
        inventory_record = inventory_by_id.get(package_id)
        if inventory_by_id and inventory_record is None:
            errors.append(
                issue(
                    "ai_draft_selected_member_not_in_inventory",
                    "Selected member packageId is not present in workspace inventory: "
                    f"{package_id}.",
                    field=f"{field}.packageId",
                )
            )
        validate_ai_draft_inventory_fields(
            member,
            inventory_record or {},
            errors,
            field,
            package_id,
        )
        role = member.get("role")
        if role not in AI_DRAFT_MEMBER_ROLES:
            warnings.append(
                issue(
                    "ai_draft_selected_member_role_unknown",
                    f"Selected member role is outside the documented taxonomy: {role}.",
                    field=f"{field}.role",
                )
            )
        validate_ai_draft_evidence_paths(
            list_value(member.get("evidencePaths")),
            allowed_paths,
            errors,
            warnings,
            f"{field}.evidencePaths",
        )
    return ids


def validate_ai_draft_excluded_packages(
    excluded_packages: list[dict[str, Any]],
    inventory_by_id: dict[str, dict[str, Any]],
    selected_ids: set[str],
    allowed_paths: set[str],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> set[str]:
    ids: set[str] = set()
    for index, excluded in enumerate(excluded_packages):
        field = f"aiDraft.excludedPackages[{index}]"
        package_id = excluded.get("packageId")
        if not isinstance(package_id, str) or not package_id:
            errors.append(
                issue(
                    "ai_draft_excluded_package_id_missing",
                    "AI draft excluded package must include packageId.",
                    field=f"{field}.packageId",
                )
            )
            continue
        if package_id in ids:
            errors.append(
                issue(
                    "ai_draft_excluded_package_duplicate",
                    f"Duplicate AI draft excluded package packageId: {package_id}.",
                    field=f"{field}.packageId",
                )
            )
        ids.add(package_id)
        if package_id in selected_ids:
            errors.append(
                issue(
                    "ai_draft_package_selected_and_excluded",
                    f"Excluded package is also selected as a member: {package_id}.",
                    field=f"{field}.packageId",
                )
            )
        inventory_record = inventory_by_id.get(package_id)
        if inventory_by_id and inventory_record is None:
            errors.append(
                issue(
                    "ai_draft_excluded_package_not_in_inventory",
                    f"Excluded packageId is not present in workspace inventory: {package_id}.",
                    field=f"{field}.packageId",
                )
            )
        validate_ai_draft_inventory_fields(
            excluded,
            inventory_record or {},
            errors,
            field,
            package_id,
        )
        category = excluded.get("category")
        if category not in AI_DRAFT_EXCLUSION_CATEGORIES:
            warnings.append(
                issue(
                    "ai_draft_exclusion_category_unknown",
                    f"Excluded package category is outside the documented taxonomy: {category}.",
                    field=f"{field}.category",
                )
            )
        validate_ai_draft_evidence_paths(
            list_value(excluded.get("evidencePaths")),
            allowed_paths,
            errors,
            warnings,
            f"{field}.evidencePaths",
        )
    return ids


def validate_ai_draft_inventory_fields(
    record: dict[str, Any],
    inventory_record: dict[str, Any],
    errors: list[dict[str, Any]],
    field: str,
    package_id: str,
) -> None:
    if not inventory_record:
        return
    for key in ("sourceTargetPath", "manifestPath"):
        value = record.get(key)
        expected = inventory_record.get(key)
        if isinstance(expected, str) and expected and value != expected:
            errors.append(
                issue(
                    "ai_draft_inventory_field_mismatch",
                    f"AI draft {key} for {package_id} must match workspace inventory.",
                    field=f"{field}.{key}",
                )
            )


def validate_ai_draft_relations(
    relations: list[dict[str, Any]],
    package_set_id: Any,
    selected_ids: set[str],
    allowed_paths: set[str],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    ids: set[str] = set()
    for index, relation in enumerate(relations):
        field = f"aiDraft.relations[{index}]"
        relation_id = relation.get("id")
        relation_type = relation.get("type")
        source_id = relation.get("sourcePackageId")
        target_id = relation.get("targetPackageId")
        if not isinstance(relation_id, str) or not relation_id:
            errors.append(
                issue(
                    "ai_draft_relation_id_missing",
                    "AI draft relation must include id.",
                    field=f"{field}.id",
                )
            )
        elif relation_id in ids:
            errors.append(
                issue(
                    "ai_draft_relation_id_duplicate",
                    f"Duplicate AI draft relation id: {relation_id}.",
                    field=f"{field}.id",
                )
            )
        if isinstance(relation_id, str):
            ids.add(relation_id)
        if relation_type != "contains":
            errors.append(
                issue(
                    "ai_draft_relation_type_unsupported",
                    "AI draft relations must use type contains.",
                    field=f"{field}.type",
                )
            )
        if source_id != package_set_id:
            errors.append(
                issue(
                    "ai_draft_relation_source_not_package_set",
                    "AI draft contains relation source must be packageSet.packageId.",
                    field=f"{field}.sourcePackageId",
                )
            )
        if target_id not in selected_ids:
            errors.append(
                issue(
                    "ai_draft_relation_target_not_selected",
                    f"AI draft relation target is not a selected member: {target_id}.",
                    field=f"{field}.targetPackageId",
                )
            )
        validate_ai_draft_evidence_paths(
            list_value(relation.get("evidencePaths")),
            allowed_paths,
            errors,
            warnings,
            f"{field}.evidencePaths",
        )


def validate_ai_draft_evidence_paths(
    paths: list[Any],
    allowed_paths: set[str],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    field: str,
) -> None:
    if not paths:
        warnings.append(
            issue(
                "ai_draft_evidence_paths_missing",
                "AI draft proposal records should cite evidencePaths.",
                field=field,
            )
        )
        return
    for index, path in enumerate(paths):
        path_field = f"{field}[{index}]"
        if not isinstance(path, str) or not path:
            errors.append(
                issue(
                    "ai_draft_evidence_path_invalid",
                    "AI draft evidencePaths must be non-empty strings.",
                    field=path_field,
                )
            )
        elif not is_safe_relative_path(path):
            errors.append(
                issue(
                    "ai_draft_evidence_path_unsafe",
                    "AI draft evidencePaths must be safe relative paths.",
                    field=path_field,
                )
            )
        elif allowed_paths and path not in allowed_paths:
            errors.append(
                issue(
                    "ai_draft_evidence_path_not_allowlisted",
                    "AI draft evidencePath is not present in compact_model_input allowlist.",
                    field=path_field,
                )
            )


def validate_ai_draft_diagnostics(
    draft: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    diagnostics = _list_of_mappings(draft.get("diagnostics"))
    severity_counts = {"error": 0, "warning": 0}
    for index, diagnostic in enumerate(diagnostics):
        severity = diagnostic.get("severity")
        if severity == "error":
            severity_counts["error"] += 1
            errors.append(
                issue(
                    "ai_draft_diagnostic_error",
                    "AI draft producer diagnostics include an error.",
                    field=f"aiDraft.diagnostics[{index}]",
                )
            )
        elif severity == "warning":
            severity_counts["warning"] += 1
            warnings.append(
                issue(
                    "ai_draft_diagnostic_warning",
                    "AI draft producer diagnostics include a warning.",
                    field=f"aiDraft.diagnostics[{index}]",
                )
            )
        elif severity is not None:
            warnings.append(
                issue(
                    "ai_draft_diagnostic_severity_unknown",
                    "AI draft diagnostic severity is not recognized.",
                    field=f"aiDraft.diagnostics[{index}].severity",
                )
            )
    summary = _mapping_value(draft.get("summary"))
    if summary.get("warningCount") not in (None, severity_counts["warning"]):
        warnings.append(
            issue(
                "ai_draft_summary_warning_count_mismatch",
                "AI draft summary.warningCount does not match diagnostics.",
                field="aiDraft.summary.warningCount",
            )
        )


def load_ai_draft_workspace_inventory(
    draft: dict[str, Any],
    root: Path | None,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    inputs = _list_of_mappings(draft.get("inputs"))
    inventory_input = next(
        (item for item in inputs if item.get("role") == "workspace_inventory"),
        None,
    )
    if inventory_input is None:
        errors.append(
            issue(
                "ai_draft_workspace_inventory_missing",
                "AI draft inputs must include workspace_inventory.",
                field="aiDraft.inputs",
            )
        )
        return {}
    if root is None:
        return {}
    path = inventory_input.get("path")
    if not isinstance(path, str) or not path:
        errors.append(
            issue(
                "ai_draft_workspace_inventory_path_missing",
                "AI draft workspace inventory input must include a non-empty path.",
                field="aiDraft.inputs.workspace_inventory.path",
            )
        )
        return {}
    path_scope = inventory_input.get("pathScope")
    if path_scope not in AI_DRAFT_INPUT_PATH_SCOPES:
        errors.append(
            issue(
                "ai_draft_workspace_inventory_path_scope_invalid",
                "AI draft workspace inventory input must use a known pathScope.",
                field="aiDraft.inputs.workspace_inventory.pathScope",
            )
        )
        return {}
    if path_scope == "local_path":
        errors.append(
            issue(
                "ai_draft_workspace_inventory_path_scope_invalid",
                "AI draft preflight does not read workspace_inventory local_path inputs.",
                field="aiDraft.inputs.workspace_inventory.pathScope",
            )
        )
        return {}
    resolved = resolve_package_set_path(root, path)
    if resolved is None:
        errors.append(
            issue(
                "ai_draft_workspace_inventory_path_escape",
                "AI draft workspace inventory path escapes the preflight root.",
                field="aiDraft.inputs.workspace_inventory.path",
            )
        )
        return {}
    if not resolved.is_file():
        errors.append(
            issue(
                "ai_draft_workspace_inventory_file_missing",
                f"AI draft workspace inventory file is missing: {path}.",
                field="aiDraft.inputs.workspace_inventory.path",
            )
        )
        return {}
    expected = digest_value(inventory_input.get("digest"))
    if expected is not None:
        actual = f"sha256:{sha256_file(resolved)}"
        if expected != actual:
            errors.append(
                issue(
                    "ai_draft_workspace_inventory_digest_mismatch",
                    "AI draft workspace inventory digest does not match file bytes.",
                    field="aiDraft.inputs.workspace_inventory.digest",
                )
            )
    try:
        loaded = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            issue(
                "ai_draft_workspace_inventory_unreadable",
                f"AI draft workspace inventory could not be read as JSON: {exc}.",
                field="aiDraft.inputs.workspace_inventory.path",
            )
        )
        return {}
    if not isinstance(loaded, dict):
        errors.append(
            issue(
                "ai_draft_workspace_inventory_invalid",
                "AI draft workspace inventory must be a JSON object.",
                field="aiDraft.inputs.workspace_inventory.path",
            )
        )
        return {}
    if not workspace_inventory_package_records(loaded):
        warnings.append(
            issue(
                "ai_draft_workspace_inventory_packages_missing",
                "AI draft workspace inventory did not expose package records for alignment.",
                field="workspaceInventory.packages",
            )
        )
    return loaded


def ai_draft_inventory_alignment(
    root: Path | None,
    inventory: dict[str, Any],
    errors: list[dict[str, Any]],
) -> str:
    if root is None:
        return "not_provided"
    if any(
        isinstance(error.get("code"), str)
        and error["code"].startswith("ai_draft_workspace_inventory_")
        for error in errors
    ):
        return "failed"
    if workspace_inventory_package_records(inventory):
        return "verified"
    return "failed"


def ai_draft_allowed_evidence_paths(draft: dict[str, Any]) -> set[str]:
    allowed: set[str] = set()
    for item in _list_of_mappings(draft.get("inputs")):
        if item.get("role") != "compact_model_input":
            continue
        for path in list_value(item.get("evidencePaths")):
            if isinstance(path, str) and path:
                allowed.add(path)
    return allowed


def workspace_inventory_package_records(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(inventory.get("packages"))


def ai_draft_inventory_by_package_id(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for package in workspace_inventory_package_records(inventory):
        package_id = package.get("proposedSpecpmPackageId")
        if isinstance(package_id, str) and package_id:
            records[package_id] = {
                "packageId": package_id,
                "inventoryRole": package.get("role"),
                "sourceTargetPath": package.get("sourceTargetPath"),
                "manifestPath": package.get("manifestPath"),
            }
    return records


def ai_draft_inventory_package_set_id(inventory_by_id: dict[str, dict[str, Any]]) -> str | None:
    for package_id, record in inventory_by_id.items():
        if record.get("inventoryRole") == "workspace":
            return package_id
    return next(iter(inventory_by_id), None)


def package_set_handoff_member_ids(handoff: dict[str, Any]) -> set[str]:
    return {
        package_id
        for member in _list_of_mappings(handoff.get("members"))
        if isinstance((package_id := member.get("packageId")), str) and package_id
    }


def _extract_json_payloads(body: str) -> list[Any]:
    payloads: list[Any] = []
    for match in JSON_FENCE_PATTERN.finditer(body):
        parsed = _parse_json_or_none(match.group(1))
        if parsed is not None:
            payloads.append(parsed)
    stripped = body.strip()
    if stripped.startswith("{"):
        parsed = _parse_json_or_none(stripped)
        if parsed is not None:
            payloads.append(parsed)
    return payloads


def _parse_json_or_none(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _find_list_payload(payloads: list[Any], key: str) -> list[Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and isinstance(payload.get(key), list):
            return payload[key]
    return None


def _find_package_set_handoff_payload(payloads: list[Any]) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and (
            payload.get("kind") == PACKAGE_SET_HANDOFF_KIND
            or payload.get("apiVersion") == PACKAGE_SET_HANDOFF_API_VERSION
            or (
                isinstance(payload.get("packageSet"), dict)
                and isinstance(payload.get("members"), list)
                and isinstance(payload.get("relations"), list)
            )
        ):
            return payload
    return None


def _find_package_set_ai_enrichment_payload(payloads: list[Any]) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and (
            payload.get("kind") == PACKAGE_SET_AI_ENRICHMENT_KIND
            or payload.get("apiVersion") == PACKAGE_SET_AI_ENRICHMENT_API_VERSION
            or (
                isinstance(payload.get("packageSet"), dict)
                and isinstance(payload.get("proposals"), list)
                and payload.get("authority") == "proposal_only_not_registry_acceptance"
            )
        ):
            return payload
    return None


def _find_package_set_ai_draft_payload(payloads: list[Any]) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and (
            payload.get("kind") == PACKAGE_SET_AI_DRAFT_KIND
            or payload.get("apiVersion") == PACKAGE_SET_AI_DRAFT_API_VERSION
            or (
                isinstance(payload.get("packageSet"), dict)
                and isinstance(payload.get("selectedMembers"), list)
                and payload.get("authority") == "proposal_only_not_registry_acceptance"
            )
        ):
            return payload
    return None


def _find_refresh_decision_payload(payloads: list[Any]) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and (
            payload.get("kind") == REFRESH_DECISION_KIND
            or (
                payload.get("apiVersion") == REFRESH_DECISION_API_VERSION
                and isinstance(payload.get("decision"), dict)
                and isinstance(payload.get("generatedContractFiles"), list)
            )
        ):
            return payload
    return None


def _find_baseline_submission_handoff_payload(payloads: list[Any]) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and (
            payload.get("kind") == BASELINE_SUBMISSION_HANDOFF_KIND
            or payload.get("apiVersion") == BASELINE_SUBMISSION_HANDOFF_API_VERSION
            or (
                isinstance(payload.get("baselineWorkflow"), dict)
                and isinstance(payload.get("authority"), dict)
                and payload.get("status") in VALID_BASELINE_HANDOFF_STATUSES
            )
        ):
            return payload
    return None


def _find_selected_candidate_handoff_payload(payloads: list[Any]) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and (
            payload.get("kind")
            in {
                SELECTED_CANDIDATE_HANDOFF_KIND,
                REFRESHED_SELECTED_CANDIDATE_HANDOFF_KIND,
            }
            or payload.get("apiVersion")
            in {
                SELECTED_CANDIDATE_HANDOFF_API_VERSION,
                REFRESHED_SELECTED_CANDIDATE_HANDOFF_API_VERSION,
            }
            or (
                isinstance(payload.get("selectedCandidates"), list)
                and isinstance(payload.get("deferredCandidates"), list)
                and payload.get("authority") == "producer_preview_evidence_only"
            )
        ):
            return payload
    return None


def _find_mapping_payload(payloads: list[Any], key: str) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and isinstance(payload.get(key), dict):
            return payload[key]
    return None


def _mapping_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def same_materialized_source(left: dict[str, str], right: dict[str, str]) -> bool:
    if "path" in left and set(left) == {"path"}:
        return set(right) == {"path"} and left["path"] == right["path"]
    return set(left) == set(right) and all(left[key] == right[key] for key in left)


def read_local_accepted_manifest_sources(manifest_path: Path) -> list[dict[str, str]]:
    if not manifest_path.is_file():
        return []
    try:
        loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return []
    if not isinstance(loaded, dict) or not isinstance(loaded.get("packages"), list):
        return []
    sources: list[dict[str, str]] = []
    for item in loaded["packages"]:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if isinstance(path, str) and path:
            sources.append({"path": path})
    return sources


def resolve_package_set_path(root: Path, path: str) -> Path | None:
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    root_resolved = root.resolve(strict=False)
    candidate = (root_resolved / relative).resolve(strict=False)
    if not candidate.is_relative_to(root_resolved):
        return None
    return candidate


def root_join(root: Path, base: Path, *parts: str) -> Path:
    if base.is_absolute():
        return base.joinpath(*parts)
    return root.joinpath(base, *parts)


def repo_relative_path(root: Path, path: Path) -> str | None:
    root_resolved = root.resolve(strict=False)
    resolved = path.resolve(strict=False)
    if not resolved.is_relative_to(root_resolved):
        return None
    relative = resolved.relative_to(root_resolved).as_posix()
    if not is_safe_relative_path(relative):
        return None
    return relative


def refresh_contract_files(package_dir: Path) -> list[Path]:
    paths: list[Path] = []
    manifest = package_dir / "specpm.yaml"
    if manifest.is_file():
        paths.append(manifest)
    specs_dir = package_dir / "specs"
    if specs_dir.is_dir():
        paths.extend(sorted(specs_dir.glob("*.spec.yaml")))
    return paths


def source_revisions_from_contracts(paths: list[Path]) -> set[str]:
    revisions: set[str] = set()
    for path in paths:
        if path.suffix not in {".yaml", ".yml"}:
            continue
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(loaded, dict):
            continue
        collect_source_revisions(loaded, revisions)
    return revisions


def collect_source_revisions(value: Any, revisions: set[str]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"sourceRevision", "revision"} and isinstance(nested, str):
                if re.fullmatch(r"[a-f0-9]{40}", nested):
                    revisions.add(nested)
            else:
                collect_source_revisions(nested, revisions)
    elif isinstance(value, list):
        for item in value:
            collect_source_revisions(item, revisions)


def refresh_decision_id(
    package_id: str,
    version: str,
    source_revision: str,
    status: str,
) -> str:
    safe_package_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", package_id).strip("-") or "unknown"
    safe_version = re.sub(r"[^a-zA-Z0-9_.-]+", "-", version).strip("-") or "unknown"
    revision_prefix = source_revision[:12] if source_revision else "unknown"
    return (
        f"specpm-refresh-decision-draft-{safe_package_id}-{safe_version}-{revision_prefix}-{status}"
    )


def refresh_decision_fresh_run_summary(update_needed: bool) -> str:
    if update_needed:
        return (
            "Fresh generated candidate comparison requires maintainer review before any "
            "registry update."
        )
    return (
        "Fresh generated candidate comparison reproduced the current generated contract "
        "files; no registry update is proposed."
    )


def refresh_decision_review_summary(update_needed: bool) -> str:
    if update_needed:
        return (
            "Prepared as review evidence only; maintainer review must decide whether a "
            "curated update, generated candidate update, or package version change is required."
        )
    return (
        "Prepared as no-update review evidence because current and fresh generated "
        "contract-bearing files match."
    )


def candidate_tree_contains_symlink(path: Path) -> bool:
    if path.is_symlink():
        return True
    return any(item.is_symlink() for item in path.rglob("*"))


def digest_value(digest: Any) -> str | None:
    if isinstance(digest, str) and digest.startswith("sha256:"):
        return digest
    if isinstance(digest, dict):
        algorithm = digest.get("algorithm")
        value = digest.get("value")
        if algorithm == "sha256" and isinstance(value, str) and value:
            return f"sha256:{value}"
    return None


def is_safe_relative_path(path: str) -> bool:
    relative = Path(path)
    return not relative.is_absolute() and ".." not in relative.parts and "\\" not in path


def package_output_path(
    output_root: Path,
    package_id: str,
    version: str,
    errors: list[dict[str, Any]],
) -> Path:
    if output_root.is_absolute() or ".." in output_root.parts:
        errors.append(
            issue(
                "package_set_materialization_output_root_invalid",
                "Accepted-source outputRoot must be a repo-relative path without '..'.",
                field="outputRoot",
            )
        )
    if any(part in package_id for part in ("/", "\\")) or package_id in {"", ".", ".."}:
        errors.append(
            issue(
                "package_set_materialization_package_id_unsafe",
                f"Selected package ID cannot be used as an output path component: {package_id}.",
                field="selection.packageIds",
            )
        )
    if any(part in version for part in ("/", "\\")) or version in {"", ".", ".."}:
        errors.append(
            issue(
                "package_set_materialization_version_unsafe",
                f"Selected package version cannot be used as an output path component: {version}.",
                field="specpm.yaml.metadata.version",
            )
        )
    root_resolved = output_root.resolve(strict=False)
    candidate = (root_resolved / package_id / version).resolve(strict=False)
    if not candidate.is_relative_to(root_resolved):
        errors.append(
            issue(
                "package_set_materialization_output_escape",
                "Accepted-source output path escapes outputRoot.",
                field="outputRoot",
            )
        )
    return output_root / package_id / version


def read_manifest_metadata(
    manifest: Path,
    errors: list[dict[str, Any]],
    package_id: str,
) -> dict[str, str]:
    try:
        loaded = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        errors.append(
            issue(
                "package_set_materialization_manifest_unreadable",
                f"Selected package {package_id} manifest could not be read: {exc}.",
                field="specpm.yaml",
            )
        )
        return {}
    if not isinstance(loaded, dict) or not isinstance(loaded.get("metadata"), dict):
        return {}
    metadata = loaded["metadata"]
    result: dict[str, str] = {}
    if isinstance(metadata.get("id"), str):
        result["package_id"] = metadata["id"]
    if isinstance(metadata.get("version"), str):
        result["version"] = metadata["version"]
    return result


def read_manifest_package_id(
    manifest: Path,
    warnings: list[dict[str, Any]],
    field: str,
) -> str | None:
    try:
        loaded = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        warnings.append(
            issue(
                "package_set_member_manifest_unreadable",
                f"Package-set member manifest could not be read: {exc}.",
                field=field,
            )
        )
        return None
    if not isinstance(loaded, dict):
        return None
    metadata = loaded.get("metadata")
    if not isinstance(metadata, dict):
        return None
    package_id = metadata.get("id")
    return package_id if isinstance(package_id, str) else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def issue(code: str, message: str, *, field: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if field:
        payload["field"] = field
    return payload
