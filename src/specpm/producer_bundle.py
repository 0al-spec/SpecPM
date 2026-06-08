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

JSON_FENCE_PATTERN = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)


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
