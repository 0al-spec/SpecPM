from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.tokens import AliasToken, AnchorToken, TagToken

SUPPORTED_API_VERSION = "specpm.dev/v0.1"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
KNOWN_INTERFACE_KINDS = {
    "library",
    "cli",
    "http",
    "file",
    "event",
    "queue",
    "plugin",
    "config",
    "schema",
    "unknown",
}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    file: str | None = None
    field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.file is not None:
            payload["file"] = self.file
        if self.field is not None:
            payload["field"] = self.field
        return payload


class RestrictedYamlError(Exception):
    def __init__(self, issues: list[Issue]):
        super().__init__("restricted YAML parse failed")
        self.issues = issues


def validate_package(package_dir: Path) -> dict[str, Any]:
    root = package_dir.resolve()
    errors: list[Issue] = []
    warnings: list[Issue] = []
    checked_files: list[str] = []
    manifest: dict[str, Any] | None = None
    specs: list[tuple[str, dict[str, Any]]] = []

    manifest_path = root / "specpm.yaml"
    if not manifest_path.is_file():
        errors.append(
            Issue("error", "manifest_missing", "Package manifest specpm.yaml is missing.")
        )
    else:
        checked_files.append("specpm.yaml")
        try:
            loaded = load_restricted_yaml(manifest_path, root)
            if not isinstance(loaded, dict):
                errors.append(
                    Issue(
                        "error",
                        "manifest_not_mapping",
                        "Package manifest must be a YAML mapping.",
                        "specpm.yaml",
                    )
                )
            else:
                manifest = loaded
        except RestrictedYamlError as exc:
            errors.extend(exc.issues)

    if manifest is not None:
        validate_manifest(manifest, errors, warnings)
        for spec_path in iter_manifest_spec_paths(manifest, errors):
            resolved = resolve_inside(root, spec_path)
            if resolved is None:
                errors.append(
                    Issue(
                        "error",
                        "path_escape",
                        f"Referenced spec path escapes package root: {spec_path}",
                        "specpm.yaml",
                        "specs",
                    )
                )
                continue
            rel = relative_path(root, resolved)
            if rel not in checked_files:
                checked_files.append(rel)
            if not resolved.is_file():
                errors.append(
                    Issue(
                        "error",
                        "spec_missing",
                        f"Referenced BoundarySpec does not exist: {spec_path}",
                        "specpm.yaml",
                        "specs",
                    )
                )
                continue
            try:
                loaded_spec = load_restricted_yaml(resolved, root)
                if not isinstance(loaded_spec, dict):
                    errors.append(
                        Issue(
                            "error",
                            "spec_not_mapping",
                            "BoundarySpec document must be a YAML mapping.",
                            rel,
                        )
                    )
                    continue
                specs.append((rel, loaded_spec))
            except RestrictedYamlError as exc:
                errors.extend(exc.issues)

    provided_by_specs: set[str] = set()
    spec_ids: list[str] = []
    for rel, spec in specs:
        provided_by_specs.update(validate_boundary_spec(rel, spec, root, errors, warnings))
        spec_id = get_field(spec, "metadata.id")
        if isinstance(spec_id, str):
            spec_ids.append(spec_id)

    warn_duplicates(spec_ids, "duplicate_spec_id", "Duplicate BoundarySpec id", warnings)

    manifest_capabilities = []
    if manifest is not None:
        manifest_capabilities = capability_ids(get_field(manifest, "index.provides.capabilities"))
        for capability_id in manifest_capabilities:
            if capability_id not in provided_by_specs:
                errors.append(
                    Issue(
                        "error",
                        "manifest_capability_not_declared",
                        f"Manifest capability is not declared by any BoundarySpec: {capability_id}",
                        "specpm.yaml",
                        "index.provides.capabilities",
                    )
                )

    status = "invalid" if errors else "warning_only" if warnings else "valid"
    identity = package_identity(manifest)
    return {
        "status": status,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": [issue.to_dict() for issue in errors],
        "warnings": [issue.to_dict() for issue in warnings],
        "package_identity": identity,
        "capabilities": sorted(set(manifest_capabilities or provided_by_specs)),
        "checked_files": sorted(checked_files),
    }


def inspect_package(package_dir: Path) -> dict[str, Any]:
    root = package_dir.resolve()
    validation = validate_package(root)
    manifest = try_load_mapping(root / "specpm.yaml", root)
    boundary_specs: list[dict[str, Any]] = []

    if manifest is not None:
        for spec_path in iter_manifest_spec_paths(manifest, []):
            resolved = resolve_inside(root, spec_path)
            if resolved is None or not resolved.is_file():
                continue
            spec = try_load_mapping(resolved, root)
            if spec is None:
                continue
            boundary_specs.append(summarize_boundary_spec(relative_path(root, resolved), spec))

    return {
        "package": summarize_manifest(manifest),
        "boundary_specs": boundary_specs,
        "validation": validation,
    }


def list_inbox(root: Path) -> dict[str, Any]:
    inbox_root = root.resolve()
    bundles = []
    if inbox_root.is_dir():
        for child in sorted(inbox_root.iterdir(), key=lambda item: item.name):
            if child.is_dir() and (child / "specpm.yaml").is_file():
                inspection = inspect_package(child)
                manifest = try_load_mapping(child / "specpm.yaml", child)
                handoff = load_handoff(child)
                bundles.append(
                    {
                        "package_id": child.name,
                        "path": str(child),
                        "package_identity": inspection["validation"].get("package_identity"),
                        "validation_status": inspection["validation"]["status"],
                        "inbox_status": classify_inbox_status(
                            manifest, handoff, inspection["validation"]["status"]
                        ),
                        "handoff": handoff,
                    }
                )
    return {"root": str(inbox_root), "bundles": bundles}


def inspect_inbox_bundle(root: Path, package_id: str) -> dict[str, Any]:
    bundle_path = root.resolve() / package_id
    if not bundle_path.is_dir():
        return {
            "found": False,
            "package_id": package_id,
            "path": str(bundle_path),
            "inbox_status": "missing",
        }

    inspection = inspect_package(bundle_path)
    manifest = try_load_mapping(bundle_path / "specpm.yaml", bundle_path)
    handoff = load_handoff(bundle_path)
    return {
        "found": True,
        "package_id": package_id,
        "path": str(bundle_path),
        "inbox_status": classify_inbox_status(
            manifest, handoff, inspection["validation"]["status"]
        ),
        "handoff": handoff,
        "inspection": inspection,
    }


def load_restricted_yaml(path: Path, package_root: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    rel = relative_path(package_root, path)
    issues: list[Issue] = []

    try:
        for token in yaml.scan(text):
            if isinstance(token, AnchorToken):
                issues.append(
                    Issue(
                        "error",
                        "yaml_anchor_unsupported",
                        "YAML anchors are not supported in SpecPM MVP packages.",
                        rel,
                    )
                )
            elif isinstance(token, AliasToken):
                issues.append(
                    Issue(
                        "error",
                        "yaml_alias_unsupported",
                        "YAML aliases are not supported in SpecPM MVP packages.",
                        rel,
                    )
                )
            elif isinstance(token, TagToken):
                issues.append(
                    Issue(
                        "error",
                        "yaml_tag_unsupported",
                        "YAML custom tags are not supported in SpecPM MVP packages.",
                        rel,
                    )
                )
    except yaml.YAMLError as exc:
        raise RestrictedYamlError([yaml_error_issue("yaml_parse_error", exc, rel)]) from exc

    if issues:
        raise RestrictedYamlError(issues)

    try:
        docs = list(yaml.safe_load_all(text))
    except yaml.YAMLError as exc:
        raise RestrictedYamlError([yaml_error_issue("yaml_parse_error", exc, rel)]) from exc

    if len(docs) != 1:
        raise RestrictedYamlError(
            [
                Issue(
                    "error",
                    "yaml_multiple_documents",
                    "SpecPM MVP packages must use exactly one YAML document per file.",
                    rel,
                )
            ]
        )

    json_issue = find_non_json_value(docs[0])
    if json_issue is not None:
        raise RestrictedYamlError(
            [
                Issue(
                    "error",
                    "yaml_non_json_value",
                    f"YAML value is not JSON-compatible at {json_issue}.",
                    rel,
                )
            ]
        )

    return docs[0]


def validate_manifest(manifest: dict[str, Any], errors: list[Issue], warnings: list[Issue]) -> None:
    required_fields = [
        "apiVersion",
        "kind",
        "metadata.id",
        "metadata.name",
        "metadata.version",
        "metadata.summary",
        "metadata.license",
        "specs",
        "index.provides.capabilities",
    ]
    for field in required_fields:
        require_field(manifest, field, errors, "specpm.yaml")

    if get_field(manifest, "apiVersion") != SUPPORTED_API_VERSION:
        errors.append(
            Issue(
                "error",
                "unsupported_api_version",
                f"Manifest apiVersion must be {SUPPORTED_API_VERSION}.",
                "specpm.yaml",
                "apiVersion",
            )
        )
    if get_field(manifest, "kind") != "SpecPackage":
        errors.append(
            Issue(
                "error",
                "invalid_kind",
                "Manifest kind must be SpecPackage.",
                "specpm.yaml",
                "kind",
            )
        )

    validate_id(get_field(manifest, "metadata.id"), "package_id_invalid", errors, "specpm.yaml")
    validate_semver(
        get_field(manifest, "metadata.version"), "package_version_invalid", errors, "specpm.yaml"
    )
    warn_empty_summary(
        get_field(manifest, "metadata.summary"), warnings, "specpm.yaml", "metadata.summary"
    )
    if manifest.get("preview_only") is True:
        warnings.append(
            Issue(
                "warning",
                "preview_only_package",
                "Package is marked preview_only and should be reviewed before publication.",
                "specpm.yaml",
                "preview_only",
            )
        )

    capabilities = get_field(manifest, "index.provides.capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append(
            Issue(
                "error",
                "manifest_capabilities_invalid",
                "Manifest index.provides.capabilities must be a non-empty list.",
                "specpm.yaml",
                "index.provides.capabilities",
            )
        )
    else:
        for index, entry in enumerate(capabilities):
            if isinstance(entry, str):
                continue
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                continue
            errors.append(
                Issue(
                    "error",
                    "manifest_capability_entry_invalid",
                    "Manifest capability entries must be strings or mappings "
                    "with a string id field.",
                    "specpm.yaml",
                    f"index.provides.capabilities.{index}",
                )
            )

    manifest_capability_ids = capability_ids(capabilities)
    for capability_id in manifest_capability_ids:
        validate_id(capability_id, "capability_id_invalid", errors, "specpm.yaml")
    warn_duplicates(
        manifest_capability_ids,
        "duplicate_manifest_capability",
        "Duplicate manifest capability",
        warnings,
    )


def validate_boundary_spec(
    rel: str,
    spec: dict[str, Any],
    root: Path,
    errors: list[Issue],
    warnings: list[Issue],
) -> set[str]:
    required_fields = [
        "apiVersion",
        "kind",
        "metadata.id",
        "metadata.title",
        "metadata.version",
        "intent.summary",
        "scope.boundedContext",
        "provides.capabilities",
        "interfaces",
        "evidence",
    ]
    for field in required_fields:
        require_field(spec, field, errors, rel)

    if get_field(spec, "apiVersion") != SUPPORTED_API_VERSION:
        errors.append(
            Issue(
                "error",
                "unsupported_api_version",
                f"BoundarySpec apiVersion must be {SUPPORTED_API_VERSION}.",
                rel,
                "apiVersion",
            )
        )
    if get_field(spec, "kind") != "BoundarySpec":
        errors.append(
            Issue("error", "invalid_kind", "BoundarySpec kind must be BoundarySpec.", rel, "kind")
        )

    validate_id(get_field(spec, "metadata.id"), "spec_id_invalid", errors, rel)
    validate_semver(get_field(spec, "metadata.version"), "spec_version_invalid", errors, rel)
    warn_empty_summary(get_field(spec, "intent.summary"), warnings, rel, "intent.summary")

    provided = capability_ids(get_field(spec, "provides.capabilities"))
    if not provided:
        errors.append(
            Issue(
                "error",
                "spec_capabilities_invalid",
                "BoundarySpec provides.capabilities must contain at least one capability.",
                rel,
                "provides.capabilities",
            )
        )
    for capability_id in provided:
        validate_id(capability_id, "capability_id_invalid", errors, rel)
    warn_duplicates(provided, "duplicate_spec_capability", "Duplicate spec capability", warnings)

    for capability_id in capability_ids(get_field(spec, "requires.capabilities")):
        validate_id(capability_id, "capability_id_invalid", errors, rel)
        warnings.append(
            Issue(
                "warning",
                "required_capability_unresolved",
                f"Required capability is not resolved by MVP validation: {capability_id}",
                rel,
                "requires.capabilities",
            )
        )

    validate_interfaces(rel, spec, warnings)
    validate_evidence_paths(rel, spec, root, warnings, errors)
    return set(provided)


def validate_interfaces(rel: str, spec: dict[str, Any], warnings: list[Issue]) -> None:
    interfaces = get_field(spec, "interfaces")
    if not isinstance(interfaces, dict):
        return
    for direction in ("inbound", "outbound"):
        items = interfaces.get(direction, [])
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if isinstance(kind, str) and kind not in KNOWN_INTERFACE_KINDS:
                warnings.append(
                    Issue(
                        "warning",
                        "unknown_interface_kind",
                        f"Unknown interface kind: {kind}",
                        rel,
                        f"interfaces.{direction}.{index}.kind",
                    )
                )


def validate_evidence_paths(
    rel: str,
    spec: dict[str, Any],
    root: Path,
    warnings: list[Issue],
    errors: list[Issue],
) -> None:
    evidence = get_field(spec, "evidence")
    if not isinstance(evidence, list):
        errors.append(
            Issue(
                "error",
                "evidence_invalid",
                "BoundarySpec evidence must be a list.",
                rel,
                "evidence",
            )
        )
        return

    if evidence and all(
        isinstance(item, dict) and item.get("kind") == "manual_assertion" for item in evidence
    ):
        warnings.append(
            Issue(
                "warning",
                "manual_assertion_only_evidence",
                "BoundarySpec evidence contains only manual assertions.",
                rel,
                "evidence",
            )
        )

    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            warnings.append(
                Issue(
                    "warning",
                    "evidence_entry_invalid",
                    "Evidence entries should be mappings.",
                    rel,
                    f"evidence.{index}",
                )
            )
            continue
        evidence_path = item.get("path")
        if not isinstance(evidence_path, str):
            continue
        resolved = resolve_inside(root, evidence_path)
        if resolved is None:
            errors.append(
                Issue(
                    "error",
                    "path_escape",
                    f"Evidence path escapes package root: {evidence_path}",
                    rel,
                    f"evidence.{index}.path",
                )
            )
            continue
        if not resolved.exists():
            warnings.append(
                Issue(
                    "warning",
                    "evidence_path_missing",
                    f"Evidence path does not exist: {evidence_path}",
                    rel,
                    f"evidence.{index}.path",
                )
            )


def iter_manifest_spec_paths(manifest: dict[str, Any], errors: list[Issue]) -> list[str]:
    specs = manifest.get("specs")
    if not isinstance(specs, list) or not specs:
        errors.append(
            Issue(
                "error",
                "manifest_specs_invalid",
                "Manifest specs must be a non-empty list.",
                "specpm.yaml",
                "specs",
            )
        )
        return []

    paths: list[str] = []
    for index, item in enumerate(specs):
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.append(item["path"])
        else:
            errors.append(
                Issue(
                    "error",
                    "manifest_spec_entry_invalid",
                    "Manifest specs entries must be strings or mappings with a path field.",
                    "specpm.yaml",
                    f"specs.{index}",
                )
            )
    return paths


def summarize_manifest(manifest: dict[str, Any] | None) -> dict[str, Any]:
    if manifest is None:
        return {}
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    return {
        "identity": package_identity(manifest),
        "name": metadata.get("name"),
        "summary": metadata.get("summary"),
        "license": metadata.get("license"),
        "capabilities": capability_ids(get_field(manifest, "index.provides.capabilities")),
        "required_capabilities": capability_ids(get_field(manifest, "index.requires.capabilities")),
        "compatibility": manifest.get("compatibility", {}),
        "preview_only": manifest.get("preview_only", False),
        "keywords": manifest.get("keywords", []),
    }


def summarize_boundary_spec(rel: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": rel,
        "id": get_field(spec, "metadata.id"),
        "title": get_field(spec, "metadata.title"),
        "version": get_field(spec, "metadata.version"),
        "status": get_field(spec, "metadata.status"),
        "intent_summary": get_field(spec, "intent.summary"),
        "bounded_context": get_field(spec, "scope.boundedContext"),
        "provides": capability_ids(get_field(spec, "provides.capabilities")),
        "requires": capability_ids(get_field(spec, "requires.capabilities")),
        "interfaces": spec.get("interfaces", {}),
        "constraints": spec.get("constraints", []),
        "evidence": spec.get("evidence", []),
        "provenance": spec.get("provenance", {}),
    }


def classify_inbox_status(
    manifest: dict[str, Any] | None,
    handoff: dict[str, Any] | None,
    validation_status: str,
) -> str:
    if validation_status == "invalid":
        return "invalid"
    if manifest and manifest.get("preview_only") is True:
        return "draft_visible"
    if handoff and handoff.get("handoff_status") == "draft_preview_only":
        return "draft_visible"
    return "ready_for_review"


def load_handoff(bundle_path: Path) -> dict[str, Any] | None:
    handoff_path = bundle_path / "handoff.json"
    if not handoff_path.is_file():
        return None
    try:
        loaded = json.loads(handoff_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "invalid_json"}
    return loaded if isinstance(loaded, dict) else {"status": "invalid_json"}


def try_load_mapping(path: Path, root: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        loaded = load_restricted_yaml(path, root)
    except RestrictedYamlError:
        return None
    return loaded if isinstance(loaded, dict) else None


def require_field(data: dict[str, Any], field: str, errors: list[Issue], file: str) -> None:
    value = get_field(data, field)
    if value is None:
        errors.append(
            Issue(
                "error",
                "required_field_missing",
                f"Required field is missing: {field}",
                file,
                field,
            )
        )


def get_field(data: Any, field: str) -> Any:
    current = data
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def capability_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    ids: list[str] = []
    for item in value:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.append(item["id"])
    return ids


def validate_id(value: Any, code: str, errors: list[Issue], file: str) -> None:
    if not isinstance(value, str) or not ID_RE.match(value):
        errors.append(
            Issue(
                "error",
                code,
                "Identifier must match ^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$.",
                file,
            )
        )


def validate_semver(value: Any, code: str, errors: list[Issue], file: str) -> None:
    if not isinstance(value, str) or not SEMVER_RE.match(value):
        errors.append(Issue("error", code, "Version must be valid SemVer 2.0.0.", file))


def warn_empty_summary(value: Any, warnings: list[Issue], file: str, field: str) -> None:
    if isinstance(value, str) and not value.strip():
        warnings.append(
            Issue("warning", "empty_summary", "Summary should not be empty.", file, field)
        )


def warn_duplicates(
    values: list[str],
    code: str,
    message_prefix: str,
    warnings: list[Issue],
) -> None:
    seen: set[str] = set()
    warned: set[str] = set()
    for value in values:
        if value in seen and value not in warned:
            warnings.append(Issue("warning", code, f"{message_prefix}: {value}"))
            warned.add(value)
        seen.add(value)


def package_identity(manifest: dict[str, Any] | None) -> dict[str, Any] | None:
    if not manifest:
        return None
    metadata = manifest.get("metadata")
    if not isinstance(metadata, dict):
        return None
    return {
        "package_id": metadata.get("id"),
        "name": metadata.get("name"),
        "version": metadata.get("version"),
    }


def resolve_inside(root: Path, rel_path: str) -> Path | None:
    candidate = Path(rel_path)
    if candidate.is_absolute():
        return None
    resolved_root = root.resolve()
    resolved_candidate = (resolved_root / candidate).resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved_candidate


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def yaml_error_issue(code: str, exc: yaml.YAMLError, rel: str) -> Issue:
    mark = getattr(exc, "problem_mark", None)
    suffix = ""
    if mark is not None:
        suffix = f" at line {mark.line + 1}, column {mark.column + 1}"
    problem = getattr(exc, "problem", None) or str(exc)
    return Issue("error", code, f"{problem}{suffix}", rel)


def find_non_json_value(value: Any, path: str = "$") -> str | None:
    if value is None or isinstance(value, str | bool | int):
        return None
    if isinstance(value, float):
        return None if math.isfinite(value) else path
    if isinstance(value, list):
        for index, item in enumerate(value):
            issue = find_non_json_value(item, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                return f"{path}.{key!r}"
            issue = find_non_json_value(item, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    return path
