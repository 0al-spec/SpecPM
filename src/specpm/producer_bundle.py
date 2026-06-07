from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

PRODUCER_BUNDLE_PREFLIGHT_KIND = "SpecPMProducerBundlePreflightReport"
PRODUCER_BUNDLE_PREFLIGHT_SCHEMA_VERSION = 1
PACKAGE_SET_HANDOFF_API_VERSION = "spec-harvester.package-set-handoff-proposal/v0"
PACKAGE_SET_HANDOFF_KIND = "SpecHarvesterPackageSetHandoffProposal"

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

JSON_FENCE_PATTERN = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def preflight_producer_bundle(body_path: Path, root: Path | None = None) -> dict[str, Any]:
    body = body_path.read_text(encoding="utf-8")
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


def resolve_package_set_path(root: Path, path: str) -> Path | None:
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve(strict=False)
    if not candidate.is_relative_to(root_resolved):
        return None
    return candidate


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
