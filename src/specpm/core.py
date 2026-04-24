from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import tarfile
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.tokens import AliasToken, AnchorToken, TagToken

SUPPORTED_API_VERSION = "specpm.dev/v0.1"
INDEX_SCHEMA_VERSION = 1
LOCK_SCHEMA_VERSION = 1
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
KNOWN_EFFECT_KINDS = {
    "filesystem_read",
    "filesystem_write",
    "network_read",
    "network_write",
    "database_read",
    "database_write",
    "process_spawn",
    "environment_read",
    "environment_write",
    "log_write",
    "event_emit",
    "message_publish",
    "state_mutation",
    "unknown",
}
KNOWN_EVIDENCE_KINDS = {
    "documentation",
    "test",
    "source",
    "example",
    "schema",
    "foreign_spec",
    "package_manifest",
    "adr",
    "commit",
    "manual_assertion",
    "unknown",
}
KNOWN_FOREIGN_ARTIFACT_ROLES = {
    "primary_intent_source",
    "api_contract",
    "behavioral_evidence",
    "implementation_hint",
    "documentation",
    "unknown",
}
KNOWN_CONSTRAINT_LEVELS = {"MUST", "SHOULD", "MAY"}
KNOWN_CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}
SECURITY_SENSITIVE_EFFECT_KINDS = {
    "filesystem_read",
    "filesystem_write",
    "network_read",
    "network_write",
    "database_read",
    "database_write",
    "process_spawn",
    "environment_read",
    "environment_write",
    "message_publish",
    "state_mutation",
}
SECURITY_SENSITIVE_CAPABILITY_TOKENS = {
    "credential",
    "credentials",
    "database",
    "db",
    "environment",
    "filesystem",
    "network",
    "process",
    "secret",
    "secrets",
    "shell",
    "storage",
}
MANIFEST_TOP_LEVEL_FIELDS = {
    "apiVersion",
    "kind",
    "metadata",
    "specs",
    "index",
    "compatibility",
    "foreignArtifacts",
    "keywords",
    "preview_only",
}
BOUNDARY_SPEC_TOP_LEVEL_FIELDS = {
    "apiVersion",
    "kind",
    "metadata",
    "intent",
    "scope",
    "provides",
    "requires",
    "interfaces",
    "effects",
    "constraints",
    "evidence",
    "provenance",
    "implementationBindings",
    "foreignArtifacts",
    "keywords",
    "compatibility",
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

    if not root.exists():
        errors.append(
            Issue(
                "error",
                "package_dir_missing",
                f"Package directory does not exist: {package_dir}",
            )
        )
        return validation_report(errors, warnings, None, [], checked_files)

    if not root.is_dir():
        errors.append(
            Issue(
                "error",
                "package_path_not_directory",
                f"Package path is not a directory: {package_dir}",
            )
        )
        return validation_report(errors, warnings, None, [], checked_files)

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
        validate_manifest(manifest, root, errors, warnings)
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

    return validation_report(
        errors,
        warnings,
        manifest,
        sorted(set(manifest_capabilities or provided_by_specs)),
        checked_files,
    )


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
        "contract_warnings": inspect_contract_warnings(boundary_specs),
        "validation": validation,
    }


def diff_packages(old_package_dir: Path, new_package_dir: Path) -> dict[str, Any]:
    old_model = package_diff_model(old_package_dir)
    new_model = package_diff_model(new_package_dir)
    validation_errors = diff_validation_errors(old_model, new_model)
    if validation_errors:
        return {
            "status": "invalid",
            "classification": "invalid",
            "old_package": old_model["path"],
            "new_package": new_model["path"],
            "old_identity": old_model["package"].get("identity"),
            "new_identity": new_model["package"].get("identity"),
            "old_validation": old_model["validation"],
            "new_validation": new_model["validation"],
            "changes": empty_diff_changes(),
            "impact": empty_diff_impact(),
            "errors": [issue.to_dict() for issue in validation_errors],
        }

    changes = structural_diff_changes(old_model, new_model)
    impact = classify_structural_changes(changes)
    return {
        "status": "ok",
        "classification": diff_classification(impact),
        "has_changes": has_structural_changes(changes),
        "old_package": old_model["path"],
        "new_package": new_model["path"],
        "old_identity": old_model["package"].get("identity"),
        "new_identity": new_model["package"].get("identity"),
        "changes": changes,
        "impact": impact,
        "errors": [],
    }


def pack_package(package_dir: Path, output_path: Path | None = None) -> dict[str, Any]:
    root = package_dir.resolve()
    validation = validate_package(root)
    if validation["status"] == "invalid":
        return {
            "status": "invalid",
            "archive": str(output_path) if output_path is not None else None,
            "digest": None,
            "format": "specpm-tar-gzip-v0",
            "included_files": [],
            "validation": validation,
            "errors": [
                {
                    "severity": "error",
                    "code": "validation_failed",
                    "message": "Package validation failed; archive was not created.",
                }
            ],
        }

    manifest = try_load_mapping(root / "specpm.yaml", root)
    if manifest is None:
        return {
            "status": "invalid",
            "archive": str(output_path) if output_path is not None else None,
            "digest": None,
            "format": "specpm-tar-gzip-v0",
            "included_files": [],
            "validation": validation,
            "errors": [
                {
                    "severity": "error",
                    "code": "manifest_unavailable",
                    "message": "Package manifest could not be loaded for packing.",
                }
            ],
        }

    collect_errors: list[Issue] = []
    files = collect_package_files(root, manifest, collect_errors)
    if collect_errors:
        return {
            "status": "invalid",
            "archive": str(output_path) if output_path is not None else None,
            "digest": None,
            "format": "specpm-tar-gzip-v0",
            "included_files": sorted(files),
            "validation": validation,
            "errors": [issue.to_dict() for issue in collect_errors],
        }

    identity = package_identity(manifest) or {}
    archive_path = output_path or Path(
        f"{identity.get('package_id', root.name)}-{identity.get('version', '0.0.0')}.specpm.tgz"
    )
    archive_path = archive_path.resolve()
    overlap = package_file_overlap(root, files, archive_path)
    if overlap is not None:
        return {
            "status": "invalid",
            "archive": str(archive_path),
            "digest": None,
            "format": "specpm-tar-gzip-v0",
            "included_files": sorted(files),
            "validation": validation,
            "errors": [
                Issue(
                    "error",
                    "pack_output_overlaps_source",
                    f"Pack output path overlaps package source file: {overlap}",
                    "pack",
                    "output",
                ).to_dict()
            ],
        }
    try:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        write_deterministic_tar_gz(root, files, archive_path)
        digest = sha256_file(archive_path)
        archive_size = archive_path.stat().st_size
    except (OSError, tarfile.TarError, zlib.error) as exc:
        delete_partial_archive(archive_path)
        return {
            "status": "invalid",
            "archive": str(archive_path),
            "digest": None,
            "format": "specpm-tar-gzip-v0",
            "included_files": sorted(files),
            "validation": validation,
            "errors": [
                Issue(
                    "error",
                    "pack_write_failed",
                    f"Package archive could not be written: {exc}",
                    "pack",
                    "output",
                ).to_dict()
            ],
        }
    return {
        "status": "packed",
        "archive": str(archive_path),
        "digest": {
            "algorithm": "sha256",
            "value": digest,
        },
        "format": "specpm-tar-gzip-v0",
        "included_files": sorted(files),
        "archive_size": archive_size,
        "validation": validation,
        "errors": [],
    }


def index_package(package_ref: Path, index_path: Path) -> dict[str, Any]:
    if package_ref.is_dir():
        return index_directory_package(package_ref.resolve(), index_path, source_kind="directory")
    if package_ref.is_file():
        return index_archive_package(package_ref.resolve(), index_path)
    return {
        "status": "invalid",
        "index": str(index_path),
        "entry": None,
        "errors": [
            Issue(
                "error",
                "package_ref_missing",
                f"Package reference does not exist: {package_ref}",
            ).to_dict()
        ],
    }


def search_index(capability_id: str, index_path: Path) -> dict[str, Any]:
    errors: list[Issue] = []
    validate_id(capability_id, "capability_id_invalid", errors, "search")
    if errors:
        return {
            "status": "invalid",
            "index": str(index_path),
            "query": {"capability_id": capability_id},
            "result_count": 0,
            "results": [],
            "errors": [issue.to_dict() for issue in errors],
        }

    resolved_index = index_path.resolve()
    index_data, load_errors = load_index(resolved_index)
    if load_errors:
        return {
            "status": "invalid",
            "index": str(resolved_index),
            "query": {"capability_id": capability_id},
            "result_count": 0,
            "results": [],
            "errors": [issue.to_dict() for issue in load_errors],
        }

    results = [
        search_result_from_package(package, capability_id)
        for package in packages_for_capability(index_data, capability_id)
    ]

    results.sort(key=lambda item: (item["package_id"], item["version"]))
    return {
        "status": "ok",
        "index": str(resolved_index),
        "query": {"capability_id": capability_id},
        "result_count": len(results),
        "results": results,
        "errors": [],
    }


def search_result_from_package(package: dict[str, Any], capability_id: str) -> dict[str, Any]:
    return {
        "package_id": package.get("package_id"),
        "version": package.get("version"),
        "name": package.get("name"),
        "summary": package.get("summary"),
        "license": package.get("license"),
        "matched_capability": capability_id,
        "provided_capabilities": package.get("provided_capabilities", []),
        "required_capabilities": package.get("required_capabilities", []),
        "compatibility": package.get("compatibility", {}),
        "confidence_summary": {
            "validation_status": package.get("validation_status"),
            "evidence": package.get("evidence_summary", {}),
        },
        "source": package.get("source", {}),
        "yanked": package.get("yanked", False),
    }


def packages_for_capability(index_data: dict[str, Any], capability_id: str) -> list[dict[str, Any]]:
    capability_index = index_data.get("capabilities")
    if not isinstance(capability_index, dict):
        capability_index = build_capability_index(index_data["packages"])
    matches = capability_index.get(capability_id, [])
    if not isinstance(matches, list):
        matches = []
    packages_by_identity = {
        (package.get("package_id"), package.get("version")): package
        for package in index_data["packages"]
        if isinstance(package, dict)
    }
    packages = []
    for match in matches:
        if not isinstance(match, dict):
            continue
        package = packages_by_identity.get((match.get("package_id"), match.get("version")))
        if package is None:
            continue
        packages.append(package)
    return packages


def add_package(target: str, index_path: Path, project_dir: Path) -> dict[str, Any]:
    project_root = project_dir.resolve()
    target_path = Path(target)
    if target_path.exists():
        return add_package_path(target_path.resolve(), project_root, target)

    if "@" in target:
        package_id, version = target.rsplit("@", 1)
        errors: list[Issue] = []
        validate_id(package_id, "package_id_invalid", errors, "add")
        validate_semver(version, "package_version_invalid", errors, "add")
        if errors:
            return add_invalid_report(target, index_path, project_root, errors)
        return add_exact_index_package(package_id, version, index_path, project_root, target)

    errors = []
    validate_id(target, "capability_id_invalid", errors, "add")
    if errors:
        return add_invalid_report(target, index_path, project_root, errors)
    return add_capability_from_index(target, index_path, project_root)


def add_package_path(package_ref: Path, project_root: Path, target: str) -> dict[str, Any]:
    local_index = project_index_path(project_root)
    lock_errors = validate_lock_before_project_mutation(project_root)
    if lock_errors:
        return add_invalid_report(
            target,
            None,
            project_root,
            lock_errors,
            resolved_by="path",
        )

    with tempfile.TemporaryDirectory(prefix="specpm-add-") as temp_dir:
        index_report = index_package(package_ref, Path(temp_dir) / "index.json")
    if index_report["status"] not in {"indexed", "unchanged"}:
        return {
            "status": "invalid",
            "target": target,
            "resolved_by": "path",
            "project": str(project_root),
            "index": None,
            "local_index": str(local_index),
            "lockfile": str(project_root / "specpm.lock"),
            "package": None,
            "candidates": [],
            "index_report": index_report,
            "errors": index_report.get("errors", []),
        }
    return add_selected_package(
        target,
        index_report["entry"],
        project_root,
        resolved_by="path",
        matched_capability=None,
        source_index=None,
    )


def add_exact_index_package(
    package_id: str,
    version: str,
    index_path: Path,
    project_root: Path,
    target: str,
) -> dict[str, Any]:
    resolved_index = index_path.resolve()
    index_data, load_errors = load_index(resolved_index)
    if load_errors:
        return add_invalid_report(target, resolved_index, project_root, load_errors)

    for package in index_data["packages"]:
        if package.get("package_id") == package_id and package.get("version") == version:
            return add_selected_package(
                target,
                package,
                project_root,
                resolved_by="package_ref",
                matched_capability=None,
                source_index=resolved_index,
            )
    return add_invalid_report(
        target,
        resolved_index,
        project_root,
        [
            Issue(
                "error",
                "package_ref_not_found",
                f"Package reference not found in index: {package_id}@{version}",
                str(resolved_index),
            )
        ],
    )


def add_capability_from_index(
    capability_id: str, index_path: Path, project_root: Path
) -> dict[str, Any]:
    resolved_index = index_path.resolve()
    index_data, load_errors = load_index(resolved_index)
    if load_errors:
        return add_invalid_report(capability_id, resolved_index, project_root, load_errors)

    candidates = packages_for_capability(index_data, capability_id)
    if not candidates:
        return add_invalid_report(
            capability_id,
            resolved_index,
            project_root,
            [
                Issue(
                    "error",
                    "capability_not_found",
                    f"No packages provide capability: {capability_id}",
                    str(resolved_index),
                )
            ],
        )

    addable = [package for package in candidates if package.get("yanked") is not True]
    stable = [package for package in addable if is_stable_semver(package.get("version"))]
    if not stable:
        return add_invalid_report(
            capability_id,
            resolved_index,
            project_root,
            [
                Issue(
                    "error",
                    "no_stable_candidate",
                    f"No stable non-yanked package provides capability: {capability_id}",
                    str(resolved_index),
                )
            ],
            candidates=[
                search_result_from_package(package, capability_id) for package in candidates
            ],
        )

    selected_by_package = select_highest_stable_by_package(stable)
    selected = sorted(selected_by_package.values(), key=lambda item: item.get("package_id") or "")
    if not selected:
        return add_invalid_report(
            capability_id,
            resolved_index,
            project_root,
            [
                Issue(
                    "error",
                    "no_addable_candidates",
                    f"No addable package provides capability: {capability_id}",
                    str(resolved_index),
                )
            ],
            candidates=[
                search_result_from_package(package, capability_id) for package in candidates
            ],
        )
    if len(selected) > 1:
        return {
            "status": "ambiguous",
            "target": capability_id,
            "resolved_by": "capability",
            "project": str(project_root),
            "index": str(resolved_index),
            "local_index": str(project_index_path(project_root)),
            "lockfile": str(project_root / "specpm.lock"),
            "package": None,
            "candidate_count": len(selected),
            "candidates": [
                search_result_from_package(package, capability_id) for package in selected
            ],
            "errors": [],
        }

    return add_selected_package(
        capability_id,
        selected[0],
        project_root,
        resolved_by="capability",
        matched_capability=capability_id,
        source_index=resolved_index,
    )


def add_selected_package(
    target: str,
    package: dict[str, Any],
    project_root: Path,
    *,
    resolved_by: str,
    matched_capability: str | None,
    source_index: Path | None,
) -> dict[str, Any]:
    validation_errors = validate_add_package_entry(package)
    if validation_errors:
        return add_invalid_report(
            target,
            source_index,
            project_root,
            validation_errors,
            resolved_by=resolved_by,
        )
    if package.get("yanked") is True:
        return add_invalid_report(
            target,
            source_index,
            project_root,
            [
                Issue(
                    "error",
                    "package_yanked",
                    f"Package is yanked: {package['package_id']}@{package['version']}",
                )
            ],
            resolved_by=resolved_by,
        )

    cache_entry = package_cache_entry(package)
    lock_errors = validate_lock_before_project_mutation(project_root, package, cache_entry)
    if lock_errors:
        return add_invalid_report(
            target,
            source_index,
            project_root,
            lock_errors,
            resolved_by=resolved_by,
        )

    local_index = project_index_path(project_root)
    index_report = write_index_entry(
        local_index,
        dict(package),
        {"status": package.get("validation_status", "unknown")},
    )
    if index_report["status"] not in {"indexed", "unchanged"}:
        return {
            "status": "invalid",
            "target": target,
            "resolved_by": resolved_by,
            "project": str(project_root),
            "index": str(source_index) if source_index is not None else None,
            "local_index": str(local_index),
            "lockfile": str(project_root / "specpm.lock"),
            "package": None,
            "candidates": [],
            "index_report": index_report,
            "errors": index_report.get("errors", []),
        }

    try:
        write_package_cache_entry(project_root, package, cache_entry)
        lock_report = write_lock_entry(project_root, package, cache_entry)
    except OSError as exc:
        return add_invalid_report(
            target,
            source_index,
            project_root,
            [
                Issue(
                    "error",
                    "project_state_write_failed",
                    f"Project state could not be written: {exc}",
                    str(project_root),
                )
            ],
        )

    if lock_report["status"] == "invalid":
        return {
            "status": "invalid",
            "target": target,
            "resolved_by": resolved_by,
            "project": str(project_root),
            "index": str(source_index) if source_index is not None else None,
            "local_index": str(local_index),
            "lockfile": str(project_root / "specpm.lock"),
            "package": None,
            "candidates": [],
            "lock_report": lock_report,
            "errors": lock_report.get("errors", []),
        }

    return {
        "status": lock_report["status"],
        "target": target,
        "resolved_by": resolved_by,
        "matched_capability": matched_capability,
        "project": str(project_root),
        "index": str(source_index) if source_index is not None else None,
        "local_index": str(local_index),
        "lockfile": str(project_root / "specpm.lock"),
        "package": lock_report["entry"],
        "candidates": [],
        "index_report": index_report,
        "errors": [],
    }


def add_invalid_report(
    target: str,
    index_path: Path | None,
    project_root: Path,
    errors: list[Issue],
    *,
    candidates: list[dict[str, Any]] | None = None,
    resolved_by: str | None = None,
) -> dict[str, Any]:
    report = {
        "status": "invalid",
        "target": target,
        "project": str(project_root),
        "index": str(index_path.resolve()) if isinstance(index_path, Path) else None,
        "local_index": str(project_index_path(project_root)),
        "lockfile": str(project_root / "specpm.lock"),
        "package": None,
        "candidates": candidates or [],
        "errors": [issue.to_dict() for issue in errors],
    }
    if resolved_by is not None:
        report["resolved_by"] = resolved_by
    return report


def index_directory_package(root: Path, index_path: Path, *, source_kind: str) -> dict[str, Any]:
    validation = validate_package(root)
    if validation["status"] == "invalid":
        return {
            "status": "invalid",
            "index": str(index_path),
            "entry": None,
            "validation": validation,
            "errors": [
                {
                    "severity": "error",
                    "code": "validation_failed",
                    "message": "Package validation failed; index was not updated.",
                }
            ],
        }

    manifest = try_load_mapping(root / "specpm.yaml", root)
    if manifest is None:
        return {
            "status": "invalid",
            "index": str(index_path),
            "entry": None,
            "validation": validation,
            "errors": [
                {
                    "severity": "error",
                    "code": "manifest_unavailable",
                    "message": "Package manifest could not be loaded for indexing.",
                }
            ],
        }

    collect_errors: list[Issue] = []
    files = collect_package_files(root, manifest, collect_errors)
    if collect_errors:
        return {
            "status": "invalid",
            "index": str(index_path),
            "entry": None,
            "validation": validation,
            "errors": [issue.to_dict() for issue in collect_errors],
        }

    source_digest = digest_package_files(root, files)
    entry = build_index_entry(root, manifest, validation, files, source_digest, source_kind)
    return write_index_entry(index_path, entry, validation)


def index_archive_package(archive_path: Path, index_path: Path) -> dict[str, Any]:
    archive_digest = sha256_file(archive_path)
    with tempfile.TemporaryDirectory(prefix="specpm-index-") as temp_dir:
        temp_root = Path(temp_dir)
        try:
            extract_archive_safely(archive_path, temp_root)
        except (OSError, tarfile.TarError) as exc:
            return {
                "status": "invalid",
                "index": str(index_path),
                "entry": None,
                "errors": [
                    Issue(
                        "error",
                        "archive_extract_failed",
                        f"Archive could not be inspected safely: {exc}",
                    ).to_dict()
                ],
            }

        validation = validate_package(temp_root)
        if validation["status"] == "invalid":
            return {
                "status": "invalid",
                "index": str(index_path),
                "entry": None,
                "validation": validation,
                "errors": [
                    {
                        "severity": "error",
                        "code": "validation_failed",
                        "message": "Archive package validation failed; index was not updated.",
                    }
                ],
            }
        manifest = try_load_mapping(temp_root / "specpm.yaml", temp_root)
        if manifest is None:
            return {
                "status": "invalid",
                "index": str(index_path),
                "entry": None,
                "validation": validation,
                "errors": [
                    {
                        "severity": "error",
                        "code": "manifest_unavailable",
                        "message": "Archive manifest could not be loaded for indexing.",
                    }
                ],
            }
        collect_errors: list[Issue] = []
        files = collect_package_files(temp_root, manifest, collect_errors)
        if collect_errors:
            return {
                "status": "invalid",
                "index": str(index_path),
                "entry": None,
                "validation": validation,
                "errors": [issue.to_dict() for issue in collect_errors],
            }
        entry = build_index_entry(
            temp_root,
            manifest,
            validation,
            files,
            archive_digest,
            "archive",
            source_path=archive_path,
        )
        return write_index_entry(index_path, entry, validation)


def list_inbox(root: Path) -> dict[str, Any]:
    inbox_root = root.resolve()
    bundles = []
    if inbox_root.is_dir():
        for child in sorted(inbox_root.iterdir(), key=lambda item: item.name):
            if child.is_dir() and is_inbox_bundle_candidate(child):
                bundles.append(inbox_bundle_report(child, include_inspection=False))
    return {"root": str(inbox_root), "bundles": bundles}


def inspect_inbox_bundle(root: Path, package_id: str) -> dict[str, Any]:
    bundle_path = root.resolve() / package_id
    if not bundle_path.is_dir():
        return {
            "found": False,
            "package_id": package_id,
            "path": str(bundle_path),
            "inbox_status": "missing",
            "layout": None,
            "handoff": None,
            "handoff_summary": None,
            "gaps": [
                Issue(
                    "error",
                    "inbox_bundle_missing",
                    f"SpecGraph inbox bundle does not exist: {package_id}",
                    str(bundle_path),
                ).to_dict()
            ],
        }

    return inbox_bundle_report(bundle_path, include_inspection=True)


def is_inbox_bundle_candidate(bundle_path: Path) -> bool:
    return any(
        [
            (bundle_path / "specpm.yaml").exists(),
            (bundle_path / "specs/main.spec.yaml").exists(),
            (bundle_path / "handoff.json").exists(),
        ]
    )


def inbox_bundle_report(bundle_path: Path, *, include_inspection: bool) -> dict[str, Any]:
    layout = inspect_inbox_layout(bundle_path)
    validation = validate_package(bundle_path)
    manifest = try_load_mapping(bundle_path / "specpm.yaml", bundle_path)
    handoff_report = load_handoff_report(bundle_path)
    gaps = layout["gaps"] + handoff_report["errors"]
    report = {
        "found": True,
        "package_id": bundle_path.name,
        "path": str(bundle_path),
        "package_identity": validation.get("package_identity"),
        "validation_status": validation["status"],
        "inbox_status": classify_inbox_status(
            manifest,
            handoff_report,
            validation["status"],
            layout["gaps"],
        ),
        "layout": layout,
        "handoff": handoff_report["payload"],
        "handoff_summary": handoff_report["summary"],
        "gaps": gaps,
    }
    if include_inspection:
        report["inspection"] = inspect_package(bundle_path)
    return report


def inspect_inbox_layout(bundle_path: Path) -> dict[str, Any]:
    required_files = [
        inbox_layout_file(bundle_path, "specpm.yaml", "inbox_manifest_missing"),
        inbox_layout_file(bundle_path, "specs/main.spec.yaml", "inbox_main_spec_missing"),
    ]
    optional_files = [
        {
            "path": "handoff.json",
            "present": (bundle_path / "handoff.json").is_file(),
        }
    ]
    gaps = [
        Issue(
            "error",
            item["missing_code"],
            f"SpecGraph inbox bundle is missing required file: {item['path']}",
            str(bundle_path / item["path"]),
        ).to_dict()
        for item in required_files
        if not item["present"]
    ]
    return {
        "required_files": [
            {"path": item["path"], "present": item["present"]} for item in required_files
        ],
        "optional_files": optional_files,
        "has_manifest": required_files[0]["present"],
        "has_main_spec": required_files[1]["present"],
        "has_handoff": optional_files[0]["present"],
        "gaps": gaps,
    }


def inbox_layout_file(bundle_path: Path, rel_path: str, missing_code: str) -> dict[str, Any]:
    return {
        "path": rel_path,
        "present": (bundle_path / rel_path).is_file(),
        "missing_code": missing_code,
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


def validate_manifest(
    manifest: dict[str, Any], root: Path, errors: list[Issue], warnings: list[Issue]
) -> None:
    reject_unknown_top_level_fields(
        manifest, MANIFEST_TOP_LEVEL_FIELDS, errors, "specpm.yaml", "manifest"
    )

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

    require_mapping_field(manifest, "metadata", errors, "specpm.yaml")
    require_mapping_field(manifest, "index", errors, "specpm.yaml")
    require_mapping_field(manifest, "index.provides", errors, "specpm.yaml")
    require_string_field(manifest, "apiVersion", errors, "specpm.yaml")
    require_string_field(manifest, "kind", errors, "specpm.yaml")
    require_string_field(manifest, "metadata.id", errors, "specpm.yaml")
    require_string_field(manifest, "metadata.name", errors, "specpm.yaml")
    require_string_field(manifest, "metadata.version", errors, "specpm.yaml")
    require_string_field(manifest, "metadata.summary", errors, "specpm.yaml")
    require_string_field(manifest, "metadata.license", errors, "specpm.yaml")

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
    elif "preview_only" in manifest and not isinstance(manifest.get("preview_only"), bool):
        errors.append(
            Issue(
                "error",
                "preview_only_invalid",
                "Manifest preview_only must be a boolean when present.",
                "specpm.yaml",
                "preview_only",
            )
        )

    capabilities = get_field(manifest, "index.provides.capabilities")
    manifest_capability_ids = validate_capability_entries(
        capabilities,
        errors,
        "specpm.yaml",
        "index.provides.capabilities",
        required_non_empty=True,
        invalid_list_code="manifest_capabilities_invalid",
        invalid_entry_code="manifest_capability_entry_invalid",
    )
    for capability_id in manifest_capability_ids:
        validate_id(capability_id, "capability_id_invalid", errors, "specpm.yaml")
    warn_duplicates(
        manifest_capability_ids,
        "duplicate_manifest_capability",
        "Duplicate manifest capability",
        warnings,
    )

    validate_capability_entries(
        get_field(manifest, "index.requires.capabilities"),
        errors,
        "specpm.yaml",
        "index.requires.capabilities",
        required_non_empty=False,
        invalid_list_code="manifest_required_capabilities_invalid",
        invalid_entry_code="manifest_required_capability_entry_invalid",
        allow_missing=True,
    )
    validate_foreign_artifacts(
        "specpm.yaml", manifest.get("foreignArtifacts"), root, warnings, errors
    )
    validate_string_list(
        manifest.get("keywords"), "keywords", errors, "specpm.yaml", allow_missing=True
    )


def validate_boundary_spec(
    rel: str,
    spec: dict[str, Any],
    root: Path,
    errors: list[Issue],
    warnings: list[Issue],
) -> set[str]:
    reject_unknown_top_level_fields(
        spec, BOUNDARY_SPEC_TOP_LEVEL_FIELDS, errors, rel, "BoundarySpec"
    )

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

    require_mapping_field(spec, "metadata", errors, rel)
    require_mapping_field(spec, "intent", errors, rel)
    require_mapping_field(spec, "scope", errors, rel)
    require_mapping_field(spec, "provides", errors, rel)
    require_mapping_field(spec, "interfaces", errors, rel)
    require_string_field(spec, "apiVersion", errors, rel)
    require_string_field(spec, "kind", errors, rel)
    require_string_field(spec, "metadata.id", errors, rel)
    require_string_field(spec, "metadata.title", errors, rel)
    require_string_field(spec, "metadata.version", errors, rel)
    require_string_field(spec, "intent.summary", errors, rel)
    require_string_field(spec, "scope.boundedContext", errors, rel)

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

    provided_capability_entries = get_field(spec, "provides.capabilities")
    provided = validate_capability_entries(
        provided_capability_entries,
        errors,
        rel,
        "provides.capabilities",
        required_non_empty=True,
        invalid_list_code="spec_capabilities_invalid",
        invalid_entry_code="spec_capability_entry_invalid",
    )
    for capability_id in provided:
        validate_id(capability_id, "capability_id_invalid", errors, rel)
    warn_duplicates(provided, "duplicate_spec_capability", "Duplicate spec capability", warnings)
    if provided and not has_primary_capability(provided_capability_entries):
        warnings.append(
            Issue(
                "warning",
                "primary_capability_missing",
                "BoundarySpec should declare at least one primary capability.",
                rel,
                "provides.capabilities",
            )
        )

    required = validate_capability_entries(
        get_field(spec, "requires.capabilities"),
        errors,
        rel,
        "requires.capabilities",
        required_non_empty=False,
        invalid_list_code="required_capabilities_invalid",
        invalid_entry_code="required_capability_entry_invalid",
        allow_missing=True,
    )
    for capability_id in required:
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

    validate_interfaces(rel, spec, warnings, errors)
    validate_effects(rel, spec, warnings, errors)
    validate_constraints(rel, spec, errors)
    validate_evidence_paths(rel, spec, root, warnings, errors)
    validate_foreign_artifacts(rel, spec.get("foreignArtifacts"), root, warnings, errors)
    validate_implementation_bindings(
        rel, spec.get("implementationBindings"), root, warnings, errors
    )
    validate_provenance(rel, spec, warnings, errors)
    validate_string_list(spec.get("keywords"), "keywords", errors, rel, allow_missing=True)
    return set(provided)


def validate_interfaces(
    rel: str, spec: dict[str, Any], warnings: list[Issue], errors: list[Issue]
) -> None:
    interfaces = get_field(spec, "interfaces")
    if not isinstance(interfaces, dict):
        errors.append(
            Issue(
                "error",
                "interfaces_invalid",
                "BoundarySpec interfaces must be a mapping.",
                rel,
                "interfaces",
            )
        )
        return
    for direction in ("inbound", "outbound"):
        items = interfaces.get(direction, [])
        if not isinstance(items, list):
            errors.append(
                Issue(
                    "error",
                    "interfaces_direction_invalid",
                    f"BoundarySpec interfaces.{direction} must be a list when present.",
                    rel,
                    f"interfaces.{direction}",
                )
            )
            continue
        ids: list[str] = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(
                    Issue(
                        "error",
                        "interface_entry_invalid",
                        "Interface entries must be mappings.",
                        rel,
                        f"interfaces.{direction}.{index}",
                    )
                )
                continue
            interface_id = item.get("id")
            if isinstance(interface_id, str):
                ids.append(interface_id)
                validate_id(interface_id, "interface_id_invalid", errors, rel)
            else:
                errors.append(
                    Issue(
                        "error",
                        "interface_id_missing",
                        "Interface entries must include a string id.",
                        rel,
                        f"interfaces.{direction}.{index}.id",
                    )
                )
            kind = item.get("kind")
            if not isinstance(kind, str):
                errors.append(
                    Issue(
                        "error",
                        "interface_kind_missing",
                        "Interface entries must include a string kind.",
                        rel,
                        f"interfaces.{direction}.{index}.kind",
                    )
                )
            elif kind not in KNOWN_INTERFACE_KINDS:
                warnings.append(
                    Issue(
                        "warning",
                        "unknown_interface_kind",
                        f"Unknown interface kind: {kind}",
                        rel,
                        f"interfaces.{direction}.{index}.kind",
                    )
                )
        warn_duplicates(
            ids,
            "duplicate_interface_id",
            f"Duplicate {direction} interface id",
            warnings,
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

    evidence_ids: list[str] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(
                Issue(
                    "error",
                    "evidence_entry_invalid",
                    "Evidence entries must be mappings.",
                    rel,
                    f"evidence.{index}",
                )
            )
            continue
        evidence_id = item.get("id")
        if isinstance(evidence_id, str):
            evidence_ids.append(evidence_id)
            validate_id(evidence_id, "evidence_id_invalid", errors, rel)
        kind = item.get("kind")
        if isinstance(kind, str) and kind not in KNOWN_EVIDENCE_KINDS:
            warnings.append(
                Issue(
                    "warning",
                    "unknown_evidence_kind",
                    f"Unknown evidence kind: {kind}",
                    rel,
                    f"evidence.{index}.kind",
                )
            )
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
    warn_duplicates(evidence_ids, "duplicate_evidence_id", "Duplicate evidence id", warnings)


def validate_effects(
    rel: str, spec: dict[str, Any], warnings: list[Issue], errors: list[Issue]
) -> None:
    effects = spec.get("effects")
    if effects is None:
        return
    if not isinstance(effects, dict):
        errors.append(
            Issue(
                "error",
                "effects_invalid",
                "BoundarySpec effects must be a mapping.",
                rel,
                "effects",
            )
        )
        return
    side_effects = effects.get("sideEffects", [])
    if not isinstance(side_effects, list):
        errors.append(
            Issue(
                "error",
                "side_effects_invalid",
                "BoundarySpec effects.sideEffects must be a list when present.",
                rel,
                "effects.sideEffects",
            )
        )
        return
    ids: list[str] = []
    for index, item in enumerate(side_effects):
        if not isinstance(item, dict):
            errors.append(
                Issue(
                    "error",
                    "side_effect_entry_invalid",
                    "Effect entries must be mappings.",
                    rel,
                    f"effects.sideEffects.{index}",
                )
            )
            continue
        effect_id = item.get("id")
        if isinstance(effect_id, str):
            ids.append(effect_id)
            validate_id(effect_id, "effect_id_invalid", errors, rel)
        kind = item.get("kind")
        if isinstance(kind, str) and kind not in KNOWN_EFFECT_KINDS:
            warnings.append(
                Issue(
                    "warning",
                    "unknown_effect_kind",
                    f"Unknown effect kind: {kind}",
                    rel,
                    f"effects.sideEffects.{index}.kind",
                )
            )
    warn_duplicates(ids, "duplicate_effect_id", "Duplicate effect id", warnings)


def validate_constraints(rel: str, spec: dict[str, Any], errors: list[Issue]) -> None:
    constraints = spec.get("constraints", [])
    if constraints is None:
        return
    if not isinstance(constraints, list):
        errors.append(
            Issue(
                "error",
                "constraints_invalid",
                "BoundarySpec constraints must be a list when present.",
                rel,
                "constraints",
            )
        )
        return
    for index, item in enumerate(constraints):
        if not isinstance(item, dict):
            errors.append(
                Issue(
                    "error",
                    "constraint_entry_invalid",
                    "Constraint entries must be mappings.",
                    rel,
                    f"constraints.{index}",
                )
            )
            continue
        constraint_id = item.get("id")
        if isinstance(constraint_id, str):
            validate_id(constraint_id, "constraint_id_invalid", errors, rel)
        level = item.get("level")
        if level not in KNOWN_CONSTRAINT_LEVELS:
            errors.append(
                Issue(
                    "error",
                    "constraint_level_invalid",
                    "Constraint level must be one of MUST, SHOULD, or MAY.",
                    rel,
                    f"constraints.{index}.level",
                )
            )


def validate_foreign_artifacts(
    rel: str,
    artifacts: Any,
    root: Path,
    warnings: list[Issue],
    errors: list[Issue],
) -> None:
    if artifacts is None:
        return
    if not isinstance(artifacts, list):
        errors.append(
            Issue(
                "error",
                "foreign_artifacts_invalid",
                "foreignArtifacts must be a list when present.",
                rel,
                "foreignArtifacts",
            )
        )
        return
    ids: list[str] = []
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            errors.append(
                Issue(
                    "error",
                    "foreign_artifact_entry_invalid",
                    "foreignArtifacts entries must be mappings.",
                    rel,
                    f"foreignArtifacts.{index}",
                )
            )
            continue
        artifact_id = item.get("id")
        if isinstance(artifact_id, str):
            ids.append(artifact_id)
            validate_id(artifact_id, "foreign_artifact_id_invalid", errors, rel)
        role = item.get("role")
        if isinstance(role, str) and role not in KNOWN_FOREIGN_ARTIFACT_ROLES:
            warnings.append(
                Issue(
                    "warning",
                    "unknown_foreign_artifact_role",
                    f"Unknown foreign artifact role: {role}",
                    rel,
                    f"foreignArtifacts.{index}.role",
                )
            )
        path = item.get("path")
        if isinstance(path, str):
            validate_advisory_path(
                root,
                path,
                warnings,
                errors,
                rel,
                f"foreignArtifacts.{index}.path",
                "foreign_artifact_path_missing",
                "Foreign artifact path does not exist",
            )
    warn_duplicates(ids, "duplicate_foreign_artifact_id", "Duplicate foreign artifact id", warnings)


def validate_implementation_bindings(
    rel: str,
    bindings: Any,
    root: Path,
    warnings: list[Issue],
    errors: list[Issue],
) -> None:
    if bindings is None:
        return
    if not isinstance(bindings, list):
        errors.append(
            Issue(
                "error",
                "implementation_bindings_invalid",
                "implementationBindings must be a list when present.",
                rel,
                "implementationBindings",
            )
        )
        return
    ids: list[str] = []
    for index, item in enumerate(bindings):
        if not isinstance(item, dict):
            errors.append(
                Issue(
                    "error",
                    "implementation_binding_entry_invalid",
                    "implementationBindings entries must be mappings.",
                    rel,
                    f"implementationBindings.{index}",
                )
            )
            continue
        binding_id = item.get("id")
        if isinstance(binding_id, str):
            ids.append(binding_id)
            validate_id(binding_id, "implementation_binding_id_invalid", errors, rel)
        direct_path = item.get("path")
        if isinstance(direct_path, str):
            validate_advisory_path(
                root,
                direct_path,
                warnings,
                errors,
                rel,
                f"implementationBindings.{index}.path",
                "implementation_binding_path_missing",
                "Implementation binding path does not exist",
            )
        files = item.get("files")
        if not isinstance(files, dict):
            continue
        for group in ("owned", "border"):
            paths = files.get(group, [])
            if not isinstance(paths, list):
                errors.append(
                    Issue(
                        "error",
                        "implementation_binding_files_invalid",
                        f"implementationBindings files.{group} must be a list when present.",
                        rel,
                        f"implementationBindings.{index}.files.{group}",
                    )
                )
                continue
            for path_index, path in enumerate(paths):
                if not isinstance(path, str):
                    errors.append(
                        Issue(
                            "error",
                            "implementation_binding_path_invalid",
                            "Implementation binding paths must be strings.",
                            rel,
                            f"implementationBindings.{index}.files.{group}.{path_index}",
                        )
                    )
                    continue
                validate_advisory_path(
                    root,
                    path,
                    warnings,
                    errors,
                    rel,
                    f"implementationBindings.{index}.files.{group}.{path_index}",
                    "implementation_binding_path_missing",
                    "Implementation binding path does not exist",
                )
    warn_duplicates(
        ids,
        "duplicate_implementation_binding_id",
        "Duplicate implementation binding id",
        warnings,
    )


def validate_provenance(
    rel: str, spec: dict[str, Any], warnings: list[Issue], errors: list[Issue]
) -> None:
    provenance = spec.get("provenance")
    if provenance is None:
        return
    if not isinstance(provenance, dict):
        errors.append(
            Issue(
                "error",
                "provenance_invalid",
                "BoundarySpec provenance must be a mapping when present.",
                rel,
                "provenance",
            )
        )
        return
    confidence = provenance.get("sourceConfidence")
    if confidence is None:
        return
    if not isinstance(confidence, dict):
        errors.append(
            Issue(
                "error",
                "source_confidence_invalid",
                "provenance.sourceConfidence must be a mapping when present.",
                rel,
                "provenance.sourceConfidence",
            )
        )
        return
    for key, value in confidence.items():
        if value not in KNOWN_CONFIDENCE_VALUES:
            warnings.append(
                Issue(
                    "warning",
                    "unknown_confidence_value",
                    f"Unknown provenance confidence value for {key}: {value}",
                    rel,
                    f"provenance.sourceConfidence.{key}",
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
    provenance = spec.get("provenance", {})
    if not isinstance(provenance, dict):
        provenance = {}
    provenance_confidence = provenance.get("sourceConfidence", {})
    if not isinstance(provenance_confidence, dict):
        provenance_confidence = {}
    return {
        "path": rel,
        "id": get_field(spec, "metadata.id"),
        "title": get_field(spec, "metadata.title"),
        "version": get_field(spec, "metadata.version"),
        "status": get_field(spec, "metadata.status"),
        "intent_summary": get_field(spec, "intent.summary"),
        "scope": spec.get("scope", {}),
        "bounded_context": get_field(spec, "scope.boundedContext"),
        "provides": capability_ids(get_field(spec, "provides.capabilities")),
        "requires": capability_ids(get_field(spec, "requires.capabilities")),
        "interfaces": spec.get("interfaces", {}),
        "effects": spec.get("effects", {}),
        "constraints": spec.get("constraints", []),
        "evidence": spec.get("evidence", []),
        "foreign_artifacts": spec.get("foreignArtifacts", []),
        "implementation_bindings": spec.get("implementationBindings", []),
        "compatibility": spec.get("compatibility", {}),
        "keywords": spec.get("keywords", []),
        "provenance": provenance,
        "provenance_confidence": provenance_confidence,
    }


def inspect_contract_warnings(boundary_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[Issue] = []
    for spec in boundary_specs:
        spec_path = spec.get("path")
        if not isinstance(spec_path, str):
            spec_path = None
        effects = spec.get("effects")
        if isinstance(effects, dict):
            side_effects = effects.get("sideEffects", [])
            if isinstance(side_effects, list):
                for index, item in enumerate(side_effects):
                    if not isinstance(item, dict):
                        continue
                    kind = item.get("kind")
                    if isinstance(kind, str) and kind in SECURITY_SENSITIVE_EFFECT_KINDS:
                        warnings.append(
                            Issue(
                                "warning",
                                "security_sensitive_effect",
                                f"BoundarySpec declares security-sensitive effect kind: {kind}",
                                spec_path,
                                f"effects.sideEffects.{index}.kind",
                            )
                        )
        for section, field in (
            ("provides", "provides.capabilities"),
            ("requires", "requires.capabilities"),
        ):
            capabilities = spec.get(section)
            if not isinstance(capabilities, list):
                continue
            for capability_id in capabilities:
                if not isinstance(capability_id, str):
                    continue
                if capability_has_security_sensitive_token(capability_id):
                    warnings.append(
                        Issue(
                            "warning",
                            "security_sensitive_capability",
                            (
                                "BoundarySpec declares security-sensitive "
                                f"{section} capability: {capability_id}"
                            ),
                            spec_path,
                            field,
                        )
                    )
    return [warning.to_dict() for warning in warnings]


def capability_has_security_sensitive_token(capability_id: str) -> bool:
    tokens = {token for token in re.split(r"[._:-]+", capability_id.lower()) if token}
    return bool(tokens & SECURITY_SENSITIVE_CAPABILITY_TOKENS)


def classify_inbox_status(
    manifest: dict[str, Any] | None,
    handoff_report: dict[str, Any],
    validation_status: str,
    layout_gaps: list[dict[str, Any]],
) -> str:
    if layout_gaps:
        return "invalid"
    if validation_status == "invalid":
        return "invalid"
    handoff_summary = handoff_report.get("summary") or {}
    handoff_status = handoff_summary.get("handoff_status")
    if handoff_report.get("present") and not handoff_report.get("valid"):
        return "blocked"
    if isinstance(handoff_status, str) and "blocked" in handoff_status:
        return "blocked"
    if manifest and manifest.get("preview_only") is True:
        return "draft_visible"
    if handoff_status == "draft_preview_only":
        return "draft_visible"
    return "ready_for_review"


def load_handoff_report(bundle_path: Path) -> dict[str, Any]:
    handoff_path = bundle_path / "handoff.json"
    if not handoff_path.is_file():
        return {
            "present": False,
            "valid": False,
            "payload": None,
            "summary": None,
            "errors": [],
        }
    try:
        loaded = json.loads(handoff_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return invalid_handoff_report(handoff_path, f"handoff.json is invalid JSON: {exc}")
    if not isinstance(loaded, dict):
        return invalid_handoff_report(handoff_path, "handoff.json root must be a JSON object.")
    return {
        "present": True,
        "valid": True,
        "payload": loaded,
        "summary": summarize_handoff(loaded),
        "errors": [],
    }


def invalid_handoff_report(handoff_path: Path, message: str) -> dict[str, Any]:
    return {
        "present": True,
        "valid": False,
        "payload": None,
        "summary": {
            "handoff_status": "invalid",
        },
        "errors": [
            Issue(
                "error",
                "handoff_invalid",
                message,
                str(handoff_path),
            ).to_dict()
        ],
    }


def summarize_handoff(handoff: dict[str, Any]) -> dict[str, Any]:
    summary_fields = [
        "materialized_at",
        "export_id",
        "handoff_id",
        "handoff_status",
        "consumer_id",
        "source_handoff_artifact",
    ]
    summary = {field: handoff.get(field) for field in summary_fields if field in handoff}
    if isinstance(handoff.get("package_identity"), dict):
        summary["package_identity"] = handoff["package_identity"]
    return summary


def package_diff_model(package_dir: Path) -> dict[str, Any]:
    root = package_dir.resolve()
    validation = validate_package(root)
    manifest = try_load_mapping(root / "specpm.yaml", root)
    specs = []
    if manifest is not None:
        for spec_path in iter_manifest_spec_paths(manifest, []):
            resolved = resolve_inside(root, spec_path)
            if resolved is None or not resolved.is_file():
                continue
            spec = try_load_mapping(resolved, root)
            if spec is None:
                continue
            rel = relative_path(root, resolved)
            specs.append(
                {
                    "path": rel,
                    "document": spec,
                    "summary": summarize_boundary_spec(rel, spec),
                }
            )
    package = summarize_manifest(manifest)
    return {
        "path": str(root),
        "validation": validation,
        "manifest": manifest,
        "package": package,
        "specs": specs,
        "provided_capabilities": sorted(set(validation.get("capabilities", []))),
        "required_capabilities": collect_required_capabilities(manifest, specs),
    }


def diff_validation_errors(old_model: dict[str, Any], new_model: dict[str, Any]) -> list[Issue]:
    errors = []
    if old_model["validation"]["status"] == "invalid":
        errors.append(
            Issue(
                "error",
                "old_package_invalid",
                "Old package must validate before structural diff.",
                old_model["path"],
            )
        )
    if new_model["validation"]["status"] == "invalid":
        errors.append(
            Issue(
                "error",
                "new_package_invalid",
                "New package must validate before structural diff.",
                new_model["path"],
            )
        )
    return errors


def empty_diff_changes() -> dict[str, Any]:
    return {
        "capabilities": {"removed": [], "added": []},
        "required_capabilities": {"removed": [], "added": []},
        "interfaces": {"removed": [], "added": [], "changed": []},
        "must_constraints": {"removed": [], "added": [], "changed": []},
        "package_metadata": {"changed": []},
        "compatibility": {"changed": False, "old": {}, "new": {}},
    }


def empty_diff_impact() -> dict[str, list[dict[str, Any]]]:
    return {
        "breaking": [],
        "review_required": [],
        "non_breaking": [],
    }


def structural_diff_changes(old_model: dict[str, Any], new_model: dict[str, Any]) -> dict[str, Any]:
    changes = empty_diff_changes()
    old_capabilities = set(old_model["provided_capabilities"])
    new_capabilities = set(new_model["provided_capabilities"])
    changes["capabilities"] = {
        "removed": sorted(old_capabilities - new_capabilities),
        "added": sorted(new_capabilities - old_capabilities),
    }

    old_required = set(old_model["required_capabilities"])
    new_required = set(new_model["required_capabilities"])
    changes["required_capabilities"] = {
        "removed": sorted(old_required - new_required),
        "added": sorted(new_required - old_required),
    }

    changes["interfaces"] = diff_keyed_items(
        interface_index(old_model["specs"]), interface_index(new_model["specs"])
    )
    changes["must_constraints"] = diff_keyed_items(
        must_constraint_index(old_model["specs"]), must_constraint_index(new_model["specs"])
    )
    changes["package_metadata"] = {
        "changed": diff_package_metadata(old_model["package"], new_model["package"])
    }

    old_compatibility = old_model["package"].get("compatibility", {})
    new_compatibility = new_model["package"].get("compatibility", {})
    changes["compatibility"] = {
        "changed": old_compatibility != new_compatibility,
        "old": old_compatibility,
        "new": new_compatibility,
    }
    return changes


def collect_required_capabilities(
    manifest: dict[str, Any] | None, specs: list[dict[str, Any]]
) -> list[str]:
    required = capability_ids(get_field(manifest, "index.requires.capabilities"))
    for spec in specs:
        required.extend(capability_ids(get_field(spec["document"], "requires.capabilities")))
    return sorted(set(required))


def interface_index(specs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    interfaces: dict[str, dict[str, Any]] = {}
    occurrences: dict[tuple[str, str, str], int] = {}
    for spec in specs:
        spec_id = spec["summary"].get("id") or spec["path"]
        spec_path = spec["path"]
        interface_root = spec["document"].get("interfaces", {})
        if not isinstance(interface_root, dict):
            continue
        for direction in ("inbound", "outbound"):
            items = interface_root.get(direction, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    continue
                identity = (spec_path, direction, item["id"])
                occurrence = occurrences.get(identity, 0)
                occurrences[identity] = occurrence + 1
                key = f"{spec_path}:{direction}:{item['id']}:{occurrence}"
                interfaces[key] = {
                    "spec_id": spec_id,
                    "path": spec_path,
                    "direction": direction,
                    "id": item["id"],
                    "occurrence": occurrence,
                    "kind": item.get("kind"),
                    "summary": item.get("summary"),
                    "definition": item,
                }
    return interfaces


def must_constraint_index(specs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    constraints: dict[str, dict[str, Any]] = {}
    occurrences: dict[tuple[str, str], int] = {}
    for spec in specs:
        spec_id = spec["summary"].get("id") or spec["path"]
        spec_path = spec["path"]
        items = spec["document"].get("constraints", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or item.get("level") != "MUST":
                continue
            if not isinstance(item.get("id"), str):
                continue
            identity = (spec_path, item["id"])
            occurrence = occurrences.get(identity, 0)
            occurrences[identity] = occurrence + 1
            key = f"{spec_path}:{item['id']}:{occurrence}"
            constraints[key] = {
                "spec_id": spec_id,
                "path": spec_path,
                "id": item["id"],
                "occurrence": occurrence,
                "statement": item.get("statement"),
                "definition": item,
            }
    return constraints


def diff_keyed_items(
    old_items: dict[str, dict[str, Any]], new_items: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    removed = [old_items[key] for key in sorted(set(old_items) - set(new_items))]
    added = [new_items[key] for key in sorted(set(new_items) - set(old_items))]
    changed = [
        {
            "key": key,
            "old": old_items[key],
            "new": new_items[key],
        }
        for key in sorted(set(old_items) & set(new_items))
        if old_items[key].get("definition") != new_items[key].get("definition")
    ]
    return {"removed": removed, "added": added, "changed": changed}


def diff_package_metadata(
    old_package: dict[str, Any], new_package: dict[str, Any]
) -> list[dict[str, Any]]:
    fields = {
        "package_id": ("identity", "package_id"),
        "name": ("name",),
        "version": ("identity", "version"),
        "summary": ("summary",),
        "license": ("license",),
    }
    changed = []
    for field, path in fields.items():
        old_value = nested_value(old_package, path)
        new_value = nested_value(new_package, path)
        if old_value != new_value:
            changed.append({"field": field, "old": old_value, "new": new_value})
    return changed


def nested_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for item in path:
        if not isinstance(current, dict):
            return None
        current = current.get(item)
    return current


def classify_structural_changes(changes: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    impact = empty_diff_impact()
    for capability in changes["capabilities"]["removed"]:
        impact["breaking"].append(
            impact_item("capability_removed", "Removed provided capability.", capability)
        )
    for capability in changes["capabilities"]["added"]:
        impact["review_required"].append(
            impact_item("capability_added", "Added provided capability.", capability)
        )
    for capability in changes["required_capabilities"]["added"]:
        impact["breaking"].append(
            impact_item("required_capability_added", "Added required capability.", capability)
        )
    for capability in changes["required_capabilities"]["removed"]:
        impact["non_breaking"].append(
            impact_item(
                "required_capability_removed",
                "Removed required capability.",
                capability,
            )
        )
    for item in changes["interfaces"]["removed"]:
        impact["breaking"].append(impact_item("interface_removed", "Removed interface.", item))
    for item in changes["interfaces"]["added"]:
        impact["review_required"].append(impact_item("interface_added", "Added interface.", item))
    for item in changes["interfaces"]["changed"]:
        impact["breaking"].append(impact_item("interface_changed", "Changed interface.", item))
    must_codes = {
        "removed": "must_constraint_removed",
        "added": "must_constraint_added",
        "changed": "must_constraint_changed",
    }
    for kind in ("removed", "added", "changed"):
        for item in changes["must_constraints"][kind]:
            impact["breaking"].append(
                impact_item(
                    must_codes[kind],
                    f"MUST constraint {kind}.",
                    item,
                )
            )
    for item in changes["package_metadata"]["changed"]:
        target = "breaking" if item["field"] == "package_id" else "review_required"
        impact[target].append(
            impact_item("package_metadata_changed", "Changed package metadata.", item)
        )
    if changes["compatibility"]["changed"]:
        impact["review_required"].append(
            impact_item(
                "compatibility_changed",
                "Changed compatibility metadata.",
                changes["compatibility"],
            )
        )
    return impact


def impact_item(code: str, message: str, value: Any) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "value": value,
    }


def diff_classification(impact: dict[str, list[dict[str, Any]]]) -> str:
    if impact["breaking"]:
        return "breaking"
    if impact["review_required"]:
        return "review_required"
    if impact["non_breaking"]:
        return "non_breaking"
    return "unchanged"


def has_structural_changes(changes: dict[str, Any]) -> bool:
    return any(
        [
            bool(changes["capabilities"]["removed"] or changes["capabilities"]["added"]),
            bool(
                changes["required_capabilities"]["removed"]
                or changes["required_capabilities"]["added"]
            ),
            bool(
                changes["interfaces"]["removed"]
                or changes["interfaces"]["added"]
                or changes["interfaces"]["changed"]
            ),
            bool(
                changes["must_constraints"]["removed"]
                or changes["must_constraints"]["added"]
                or changes["must_constraints"]["changed"]
            ),
            bool(changes["package_metadata"]["changed"]),
            bool(changes["compatibility"]["changed"]),
        ]
    )


def build_index_entry(
    root: Path,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    files: list[str],
    source_digest: str,
    source_kind: str,
    *,
    source_path: Path | None = None,
) -> dict[str, Any]:
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    specs = load_index_specs(root, manifest)
    required_capabilities = sorted(
        set(
            capability_ids(get_field(manifest, "index.requires.capabilities"))
            + [
                capability
                for spec in specs
                for capability in capability_ids(get_field(spec, "requires.capabilities"))
            ]
        )
    )
    evidence_entries = [
        item for spec in specs for item in spec.get("evidence", []) if isinstance(item, dict)
    ]
    return {
        "package_id": metadata.get("id"),
        "name": metadata.get("name"),
        "version": metadata.get("version"),
        "summary": metadata.get("summary"),
        "license": metadata.get("license"),
        "provided_capabilities": sorted(validation.get("capabilities", [])),
        "required_capabilities": required_capabilities,
        "compatibility": manifest.get("compatibility", {}),
        "evidence_summary": summarize_evidence_entries(evidence_entries),
        "source": {
            "kind": source_kind,
            "path": str(source_path or root),
            "digest": {
                "algorithm": "sha256",
                "value": source_digest,
            },
        },
        "validation_status": validation["status"],
        "yanked": False,
        "files": sorted(files),
    }


def load_index_specs(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for spec_path in iter_manifest_spec_paths(manifest, []):
        resolved = resolve_inside(root, spec_path)
        if resolved is None or not resolved.is_file():
            continue
        spec = try_load_mapping(resolved, root)
        if spec is not None:
            specs.append(spec)
    return specs


def summarize_evidence_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    kinds: dict[str, int] = {}
    missing_paths = 0
    for entry in entries:
        kind = entry.get("kind") if isinstance(entry.get("kind"), str) else "unknown"
        kinds[kind] = kinds.get(kind, 0) + 1
        if "path" not in entry:
            missing_paths += 1
    return {
        "total": len(entries),
        "kinds": dict(sorted(kinds.items())),
        "entries_without_paths": missing_paths,
    }


def write_index_entry(
    index_path: Path, entry: dict[str, Any], validation: dict[str, Any]
) -> dict[str, Any]:
    resolved_index = index_path.resolve()
    index_data, load_errors = load_index(resolved_index)
    if load_errors:
        return {
            "status": "invalid",
            "index": str(resolved_index),
            "entry": None,
            "validation": validation,
            "errors": [issue.to_dict() for issue in load_errors],
        }

    packages = index_data["packages"]
    for existing in packages:
        if existing.get("package_id") == entry.get("package_id") and existing.get(
            "version"
        ) == entry.get("version"):
            existing_digest = get_field(existing, "source.digest.value")
            new_digest = get_field(entry, "source.digest.value")
            if existing_digest == new_digest:
                return {
                    "status": "unchanged",
                    "index": str(resolved_index),
                    "entry": existing,
                    "validation": validation,
                    "errors": [],
                }
            return {
                "status": "invalid",
                "index": str(resolved_index),
                "entry": None,
                "validation": validation,
                "errors": [
                    Issue(
                        "error",
                        "duplicate_package_conflict",
                        "Index already contains this package id and version "
                        "with a different digest.",
                        str(resolved_index),
                    ).to_dict()
                ],
            }

    packages.append(entry)
    packages.sort(key=lambda item: (item.get("package_id") or "", item.get("version") or ""))
    index_data["capabilities"] = build_capability_index(packages)
    try:
        write_json_file(resolved_index, index_data)
    except OSError as exc:
        return {
            "status": "invalid",
            "index": str(resolved_index),
            "entry": None,
            "validation": validation,
            "errors": [
                Issue(
                    "error",
                    "index_write_failed",
                    f"Index could not be written: {exc}",
                    str(resolved_index),
                ).to_dict()
            ],
        }
    return {
        "status": "indexed",
        "index": str(resolved_index),
        "entry": entry,
        "validation": validation,
        "errors": [],
    }


def load_index(index_path: Path) -> tuple[dict[str, Any], list[Issue]]:
    if not index_path.exists():
        return empty_index(), []
    try:
        loaded = json.loads(index_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return empty_index(), [
            Issue(
                "error",
                "index_read_failed",
                f"Index could not be read: {exc}",
                str(index_path),
            )
        ]
    except json.JSONDecodeError as exc:
        return empty_index(), [Issue("error", "index_json_invalid", str(exc), str(index_path))]
    if not isinstance(loaded, dict):
        return empty_index(), [
            Issue(
                "error",
                "index_schema_invalid",
                "Index root must be a JSON object.",
                str(index_path),
            )
        ]
    if loaded.get("schemaVersion") != INDEX_SCHEMA_VERSION:
        return empty_index(), [
            Issue(
                "error",
                "index_schema_unsupported",
                f"Index schemaVersion must be {INDEX_SCHEMA_VERSION}.",
                str(index_path),
                "schemaVersion",
            )
        ]
    packages = loaded.get("packages")
    if not isinstance(packages, list):
        return empty_index(), [
            Issue(
                "error", "index_schema_invalid", "Index packages must be a list.", str(index_path)
            )
        ]
    if not isinstance(loaded.get("capabilities"), dict):
        loaded["capabilities"] = build_capability_index(packages)
    return loaded, []


def empty_index() -> dict[str, Any]:
    return {
        "schemaVersion": INDEX_SCHEMA_VERSION,
        "packages": [],
        "capabilities": {},
    }


def build_capability_index(packages: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    capability_index: dict[str, list[dict[str, str]]] = {}
    for package in packages:
        package_id = package.get("package_id")
        version = package.get("version")
        if not isinstance(package_id, str) or not isinstance(version, str):
            continue
        for capability in package.get("provided_capabilities", []):
            if not isinstance(capability, str):
                continue
            capability_index.setdefault(capability, []).append(
                {"package_id": package_id, "version": version}
            )
    return {
        capability: sorted(entries, key=lambda item: (item["package_id"], item["version"]))
        for capability, entries in sorted(capability_index.items())
    }


def project_index_path(project_root: Path) -> Path:
    return project_root / ".specpm/index.json"


def validate_lock_before_project_mutation(
    project_root: Path,
    package: dict[str, Any] | None = None,
    cache_entry: str | None = None,
) -> list[Issue]:
    lock_data, lock_errors = load_lock(project_root / "specpm.lock")
    if lock_errors or package is None or cache_entry is None:
        return lock_errors

    lock_entry = build_lock_entry(package, cache_entry)
    for existing in lock_data["packages"]:
        if (
            existing.get("package_id") == lock_entry["package_id"]
            and existing.get("version") == lock_entry["version"]
        ):
            existing_digest = get_field(existing, "source.digest.value")
            new_digest = get_field(lock_entry, "source.digest.value")
            if existing_digest != new_digest:
                return [
                    Issue(
                        "error",
                        "lock_package_conflict",
                        "Lockfile already contains this package id and version "
                        "with a different digest.",
                        str(project_root / "specpm.lock"),
                    )
                ]
    return []


def load_lock(lock_path: Path) -> tuple[dict[str, Any], list[Issue]]:
    if not lock_path.exists():
        return empty_lock(), []
    try:
        loaded = json.loads(lock_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return empty_lock(), [
            Issue("error", "lock_read_failed", f"Lockfile could not be read: {exc}", str(lock_path))
        ]
    except json.JSONDecodeError as exc:
        return empty_lock(), [Issue("error", "lock_json_invalid", str(exc), str(lock_path))]
    if not isinstance(loaded, dict):
        return empty_lock(), [
            Issue(
                "error",
                "lock_schema_invalid",
                "Lockfile root must be a JSON object.",
                str(lock_path),
            )
        ]
    if loaded.get("schemaVersion") != LOCK_SCHEMA_VERSION:
        return empty_lock(), [
            Issue(
                "error",
                "lock_schema_unsupported",
                f"Lockfile schemaVersion must be {LOCK_SCHEMA_VERSION}.",
                str(lock_path),
                "schemaVersion",
            )
        ]
    packages = loaded.get("packages")
    if not isinstance(packages, list):
        return empty_lock(), [
            Issue(
                "error", "lock_schema_invalid", "Lockfile packages must be a list.", str(lock_path)
            )
        ]
    return loaded, []


def empty_lock() -> dict[str, Any]:
    return {
        "schemaVersion": LOCK_SCHEMA_VERSION,
        "packages": [],
    }


def write_lock_entry(
    project_root: Path, package: dict[str, Any], cache_entry: str
) -> dict[str, Any]:
    lock_path = project_root / "specpm.lock"
    lock_data, load_errors = load_lock(lock_path)
    if load_errors:
        return {
            "status": "invalid",
            "lockfile": str(lock_path),
            "entry": None,
            "errors": [issue.to_dict() for issue in load_errors],
        }

    lock_entry = build_lock_entry(package, cache_entry)
    packages = lock_data["packages"]
    status = "added"
    for index, existing in enumerate(packages):
        if (
            existing.get("package_id") == lock_entry["package_id"]
            and existing.get("version") == lock_entry["version"]
        ):
            existing_digest = get_field(existing, "source.digest.value")
            new_digest = get_field(lock_entry, "source.digest.value")
            if existing_digest != new_digest:
                return {
                    "status": "invalid",
                    "lockfile": str(lock_path),
                    "entry": None,
                    "errors": [
                        Issue(
                            "error",
                            "lock_package_conflict",
                            "Lockfile already contains this package id and version "
                            "with a different digest.",
                            str(lock_path),
                        ).to_dict()
                    ],
                }
            if existing == lock_entry:
                status = "unchanged"
            else:
                packages[index] = lock_entry
            break
    else:
        packages.append(lock_entry)

    packages.sort(key=lambda item: (item.get("package_id") or "", item.get("version") or ""))
    write_json_file(lock_path, lock_data)
    return {
        "status": status,
        "lockfile": str(lock_path),
        "entry": lock_entry,
        "errors": [],
    }


def build_lock_entry(package: dict[str, Any], cache_entry: str) -> dict[str, Any]:
    return {
        "package_id": package.get("package_id"),
        "version": package.get("version"),
        "name": package.get("name"),
        "summary": package.get("summary"),
        "license": package.get("license"),
        "provided_capabilities": package.get("provided_capabilities", []),
        "required_capabilities": package.get("required_capabilities", []),
        "compatibility": package.get("compatibility", {}),
        "source": package.get("source", {}),
        "validation_status": package.get("validation_status"),
        "yanked": package.get("yanked", False),
        "cache_entry": cache_entry,
    }


def package_cache_entry(package: dict[str, Any]) -> str:
    package_id = package["package_id"]
    version = package["version"]
    return f".specpm/packages/{package_id}/{version}/package.json"


def write_package_cache_entry(
    project_root: Path, package: dict[str, Any], cache_entry: str
) -> None:
    cache_rel = cache_entry
    cache_path = project_root / cache_rel
    write_json_file(
        cache_path,
        {
            "schemaVersion": LOCK_SCHEMA_VERSION,
            "package": package,
        },
    )


def validate_add_package_entry(package: dict[str, Any]) -> list[Issue]:
    errors: list[Issue] = []
    validate_id(package.get("package_id"), "package_id_invalid", errors, "index")
    validate_semver(package.get("version"), "package_version_invalid", errors, "index")
    source_digest = get_field(package, "source.digest.value")
    if not isinstance(source_digest, str) or not source_digest:
        errors.append(
            Issue(
                "error",
                "package_digest_missing",
                "Indexed package source digest is required for add.",
                "index",
                "source.digest.value",
            )
        )
    capabilities = package.get("provided_capabilities")
    if not isinstance(capabilities, list):
        errors.append(
            Issue(
                "error",
                "package_capabilities_invalid",
                "Indexed package provided_capabilities must be a list.",
                "index",
                "provided_capabilities",
            )
        )
    return errors


def select_highest_stable_by_package(
    packages: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for package in packages:
        package_id = package.get("package_id")
        version = package.get("version")
        if not isinstance(package_id, str) or semver_key(version) is None:
            continue
        current = selected.get(package_id)
        if current is None or semver_key(version) > semver_key(current.get("version")):
            selected[package_id] = package
    return selected


def is_stable_semver(version: Any) -> bool:
    parsed = semver_key(version)
    if parsed is None:
        return False
    public = str(version).split("+", 1)[0]
    return "-" not in public


def semver_key(version: Any) -> tuple[int, int, int] | None:
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        return None
    public = version.split("+", 1)[0]
    numeric = public.split("-", 1)[0]
    major, minor, patch = numeric.split(".")
    return (int(major), int(minor), int(patch))


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def digest_package_files(root: Path, files: list[str]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(files):
        path = root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def extract_archive_safely(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            validate_archive_member(member)
            if member.isdir():
                continue
            if not member.isfile():
                raise tarfile.TarError(f"Unsupported archive member type: {member.name}")
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise tarfile.TarError(f"Archive member could not be read: {member.name}")
            with source, target.open("wb") as output:
                for chunk in iter(lambda source=source: source.read(1024 * 1024), b""):
                    output.write(chunk)


def validate_archive_member(member: tarfile.TarInfo) -> None:
    name = member.name
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or name.startswith("/"):
        raise tarfile.TarError(f"Unsafe archive member path: {name}")
    if member.issym() or member.islnk():
        raise tarfile.TarError(f"Archive symlinks and hardlinks are unsupported: {name}")


def collect_package_files(root: Path, manifest: dict[str, Any], errors: list[Issue]) -> list[str]:
    files: set[str] = {"specpm.yaml"}

    specs: list[tuple[str, dict[str, Any]]] = []
    for spec_path in iter_manifest_spec_paths(manifest, []):
        add_pack_path(root, spec_path, files, errors, "specpm.yaml", "specs")
        resolved = resolve_inside(root, spec_path)
        if resolved is None or not resolved.is_file():
            continue
        spec = try_load_mapping(resolved, root)
        if spec is not None:
            specs.append((relative_path(root, resolved), spec))

    for rel in optional_top_level_sidecars(root):
        add_pack_path(root, rel, files, errors, rel, rel)

    for artifact_path in manifest_artifact_paths(manifest):
        add_pack_path(
            root,
            artifact_path,
            files,
            errors,
            "specpm.yaml",
            "foreignArtifacts",
            missing_is_error=False,
        )

    for spec_rel, spec in specs:
        for artifact_path in boundary_spec_artifact_paths(spec):
            add_pack_path(
                root,
                artifact_path,
                files,
                errors,
                spec_rel,
                "artifact path",
                missing_is_error=False,
            )

    return sorted(files)


def optional_top_level_sidecars(root: Path) -> list[str]:
    names = {"readme", "readme.md", "readme.markdown", "handoff.json"}
    sidecars: list[str] = []
    for child in root.iterdir() if root.is_dir() else []:
        if child.is_file() and child.name.lower() in names:
            sidecars.append(child.name)
    return sidecars


def manifest_artifact_paths(manifest: dict[str, Any]) -> list[str]:
    return paths_from_foreign_artifacts(manifest.get("foreignArtifacts"))


def boundary_spec_artifact_paths(spec: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    evidence = spec.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                paths.append(item["path"])
    paths.extend(paths_from_foreign_artifacts(spec.get("foreignArtifacts")))
    paths.extend(paths_from_implementation_bindings(spec.get("implementationBindings")))
    return paths


def paths_from_foreign_artifacts(artifacts: Any) -> list[str]:
    if not isinstance(artifacts, list):
        return []
    return [
        item["path"]
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]


def paths_from_implementation_bindings(bindings: Any) -> list[str]:
    paths: list[str] = []
    if not isinstance(bindings, list):
        return paths
    for item in bindings:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("path"), str):
            paths.append(item["path"])
        files = item.get("files")
        if not isinstance(files, dict):
            continue
        for group in ("owned", "border"):
            group_paths = files.get(group, [])
            if isinstance(group_paths, list):
                paths.extend(path for path in group_paths if isinstance(path, str))
    return paths


def add_pack_path(
    root: Path,
    rel_path: str,
    files: set[str],
    errors: list[Issue],
    file: str,
    field: str,
    *,
    missing_is_error: bool = True,
) -> None:
    candidate = root / rel_path
    if candidate.is_symlink():
        errors.append(
            Issue(
                "error",
                "pack_symlink_unsupported",
                f"Pack path is a symlink and will not be archived: {rel_path}",
                file,
                field,
            )
        )
        return
    resolved = resolve_inside(root, rel_path)
    if resolved is None:
        errors.append(
            Issue(
                "error", "path_escape", f"Pack path escapes package root: {rel_path}", file, field
            )
        )
        return
    if not resolved.exists():
        if missing_is_error:
            errors.append(
                Issue(
                    "error",
                    "pack_path_missing",
                    f"Pack path does not exist: {rel_path}",
                    file,
                    field,
                )
            )
        return
    if resolved.is_symlink():
        errors.append(
            Issue(
                "error",
                "pack_symlink_unsupported",
                f"Pack path is a symlink and will not be archived: {rel_path}",
                file,
                field,
            )
        )
        return
    if resolved.is_file():
        files.add(relative_path(root, resolved))
        return
    if resolved.is_dir():
        for child in sorted(resolved.rglob("*")):
            if child.is_symlink():
                errors.append(
                    Issue(
                        "error",
                        "pack_symlink_unsupported",
                        "Pack path contains a symlink and will not be archived: "
                        f"{relative_path(root, child)}",
                        file,
                        field,
                    )
                )
                continue
            if child.is_file():
                files.add(relative_path(root, child))


def write_deterministic_tar_gz(root: Path, files: list[str], archive_path: Path) -> None:
    with archive_path.open("wb") as raw_file:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_file, mtime=0) as gzip_file:
            with tarfile.open(fileobj=gzip_file, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for rel in sorted(files):
                    path = root / rel
                    info = tarfile.TarInfo(rel)
                    info.size = path.stat().st_size
                    info.mtime = 0
                    info.mode = 0o644
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    with path.open("rb") as source:
                        tar.addfile(info, source)


def package_file_overlap(root: Path, files: list[str], archive_path: Path) -> str | None:
    for rel in files:
        if (root / rel).resolve() == archive_path:
            return rel
    return None


def delete_partial_archive(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def try_load_mapping(path: Path, root: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        loaded = load_restricted_yaml(path, root)
    except RestrictedYamlError:
        return None
    return loaded if isinstance(loaded, dict) else None


def validation_report(
    errors: list[Issue],
    warnings: list[Issue],
    manifest: dict[str, Any] | None,
    capabilities: list[str],
    checked_files: list[str],
) -> dict[str, Any]:
    status = "invalid" if errors else "warning_only" if warnings else "valid"
    return {
        "status": status,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": [issue.to_dict() for issue in errors],
        "warnings": [issue.to_dict() for issue in warnings],
        "package_identity": package_identity(manifest),
        "capabilities": sorted(set(capabilities)),
        "checked_files": sorted(checked_files),
    }


def reject_unknown_top_level_fields(
    data: dict[str, Any],
    allowed_fields: set[str],
    errors: list[Issue],
    file: str,
    document_kind: str,
) -> None:
    for field in sorted(data):
        if field in allowed_fields or field.startswith("x-"):
            continue
        errors.append(
            Issue(
                "error",
                "unknown_top_level_field",
                f"Unknown top-level field in {document_kind}: {field}",
                file,
                field,
            )
        )


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


def require_mapping_field(data: dict[str, Any], field: str, errors: list[Issue], file: str) -> None:
    value = get_field(data, field)
    if value is not None and not isinstance(value, dict):
        errors.append(
            Issue(
                "error",
                "field_type_invalid",
                f"Field must be a mapping: {field}",
                file,
                field,
            )
        )


def require_string_field(data: dict[str, Any], field: str, errors: list[Issue], file: str) -> None:
    value = get_field(data, field)
    if value is not None and not isinstance(value, str):
        errors.append(
            Issue(
                "error",
                "field_type_invalid",
                f"Field must be a string: {field}",
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


def validate_string_list(
    value: Any,
    field: str,
    errors: list[Issue],
    file: str,
    *,
    allow_missing: bool = False,
) -> list[str]:
    if value is None and allow_missing:
        return []
    if not isinstance(value, list):
        errors.append(
            Issue(
                "error",
                "field_type_invalid",
                f"Field must be a list of strings: {field}",
                file,
                field,
            )
        )
        return []
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(
                Issue(
                    "error",
                    "field_type_invalid",
                    f"List item must be a string: {field}.{index}",
                    file,
                    f"{field}.{index}",
                )
            )
            continue
        items.append(item)
    return items


def validate_capability_entries(
    value: Any,
    errors: list[Issue],
    file: str,
    field: str,
    *,
    required_non_empty: bool,
    invalid_list_code: str,
    invalid_entry_code: str,
    allow_missing: bool = False,
) -> list[str]:
    if value is None and allow_missing:
        return []
    if not isinstance(value, list) or (required_non_empty and not value):
        errors.append(
            Issue(
                "error",
                invalid_list_code,
                f"{field} must be a {'non-empty ' if required_non_empty else ''}list.",
                file,
                field,
            )
        )
        return []
    ids: list[str] = []
    for index, entry in enumerate(value):
        if isinstance(entry, str):
            ids.append(entry)
            continue
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            ids.append(entry["id"])
            continue
        errors.append(
            Issue(
                "error",
                invalid_entry_code,
                "Capability entries must be strings or mappings with a string id field.",
                file,
                f"{field}.{index}",
            )
        )
    return ids


def has_primary_capability(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if isinstance(item, dict) and item.get("role") == "primary":
            return True
    return any(isinstance(item, str) for item in value)


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


def validate_advisory_path(
    root: Path,
    rel_path: str,
    warnings: list[Issue],
    errors: list[Issue],
    file: str,
    field: str,
    missing_code: str,
    missing_prefix: str,
) -> None:
    resolved = resolve_inside(root, rel_path)
    if resolved is None:
        errors.append(
            Issue(
                "error",
                "path_escape",
                f"Path escapes package root: {rel_path}",
                file,
                field,
            )
        )
        return
    if not resolved.exists():
        warnings.append(
            Issue(
                "warning",
                missing_code,
                f"{missing_prefix}: {rel_path}",
                file,
                field,
            )
        )


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
