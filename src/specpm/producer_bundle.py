from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

PRODUCER_BUNDLE_PREFLIGHT_KIND = "SpecPMProducerBundlePreflightReport"
PRODUCER_BUNDLE_PREFLIGHT_SCHEMA_VERSION = 1

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
    producer_links = _find_list_payload(payloads, "producerEvidenceLinks")
    registry_decision = _find_mapping_payload(payloads, "registryAcceptanceDecision")

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if producer_links is None:
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

    role_map = validate_producer_evidence_links(producer_links, errors, warnings, root)
    validate_registry_acceptance_decision(registry_decision, errors, warnings)

    return {
        "kind": PRODUCER_BUNDLE_PREFLIGHT_KIND,
        "schemaVersion": PRODUCER_BUNDLE_PREFLIGHT_SCHEMA_VERSION,
        "status": "failed" if errors else ("warning" if warnings else "passed"),
        "body": str(body_path),
        "root": str(root) if root else None,
        "summary": {
            "producerEvidenceRoleCount": len(role_map),
            "errorCount": len(errors),
            "warningCount": len(warnings),
        },
        "producerEvidenceRoles": sorted(role_map),
        "registryAcceptanceDecision": {
            "status": registry_decision.get("status"),
            "recordKind": registry_decision.get("recordKind"),
            "producerReceiptAuthority": registry_decision.get("producerReceiptAuthority"),
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


def _find_mapping_payload(payloads: list[Any], key: str) -> dict[str, Any] | None:
    for payload in payloads:
        if isinstance(payload, dict) and isinstance(payload.get(key), dict):
            return payload[key]
    return None


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
