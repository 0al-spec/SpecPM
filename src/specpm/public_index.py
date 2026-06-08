from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from specpm import __version__
from specpm.core import (
    REMOTE_REGISTRY_API_VERSION,
    REMOTE_REGISTRY_SCHEMA_VERSION,
    Issue,
    RestrictedYamlError,
    get_field,
    inspect_package,
    load_restricted_yaml,
    pack_package,
    resolve_inside,
    semver_key,
    sha256_file,
    validate_remote_registry_payload,
    write_json_file,
)

PUBLIC_INDEX_REPORT_SCHEMA_VERSION = 1
PUBLIC_INDEX_MANIFEST_FILE_SCHEMA_VERSION = 1
PUBLIC_INDEX_MANIFEST_REPORT_SCHEMA_VERSION = 1
GIT_REVISION_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
GIT_REF_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")
PUBLIC_INDEX_RELATION_TYPES = {"contains"}


def generate_public_index_from_inputs(
    package_dirs: list[Path],
    output_dir: Path,
    registry_url: str,
    *,
    manifest_path: Path | None = None,
    root: Path | None = None,
    build_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_package_dirs = [Path(package_dir) for package_dir in package_dirs]
    if manifest_path is not None:
        with tempfile.TemporaryDirectory(prefix="specpm-public-index-sources-") as source_dir:
            manifest = load_public_index_manifest(
                manifest_path,
                root=root,
                remote_root=Path(source_dir),
            )
            if manifest["status"] != "ok":
                return public_index_report(
                    "invalid",
                    output_dir.resolve(),
                    registry_url,
                    [],
                    manifest["errors"],
                )
            resolved_package_dirs.extend(Path(path) for path in manifest["package_dirs"])
            return generate_public_index(
                resolved_package_dirs,
                output_dir,
                registry_url,
                source_contexts=public_index_source_contexts(manifest["sources"]),
                accepted_relations=manifest["relations"],
                build_metadata=build_metadata,
            )
    return generate_public_index(
        resolved_package_dirs,
        output_dir,
        registry_url,
        build_metadata=build_metadata,
    )


def load_public_index_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
    remote_root: Path | None = None,
) -> dict[str, Any]:
    resolved_root = (root or Path.cwd()).resolve()
    resolved_manifest = manifest_path.resolve()
    errors: list[dict[str, Any]] = []

    if not resolved_manifest.is_file():
        return public_index_manifest_report(
            "invalid",
            resolved_manifest,
            resolved_root,
            [],
            [],
            [],
            [
                public_index_error(
                    "public_index_manifest_missing",
                    "Public index accepted package manifest is missing.",
                    field=str(manifest_path),
                )
            ],
        )

    try:
        loaded = load_restricted_yaml(resolved_manifest, resolved_manifest.parent)
    except RestrictedYamlError as exc:
        return public_index_manifest_report(
            "invalid",
            resolved_manifest,
            resolved_root,
            [],
            [],
            [],
            [issue.to_dict() for issue in exc.issues],
        )

    if not isinstance(loaded, dict):
        errors.append(
            public_index_error(
                "public_index_manifest_invalid",
                "Public index accepted package manifest must be a mapping.",
                field=str(manifest_path),
            )
        )
        return public_index_manifest_report(
            "invalid", resolved_manifest, resolved_root, [], [], [], errors
        )

    unknown_top_level_fields = sorted(set(loaded) - {"schemaVersion", "packages", "relations"})
    if unknown_top_level_fields:
        errors.append(
            public_index_error(
                "public_index_manifest_field_unknown",
                "Public index accepted package manifest contains unknown top-level fields.",
                detail={"fields": unknown_top_level_fields},
            )
        )

    if loaded.get("schemaVersion") != PUBLIC_INDEX_MANIFEST_FILE_SCHEMA_VERSION:
        errors.append(
            public_index_error(
                "public_index_manifest_schema_version_invalid",
                "Public index accepted package manifest schemaVersion must be 1.",
                field="schemaVersion",
            )
        )

    packages = loaded.get("packages")
    if not isinstance(packages, list) or not packages:
        errors.append(
            public_index_error(
                "public_index_manifest_packages_invalid",
                "Public index accepted package manifest must contain a non-empty packages list.",
                field="packages",
            )
        )
        return public_index_manifest_report(
            "invalid", resolved_manifest, resolved_root, [], [], [], errors
        )

    package_dirs: list[Path] = []
    sources: list[dict[str, Any]] = []
    for index, item in enumerate(packages):
        field = f"packages[{index}]"
        if not isinstance(item, dict):
            errors.append(
                public_index_error(
                    "public_index_manifest_package_invalid",
                    "Public index manifest package entries must be mappings.",
                    field=field,
                )
            )
            continue

        is_remote_source = any(key in item for key in {"repository", "ref", "revision"})
        allowed_fields = {"path", "repository", "ref", "revision"} if is_remote_source else {"path"}
        unknown_fields = sorted(set(item) - allowed_fields)
        if unknown_fields:
            errors.append(
                public_index_error(
                    "public_index_manifest_package_field_unknown",
                    "Public index manifest package entry contains unknown fields.",
                    field=field,
                    detail={"fields": unknown_fields},
                )
            )
            continue

        package_path = item.get("path")
        if not isinstance(package_path, str) or not package_path.strip():
            errors.append(
                public_index_error(
                    "public_index_manifest_package_path_invalid",
                    "Public index manifest package path must be a non-empty string.",
                    field=f"{field}.path",
                )
            )
            continue

        if is_remote_source:
            resolved_package = resolve_remote_manifest_package(
                item,
                field,
                package_path,
                remote_root,
                errors,
            )
            if resolved_package is None:
                continue
            package_dirs.append(resolved_package)
            sources.append(
                {
                    "kind": "git",
                    "repository": item["repository"],
                    "ref": item["ref"],
                    "revision": item["revision"].lower(),
                    "path": package_path,
                    "package_dir": str(resolved_package),
                }
            )
            continue

        resolved_package = resolve_inside(resolved_root, package_path)
        if resolved_package is None:
            errors.append(
                public_index_error(
                    "public_index_manifest_package_path_escape",
                    "Public index manifest package path must stay inside the repository root.",
                    field=f"{field}.path",
                )
            )
            continue
        package_dirs.append(resolved_package)
        sources.append(
            {
                "kind": "local",
                "path": package_path,
                "package_dir": str(resolved_package),
            }
        )

    relations = parse_public_index_manifest_relations(loaded.get("relations"), errors)

    status = "invalid" if errors else "ok"
    return public_index_manifest_report(
        status,
        resolved_manifest,
        resolved_root,
        package_dirs if status == "ok" else [],
        sources if status == "ok" else [],
        relations if status == "ok" else [],
        errors,
    )


def parse_public_index_manifest_relations(
    loaded_relations: Any,
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if loaded_relations is None:
        return []
    if not isinstance(loaded_relations, list):
        errors.append(
            public_index_error(
                "public_index_manifest_relations_invalid",
                "Public index accepted relations must be an array.",
                field="relations",
            )
        )
        return []

    relations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(loaded_relations):
        field = f"relations[{index}]"
        if not isinstance(item, dict):
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_invalid",
                    "Public index accepted relation entries must be mappings.",
                    field=field,
                )
            )
            continue

        unknown_fields = sorted(
            set(item) - {"id", "type", "source", "target", "reviewStatus", "evidence"}
        )
        if unknown_fields:
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_field_unknown",
                    "Public index accepted relation entry contains unknown fields.",
                    field=field,
                    detail={"fields": unknown_fields},
                )
            )
            continue

        relation_id = item.get("id")
        relation_type = item.get("type")
        review_status = item.get("reviewStatus")
        source = parse_public_index_relation_endpoint(item.get("source"), f"{field}.source", errors)
        target = parse_public_index_relation_endpoint(item.get("target"), f"{field}.target", errors)
        evidence = parse_public_index_relation_evidence(
            item.get("evidence"),
            f"{field}.evidence",
            errors,
        )

        if not isinstance(relation_id, str) or not relation_id.strip():
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_id_invalid",
                    "Public index accepted relation id must be a non-empty string.",
                    field=f"{field}.id",
                )
            )
        elif relation_id in seen_ids:
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_id_duplicate",
                    "Public index accepted relation id must be unique.",
                    field=f"{field}.id",
                )
            )
        else:
            seen_ids.add(relation_id)

        if relation_type not in PUBLIC_INDEX_RELATION_TYPES:
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_type_invalid",
                    "Public index accepted relation type is not supported.",
                    field=f"{field}.type",
                    detail={"allowed": sorted(PUBLIC_INDEX_RELATION_TYPES)},
                )
            )

        if review_status != "accepted":
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_review_status_invalid",
                    "Public index accepted relation reviewStatus must be accepted.",
                    field=f"{field}.reviewStatus",
                )
            )

        if (
            isinstance(relation_id, str)
            and relation_id.strip()
            and relation_type in PUBLIC_INDEX_RELATION_TYPES
            and review_status == "accepted"
            and source is not None
            and target is not None
            and evidence is not None
        ):
            relations.append(
                {
                    "id": relation_id,
                    "type": relation_type,
                    "source": source,
                    "target": target,
                    "reviewStatus": review_status,
                    "evidence": evidence,
                }
            )
    return relations


def parse_public_index_relation_endpoint(
    value: Any,
    field: str,
    errors: list[dict[str, Any]],
) -> dict[str, str] | None:
    if not isinstance(value, dict):
        errors.append(
            public_index_error(
                "public_index_manifest_relation_endpoint_invalid",
                "Public index accepted relation endpoint must be a mapping.",
                field=field,
            )
        )
        return None
    unknown_fields = sorted(set(value) - {"package_id", "version"})
    if unknown_fields:
        errors.append(
            public_index_error(
                "public_index_manifest_relation_endpoint_field_unknown",
                "Public index accepted relation endpoint contains unknown fields.",
                field=field,
                detail={"fields": unknown_fields},
            )
        )
        return None
    package_id = value.get("package_id")
    version = value.get("version")
    endpoint: dict[str, str] = {}
    if not isinstance(package_id, str) or not package_id.strip():
        errors.append(
            public_index_error(
                "public_index_manifest_relation_endpoint_package_id_invalid",
                "Public index accepted relation endpoint package_id must be a non-empty string.",
                field=f"{field}.package_id",
            )
        )
    else:
        endpoint["package_id"] = package_id
    if not isinstance(version, str) or not version.strip():
        errors.append(
            public_index_error(
                "public_index_manifest_relation_endpoint_version_invalid",
                "Public index accepted relation endpoint version must be a non-empty string.",
                field=f"{field}.version",
            )
        )
    else:
        endpoint["version"] = version
    return endpoint if set(endpoint) == {"package_id", "version"} else None


def parse_public_index_relation_evidence(
    value: Any,
    field: str,
    errors: list[dict[str, Any]],
) -> list[dict[str, str]] | None:
    if not isinstance(value, list) or not value:
        errors.append(
            public_index_error(
                "public_index_manifest_relation_evidence_invalid",
                "Public index accepted relation evidence must be a non-empty array.",
                field=field,
            )
        )
        return None

    evidence: list[dict[str, str]] = []
    for index, item in enumerate(value):
        item_field = f"{field}[{index}]"
        if not isinstance(item, dict):
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_evidence_item_invalid",
                    "Public index accepted relation evidence entries must be mappings.",
                    field=item_field,
                )
            )
            continue
        unknown_fields = sorted(set(item) - {"kind", "path"})
        if unknown_fields:
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_evidence_field_unknown",
                    "Public index accepted relation evidence entry contains unknown fields.",
                    field=item_field,
                    detail={"fields": unknown_fields},
                )
            )
            continue
        kind = item.get("kind")
        path = item.get("path")
        if not isinstance(kind, str) or not kind.strip():
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_evidence_kind_invalid",
                    "Public index accepted relation evidence kind must be a non-empty string.",
                    field=f"{item_field}.kind",
                )
            )
            continue
        if not isinstance(path, str) or not path.strip() or Path(path).is_absolute():
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_evidence_path_invalid",
                    "Public index accepted relation evidence path must be a relative string.",
                    field=f"{item_field}.path",
                )
            )
            continue
        if any(part == ".." for part in Path(path).parts):
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_evidence_path_escape",
                    "Public index accepted relation evidence path must not contain "
                    "parent segments.",
                    field=f"{item_field}.path",
                )
            )
            continue
        evidence.append({"kind": kind, "path": path})
    return evidence if evidence else None


def resolve_remote_manifest_package(
    item: dict[str, Any],
    field: str,
    package_path: str,
    remote_root: Path | None,
    errors: list[dict[str, Any]],
) -> Path | None:
    repository = item.get("repository")
    ref = item.get("ref")
    revision = item.get("revision")
    source_errors: list[dict[str, Any]] = []
    source_errors.extend(validate_public_index_repository_url(repository, f"{field}.repository"))
    source_errors.extend(validate_public_index_ref(ref, f"{field}.ref"))
    source_errors.extend(validate_public_index_revision(revision, f"{field}.revision"))
    if remote_root is None:
        source_errors.append(
            public_index_error(
                "public_index_manifest_remote_root_missing",
                "Remote public index manifest entries require a remote source checkout root.",
                field=field,
            )
        )
    if source_errors:
        errors.extend(source_errors)
        return None

    assert isinstance(repository, str)
    assert isinstance(ref, str)
    assert isinstance(revision, str)
    assert remote_root is not None

    normalized_revision = revision.lower()
    checkout = remote_root / public_index_checkout_dir_name(repository, ref, normalized_revision)
    checkout_result = checkout_public_index_repository(repository, ref, checkout)
    if checkout_result["status"] != "ok":
        errors.extend(
            add_public_index_source_context(
                checkout_result["errors"],
                field=field,
                repository=repository,
                ref=ref,
            )
        )
        return None

    actual_revision = str(checkout_result.get("revision", "")).lower()
    expected_revision = normalized_revision
    if actual_revision != expected_revision:
        errors.append(
            public_index_error(
                "public_index_manifest_repository_revision_mismatch",
                "Remote public index package source did not resolve to the pinned revision.",
                field=f"{field}.revision",
                detail={
                    "repository": repository,
                    "ref": ref,
                    "expected": expected_revision,
                    "actual": actual_revision,
                },
            )
        )
        return None

    resolved_package = resolve_inside(checkout, package_path)
    if resolved_package is None:
        errors.append(
            public_index_error(
                "public_index_manifest_package_path_escape",
                "Public index manifest package path must stay inside the checked out repository.",
                field=f"{field}.path",
            )
        )
        return None
    return resolved_package


def add_public_index_source_context(
    issues: list[dict[str, Any]],
    *,
    field: str,
    repository: str,
    ref: str,
) -> list[dict[str, Any]]:
    contextual: list[dict[str, Any]] = []
    for issue in issues:
        updated = dict(issue)
        updated.setdefault("field", field)
        detail = dict(updated.get("detail") or {})
        detail.setdefault("repository", repository)
        detail.setdefault("ref", ref)
        updated["detail"] = detail
        contextual.append(updated)
    return contextual


def prepare_public_index_relations(
    accepted_relations: list[dict[str, Any]],
    packages: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    package_by_identity = {
        (package["package_id"], package["version"]): package for package in packages
    }
    normalized: list[dict[str, Any]] = []

    for index, relation in enumerate(accepted_relations):
        field = f"relations[{index}]"
        source = relation["source"]
        target = relation["target"]
        source_key = (source["package_id"], source["version"])
        target_key = (target["package_id"], target["version"])
        if source_key not in package_by_identity:
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_source_missing",
                    "Public index accepted relation source must reference an accepted "
                    "package version.",
                    field=f"{field}.source",
                    detail={"package_id": source_key[0], "version": source_key[1]},
                )
            )
        if target_key not in package_by_identity:
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_target_missing",
                    "Public index accepted relation target must reference an accepted "
                    "package version.",
                    field=f"{field}.target",
                    detail={"package_id": target_key[0], "version": target_key[1]},
                )
            )
        if source_key == target_key:
            errors.append(
                public_index_error(
                    "public_index_manifest_relation_self_reference",
                    "Public index accepted relation source and target must differ.",
                    field=field,
                )
            )
        if source_key in package_by_identity and target_key in package_by_identity:
            normalized.append(
                remote_package_relation_summary(
                    relation,
                    source_package=package_by_identity[source_key],
                    target_package=package_by_identity[target_key],
                )
            )

    if errors:
        return {"status": "invalid", "relations": [], "errors": errors}
    return {
        "status": "ok",
        "relations": sorted(normalized, key=lambda item: item["id"]),
        "errors": [],
    }


def generate_public_index(
    package_dirs: list[Path],
    output_dir: Path,
    registry_url: str,
    *,
    source_contexts: dict[str, dict[str, Any]] | None = None,
    accepted_relations: list[dict[str, Any]] | None = None,
    build_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_output = output_dir.resolve()
    errors: list[dict[str, Any]] = []

    if not package_dirs:
        errors.append(
            public_index_error(
                "public_index_packages_missing",
                "At least one package directory is required.",
            )
        )
    if not is_allowed_public_index_registry_url(registry_url):
        errors.append(
            public_index_error(
                "public_index_registry_url_invalid",
                "Public index registry URL must be an https URL, except localhost HTTP "
                "development endpoints.",
                field="registry_url",
            )
        )
    if errors:
        return public_index_report("invalid", resolved_output, registry_url, [], errors)

    with tempfile.TemporaryDirectory(prefix="specpm-public-index-") as temp_dir:
        staging_output = Path(temp_dir) / "site"
        packages: list[dict[str, Any]] = []
        seen: dict[tuple[str, str], dict[str, Any]] = {}

        for package_dir in package_dirs:
            package_result = prepare_public_index_package(
                package_dir,
                staging_output,
                registry_url,
                source_context=public_index_source_context(package_dir, source_contexts),
            )
            if package_result["status"] != "ok":
                errors.extend(package_result["errors"])
                continue

            package = package_result["package"]
            identity = (package["package_id"], package["version"])
            existing = seen.get(identity)
            if existing is not None:
                if get_field(existing, "source.digest.value") == get_field(
                    package, "source.digest.value"
                ):
                    continue
                errors.append(
                    public_index_error(
                        "public_index_duplicate_package_conflict",
                        "Public index input contains the same package id and version "
                        "with a different archive digest.",
                        field=f"{identity[0]}@{identity[1]}",
                    )
                )
                continue
            seen[identity] = package
            packages.append(package)

        if errors:
            return public_index_report("invalid", resolved_output, registry_url, [], errors)

        relations_result = prepare_public_index_relations(accepted_relations or [], packages)
        if relations_result["status"] != "ok":
            return public_index_report(
                "invalid",
                resolved_output,
                registry_url,
                [],
                relations_result["errors"],
            )
        relations = relations_result["relations"]

        receipt_files = write_public_index_provenance_receipts(
            staging_output,
            packages,
            registry_url,
            build_metadata=build_metadata,
        )
        payloads = build_public_index_payloads(
            packages,
            relations=relations,
            build_metadata=build_metadata,
        )
        payload_errors = validate_public_index_payloads(payloads)
        if payload_errors:
            return public_index_report("invalid", resolved_output, registry_url, [], payload_errors)

        written_files = write_public_index_payloads(staging_output, payloads)
        written_files.extend(receipt_files)
        written_files.extend(package["archive_path"] for package in packages)
        written_files = sorted(
            {relative_output_path(staging_output, Path(path)) for path in written_files}
        )
        copy_public_index_output(staging_output, resolved_output)

        return public_index_report("ok", resolved_output, registry_url, written_files, [])


def prepare_public_index_package(
    package_dir: Path,
    output_dir: Path,
    registry_url: str,
    *,
    source_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inspection = inspect_package(package_dir)
    validation = inspection["validation"]
    identity = validation.get("package_identity") or {}
    package_id = identity.get("package_id")
    version = identity.get("version")
    if not isinstance(package_id, str) or not isinstance(version, str):
        return {
            "status": "invalid",
            "package": None,
            "errors": [
                public_index_error(
                    "public_index_package_identity_missing",
                    "Package validation did not produce a package id and version.",
                    field=str(package_dir),
                )
            ],
        }

    archive_name = f"{package_id}-{version}.specpm.tgz"
    archive_path = output_dir / "v0/packages" / package_id / "versions" / version / archive_name
    pack_report = pack_package(package_dir, archive_path)
    if pack_report["status"] != "packed":
        return {
            "status": "invalid",
            "package": None,
            "errors": [
                public_index_error(
                    "public_index_pack_failed",
                    "Package could not be packed for public index generation.",
                    field=str(package_dir),
                    detail=pack_report,
                )
            ],
        }

    package_summary = inspection["package"]
    source_url = public_index_url(
        registry_url,
        ["v0", "packages", package_id, "versions", version, archive_name],
    )
    return {
        "status": "ok",
        "package": {
            "package_id": package_id,
            "name": identity.get("name"),
            "version": version,
            "summary": package_summary.get("summary"),
            "license": package_summary.get("license"),
            "keywords": package_summary.get("keywords", []),
            "provided_capabilities": sorted(validation.get("capabilities", [])),
            "required_capabilities": package_summary.get("required_capabilities", []),
            "provided_intents": package_summary.get("intents", []),
            "intent_mappings": package_summary.get("intent_mappings", []),
            "compatibility": package_summary.get("compatibility", {}),
            "state": {"yanked": False, "deprecated": False},
            "source": {
                "kind": "archive",
                "format": pack_report["format"],
                "digest": pack_report["digest"],
                "size": pack_report["archive_size"],
                "url": source_url,
            },
            "accepted_source": public_index_receipt_source(source_context, package_dir),
            "validation": pack_report["validation"],
            "archive_path": str(archive_path),
        },
        "errors": [],
    }


def public_index_source_contexts(
    sources: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for source in sources:
        package_dir = source.get("package_dir")
        if isinstance(package_dir, str) and package_dir:
            contexts[str(Path(package_dir).resolve())] = source
    return contexts


def public_index_source_context(
    package_dir: Path,
    source_contexts: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    resolved = str(package_dir.resolve())
    if source_contexts and resolved in source_contexts:
        return source_contexts[resolved]
    return {
        "kind": "local_path",
        "path": public_index_local_source_path(package_dir),
        "package_dir": resolved,
    }


def public_index_receipt_source(
    source_context: dict[str, Any] | None,
    package_dir: Path,
) -> dict[str, Any]:
    context = source_context or {}
    if context.get("kind") == "git":
        return {
            "kind": "git",
            "repository": context.get("repository"),
            "ref": context.get("ref"),
            "revision": context.get("revision"),
            "path": context.get("path") or ".",
        }
    return {
        "kind": "local_path",
        "path": context.get("path") or public_index_local_source_path(package_dir),
    }


def public_index_local_source_path(package_dir: Path) -> str:
    resolved = package_dir.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(package_dir)


def write_public_index_provenance_receipts(
    output_dir: Path,
    packages: list[dict[str, Any]],
    registry_url: str,
    *,
    build_metadata: dict[str, Any] | None,
) -> list[str]:
    written: list[str] = []
    for package in packages:
        receipt_path = output_dir / provenance_receipt_payload_path(package)
        receipt = public_index_provenance_receipt(package, build_metadata)
        write_json_file(receipt_path, receipt)
        package["provenance_receipt"] = {
            "kind": "provenance_receipt",
            "apiVersion": receipt["apiVersion"],
            "receiptProfile": receipt["receiptProfile"],
            "url": public_index_url(
                registry_url, provenance_receipt_payload_path(package).split("/")
            ),
            "digest": {
                "algorithm": "sha256",
                "value": sha256_file(receipt_path),
            },
            "size": receipt_path.stat().st_size,
        }
        written.append(str(receipt_path))

        index_html_path = receipt_path.with_name("index.html")
        write_json_file(index_html_path, receipt)
        written.append(str(index_html_path))
    return written


def public_index_provenance_receipt(
    package: dict[str, Any],
    build_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata = build_metadata or {}
    validation = package.get("validation", {})
    warning_count = len(validation.get("warnings", [])) if isinstance(validation, dict) else 0
    error_count = len(validation.get("errors", [])) if isinstance(validation, dict) else 0
    validation_status = public_index_receipt_validation_status(
        validation, warning_count=warning_count, error_count=error_count
    )
    source = package.get("accepted_source", {})
    state = package.get("state", {})
    archive_digest = package["source"]["digest"]["value"]
    build_revision = str(metadata.get("revision") or "unknown").strip() or "unknown"
    build_number = str(metadata.get("build_number") or "").strip()
    issued_at = str(metadata.get("issued_at") or "").strip() or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")

    build: dict[str, Any] = {
        "provider": "github_actions" if build_number and build_number != "local" else "local",
        "workflow": "specpm public-index generate",
        "revision": build_revision,
        "builder": "SpecPM",
        "implementation": public_index_implementation_metadata(metadata),
    }
    if build_number:
        build["runId"] = build_number

    audit_evidence: list[dict[str, Any]] = [
        {
            "kind": "archive_digest",
            "digest": package["source"]["digest"],
            "retention": "public-static-index",
        },
        {
            "kind": "registry_payload",
            "path": version_payload_path(package),
            "retention": "public-static-index",
        },
    ]
    if isinstance(source, dict) and source.get("kind") == "git":
        audit_evidence.insert(
            0,
            {
                "kind": "source_commit",
                "repository": source.get("repository"),
                "revision": source.get("revision"),
                "retention": "git-history",
            },
        )

    return {
        "apiVersion": "specpm.receipts/v0",
        "kind": "SpecPMProvenanceReceipt",
        "schemaVersion": 1,
        "receiptProfile": "public_static_index_build_v0",
        "receiptId": (f"{package['package_id']}@{package['version']}:sha256:{archive_digest[:12]}"),
        "issuedAt": issued_at,
        "subject": {
            "packageId": package["package_id"],
            "version": package["version"],
            "registryProfile": "public_static_index",
        },
        "source": source,
        "archive": package["source"],
        "review": public_index_receipt_review(source),
        "build": build,
        "validation": {
            "status": validation_status,
            "warningCount": warning_count,
            "errorCount": error_count,
            "validatorVersion": public_index_implementation_metadata(metadata)["version"],
        },
        "trust": {
            "policy": "specs/PACKAGE_SIGNING_REVOCATION.md",
            "signatureRequired": False,
            "signatureStatus": "not_applicable",
            "revocationStatus": "not_checked",
        },
        "lifecycle": {
            "state": public_index_receipt_lifecycle_state(state),
            "yanked": isinstance(state, dict) and state.get("yanked") is True,
            "deprecated": isinstance(state, dict) and state.get("deprecated") is True,
            "revoked": isinstance(state, dict) and state.get("revoked") is True,
        },
        "audit": {
            "evidence": audit_evidence,
        },
    }


def public_index_receipt_validation_status(
    validation: Any,
    *,
    warning_count: int,
    error_count: int,
) -> str:
    status = validation.get("status") if isinstance(validation, dict) else None
    if status == "invalid" or error_count > 0:
        return "invalid"
    if status == "warning_only" or warning_count > 0:
        return "warning"
    return "valid"


def public_index_receipt_lifecycle_state(state: Any) -> str:
    if not isinstance(state, dict):
        return "visible"
    if state.get("revoked") is True:
        return "revoked"
    if state.get("yanked") is True:
        return "yanked"
    if state.get("deprecated") is True:
        return "deprecated"
    return "visible"


def public_index_receipt_review(source: Any) -> dict[str, Any]:
    review: dict[str, Any] = {
        "kind": "manual",
        "decision": "accepted",
    }
    if isinstance(source, dict) and source.get("kind") == "git":
        review["commit"] = source.get("revision")
    return review


def build_public_index_payloads(
    packages: list[dict[str, Any]],
    *,
    relations: list[dict[str, Any]] | None = None,
    build_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    packages = sorted(packages, key=public_index_package_sort_key)
    relations = sorted(relations or [], key=lambda item: item["id"])
    implementation = public_index_implementation_metadata(build_metadata)
    intent_matches = observed_intent_matches(packages)
    payloads: list[dict[str, Any]] = [
        {
            "path": registry_root_payload_path(),
            "payload": remote_registry_root_payload(packages, relations, implementation),
        },
        {
            "path": registry_status_payload_path(),
            "payload": remote_registry_status_payload(packages, relations, implementation),
        },
        {
            "path": package_index_payload_path(),
            "payload": remote_package_index_payload(packages, relations),
        },
        {
            "path": relations_index_payload_path(),
            "payload": remote_package_relations_payload(relations),
        },
        {
            "path": intent_index_payload_path(),
            "payload": remote_intent_index_payload(intent_matches),
        },
    ]

    packages_by_id: dict[str, list[dict[str, Any]]] = {}
    capability_matches: dict[str, list[dict[str, Any]]] = {}
    for package in packages:
        packages_by_id.setdefault(package["package_id"], []).append(package)
        payloads.append(
            {
                "path": version_payload_path(package),
                "payload": remote_package_version_payload(package, relations),
            }
        )
        for capability_id in package["provided_capabilities"]:
            capability_matches.setdefault(capability_id, []).append(package)

    for package_id, versions in sorted(packages_by_id.items()):
        payloads.append(
            {
                "path": package_payload_path(package_id),
                "payload": remote_package_payload(versions, relations),
            }
        )

    for capability_id, matches in sorted(capability_matches.items()):
        payloads.append(
            {
                "path": capability_payload_path(capability_id),
                "payload": remote_capability_search_payload(capability_id, matches, relations),
            }
        )

    for intent_id, matches in sorted(intent_matches.items()):
        payloads.append(
            {
                "path": intent_payload_path(intent_id),
                "payload": remote_intent_search_payload(intent_id, matches, relations),
            }
        )
        payloads.append(
            {
                "path": intent_summary_payload_path(intent_id),
                "payload": remote_intent_payload(intent_id, matches),
            }
        )

    return sorted(payloads, key=lambda item: item["path"])


def observed_intent_matches(packages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    matches: dict[str, list[dict[str, Any]]] = {}
    for package in packages:
        for intent_id in package.get("provided_intents", []):
            if isinstance(intent_id, str):
                matches.setdefault(intent_id, []).append(package)
    return matches


def remote_registry_status_payload(
    packages: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    implementation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemoteRegistryStatus",
        "status": "ok",
        "registry": remote_registry_summary(packages, relations, implementation),
    }


def remote_registry_root_payload(
    packages: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    implementation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemoteRegistryRoot",
        "status": "ok",
        "registry": remote_registry_summary(packages, relations, implementation),
        "endpoints": {
            "status": registry_status_payload_path(),
            "packages": package_index_payload_path(),
            "relations": relations_index_payload_path(),
            "intents": intent_index_payload_path(),
        },
    }


def remote_registry_summary(
    packages: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    implementation: dict[str, Any],
) -> dict[str, Any]:
    package_ids = {package["package_id"] for package in packages}
    capabilities = {
        capability
        for package in packages
        for capability in package.get("provided_capabilities", [])
        if isinstance(capability, str)
    }
    intents = {
        intent
        for package in packages
        for intent in package.get("provided_intents", [])
        if isinstance(intent, str)
    }
    return {
        "profile": "public_static_index",
        "api_version": "v0",
        "read_only": True,
        "authority": "metadata_only",
        "package_count": len(package_ids),
        "version_count": len(packages),
        "capability_count": len(capabilities),
        "intent_count": len(intents),
        "relation_count": len(relations),
        "supportedFeatures": [
            "package_sets",
            "package_relations",
            "search_result_scope",
        ],
        "provenance_receipt_count": sum(
            1 for package in packages if isinstance(package.get("provenance_receipt"), dict)
        ),
        "implementation": implementation,
    }


def public_index_implementation_metadata(
    build_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata = build_metadata or {}
    version = str(metadata.get("version") or __version__).strip() or __version__
    implementation: dict[str, Any] = {
        "name": "SpecPM",
        "version": version,
    }

    build: dict[str, str] = {}
    build_number = str(metadata.get("build_number") or "").strip()
    if build_number:
        build["number"] = build_number

    revision = str(metadata.get("revision") or "").strip()
    if revision:
        build["revision"] = revision
        build["revision_short"] = revision[:12]

    if build:
        implementation["build"] = build
    return implementation


def remote_package_index_payload(
    packages: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    packages_by_id: dict[str, list[dict[str, Any]]] = {}
    for package in sorted(packages, key=public_index_package_sort_key):
        packages_by_id.setdefault(package["package_id"], []).append(package)

    package_summaries = [
        remote_package_payload(versions, relations)["package"]
        for _, versions in sorted(packages_by_id.items())
    ]
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemotePackageIndex",
        "status": "ok",
        "package_count": len(package_summaries),
        "version_count": len(packages),
        "packages": package_summaries,
    }


def remote_package_payload(
    versions: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    versions = sorted(versions, key=public_index_package_sort_key)
    latest = max(versions, key=public_index_latest_key)
    capabilities = sorted(
        {
            capability
            for package in versions
            for capability in package.get("provided_capabilities", [])
            if isinstance(capability, str)
        }
    )
    intents = sorted(
        {
            intent
            for package in versions
            for intent in package.get("provided_intents", [])
            if isinstance(intent, str)
        }
    )
    package_payload = {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemotePackage",
        "status": "ok",
        "package": {
            "package_id": latest["package_id"],
            "name": latest["name"],
            "summary": latest["summary"],
            "license": latest["license"],
            "latest_version": latest["version"],
            "capabilities": capabilities,
            "intents": intents,
            "keywords": latest.get("keywords", []),
            "versions": [
                {
                    "version": package["version"],
                    "yanked": package["state"]["yanked"],
                    "deprecated": package["state"]["deprecated"],
                }
                for package in versions
            ],
        },
    }
    package_payload["package"].update(
        package_relation_fields(latest, relations, include_members=True)
    )
    return package_payload


def remote_package_version_payload(
    package: dict[str, Any],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemotePackageVersion",
        "status": "ok",
        "package": {
            "package_id": package["package_id"],
            "name": package["name"],
            "version": package["version"],
            "summary": package["summary"],
            "license": package["license"],
            "provided_capabilities": package["provided_capabilities"],
            "required_capabilities": package["required_capabilities"],
            "provided_intents": package.get("provided_intents", []),
            "intent_mappings": package.get("intent_mappings", []),
            "compatibility": package["compatibility"],
            "state": package["state"],
            "source": package["source"],
            "provenance_receipt": package.get("provenance_receipt"),
        },
    }
    payload["package"].update(package_relation_fields(package, relations, include_members=True))
    return payload


def remote_package_relations_payload(relations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemotePackageRelations",
        "status": "ok",
        "relation_count": len(relations),
        "relations": relations,
    }


def remote_package_relation_summary(
    relation: dict[str, Any],
    *,
    source_package: dict[str, Any],
    target_package: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": relation["id"],
        "type": relation["type"],
        "source": source_package["package_id"],
        "target": target_package["package_id"],
        "versionScope": {
            "sourceVersion": source_package["version"],
            "targetVersion": target_package["version"],
        },
        "reviewStatus": relation["reviewStatus"],
        "evidence": relation["evidence"],
    }


def package_relation_fields(
    package: dict[str, Any],
    relations: list[dict[str, Any]],
    *,
    include_members: bool,
) -> dict[str, Any]:
    outgoing = package_outgoing_relations(package, relations)
    context = package_relation_context(package, relations)
    subject_scope = "aggregate" if outgoing else "package"
    fields: dict[str, Any] = {
        "subject": {
            "kind": "package_set" if outgoing else "package",
            "scope": subject_scope,
        },
        "scope": subject_scope,
        "match": "direct",
    }
    if context:
        fields["relationContext"] = context
    if include_members and outgoing:
        fields["packageSet"] = {
            "profile": "specpm.package_set/v0",
            "setType": "workspace",
            "members": [
                {
                    "package_id": relation["target"],
                    "version": relation["versionScope"]["targetVersion"],
                    "type": relation["type"],
                    "relation_id": relation["id"],
                }
                for relation in outgoing
            ],
        }
    return fields


def package_relation_context(
    package: dict[str, Any],
    relations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    package_id = package["package_id"]
    version = package["version"]
    context = [
        relation
        for relation in relations
        if (
            relation["source"] == package_id
            and relation["versionScope"]["sourceVersion"] == version
        )
        or (
            relation["target"] == package_id
            and relation["versionScope"]["targetVersion"] == version
        )
    ]
    return sorted(context, key=lambda item: item["id"])


def package_outgoing_relations(
    package: dict[str, Any],
    relations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    package_id = package["package_id"]
    version = package["version"]
    return sorted(
        [
            relation
            for relation in relations
            if relation["source"] == package_id
            and relation["versionScope"]["sourceVersion"] == version
        ],
        key=lambda item: item["id"],
    )


def remote_intent_index_payload(
    intent_matches: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    intents = [
        observed_intent_summary(intent_id, matches)
        for intent_id, matches in sorted(intent_matches.items())
    ]
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemoteIntentIndex",
        "status": "ok",
        "catalog": observed_intent_catalog_metadata(),
        "intent_count": len(intents),
        "intents": intents,
    }


def remote_intent_payload(intent_id: str, packages: list[dict[str, Any]]) -> dict[str, Any]:
    packages = sorted(packages, key=public_index_package_sort_key)
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemoteIntent",
        "status": "ok",
        "catalog": observed_intent_catalog_metadata(),
        "intent": observed_intent_summary(intent_id, packages),
        "packages": [
            {
                "package_id": package["package_id"],
                "version": package["version"],
                "name": package["name"],
                "summary": package["summary"],
                "matched_capabilities": matched_capabilities_for_intent(package, intent_id),
                "provided_intents": package.get("provided_intents", []),
                "provided_capabilities": package["provided_capabilities"],
                "required_capabilities": package["required_capabilities"],
                "license": package["license"],
                "yanked": package["state"]["yanked"],
                "deprecated": package["state"]["deprecated"],
            }
            for package in packages
        ],
    }


def observed_intent_catalog_metadata() -> dict[str, Any]:
    return {
        "authority": "observed_metadata_only",
        "canonical": False,
        "description": (
            "Observed intent IDs are collected from accepted package metadata; "
            "package declaration does not make an intent ID canonical."
        ),
    }


def observed_intent_summary(intent_id: str, packages: list[dict[str, Any]]) -> dict[str, Any]:
    packages = sorted(packages, key=public_index_package_sort_key)
    package_ids = sorted({package["package_id"] for package in packages})
    capabilities = sorted(
        {
            capability_id
            for package in packages
            for capability_id in matched_capabilities_for_intent(package, intent_id)
        }
    )
    return {
        "intent_id": intent_id,
        "status": "observed",
        "canonical": False,
        "package_count": len(package_ids),
        "version_count": len(packages),
        "capability_count": len(capabilities),
        "package_ids": package_ids,
        "capabilities": capabilities,
    }


def remote_capability_search_payload(
    capability_id: str,
    packages: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    packages = sorted(packages, key=public_index_package_sort_key)
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemoteCapabilitySearch",
        "status": "ok",
        "query": {
            "capability_id": capability_id,
            "match": "exact",
        },
        "result_count": len(packages),
        "results": [
            {
                "package_id": package["package_id"],
                "version": package["version"],
                "name": package["name"],
                "summary": package["summary"],
                "matched_capability": capability_id,
                "provided_intents": package.get("provided_intents", []),
                "provided_capabilities": package["provided_capabilities"],
                "required_capabilities": package["required_capabilities"],
                "license": package["license"],
                "yanked": package["state"]["yanked"],
                "deprecated": package["state"]["deprecated"],
                "source": package["source"],
                **package_relation_fields(package, relations, include_members=False),
            }
            for package in packages
        ],
    }


def remote_intent_search_payload(
    intent_id: str,
    packages: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    packages = sorted(packages, key=public_index_package_sort_key)
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemoteIntentSearch",
        "status": "ok",
        "query": {
            "intent_id": intent_id,
            "match": "exact",
        },
        "result_count": len(packages),
        "results": [
            {
                "package_id": package["package_id"],
                "version": package["version"],
                "name": package["name"],
                "summary": package["summary"],
                "matched_intent": intent_id,
                "matched_capabilities": matched_capabilities_for_intent(package, intent_id),
                "provided_intents": package.get("provided_intents", []),
                "provided_capabilities": package["provided_capabilities"],
                "required_capabilities": package["required_capabilities"],
                "license": package["license"],
                "yanked": package["state"]["yanked"],
                "deprecated": package["state"]["deprecated"],
                "source": package["source"],
                **package_relation_fields(package, relations, include_members=False),
            }
            for package in packages
        ],
    }


def matched_capabilities_for_intent(package: dict[str, Any], intent_id: str) -> list[str]:
    capability_ids = {
        mapping.get("capability_id")
        for mapping in package.get("intent_mappings", [])
        if isinstance(mapping, dict) and mapping.get("intent_id") == intent_id
    }
    return sorted(
        capability_id for capability_id in capability_ids if isinstance(capability_id, str)
    )


def validate_public_index_payloads(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for item in payloads:
        for issue in validate_remote_registry_payload(item["payload"]):
            payload = issue.to_dict()
            payload["path"] = item["path"]
            errors.append(payload)
    return errors


def write_public_index_payloads(output_dir: Path, payloads: list[dict[str, Any]]) -> list[str]:
    written: list[str] = []
    for item in payloads:
        json_path = output_dir / item["path"]
        write_json_file(json_path, item["payload"])
        written.append(str(json_path))

        index_html_path = json_path.with_name("index.html")
        write_json_file(index_html_path, item["payload"])
        written.append(str(index_html_path))
    return written


def copy_public_index_output(staging_output: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_v0 = output_dir / "v0"
    if output_v0.exists():
        shutil.rmtree(output_v0)
    shutil.copytree(staging_output / "v0", output_v0)


def public_index_package_sort_key(
    package: dict[str, Any],
) -> tuple[str, tuple[tuple[int, int, int], int, tuple[tuple[int, int | str], ...], str]]:
    return (package["package_id"], public_index_semver_key(package.get("version")))


def public_index_latest_key(
    package: dict[str, Any],
) -> tuple[tuple[int, int, int], int, tuple[tuple[int, int | str], ...], str]:
    return public_index_semver_key(package.get("version"))


def public_index_semver_key(
    version: Any,
) -> tuple[tuple[int, int, int], int, tuple[tuple[int, int | str], ...], str]:
    base_version = semver_key(version) or (0, 0, 0)
    if not isinstance(version, str):
        return (base_version, 1, (), "")

    public_version = version.split("+", 1)[0]
    if "-" not in public_version:
        return (base_version, 1, (), version)

    prerelease = public_version.split("-", 1)[1]
    identifiers: list[tuple[int, int | str]] = []
    for identifier in prerelease.split("."):
        if identifier.isdigit():
            identifiers.append((0, int(identifier)))
        else:
            identifiers.append((1, identifier))
    return (base_version, 0, tuple(identifiers), version)


def registry_root_payload_path() -> str:
    return "v0/index.json"


def package_payload_path(package_id: str) -> str:
    return f"v0/packages/{package_id}/index.json"


def package_index_payload_path() -> str:
    return "v0/packages/index.json"


def relations_index_payload_path() -> str:
    return "v0/relations/index.json"


def registry_status_payload_path() -> str:
    return "v0/status/index.json"


def version_payload_path(package: dict[str, Any]) -> str:
    return f"v0/packages/{package['package_id']}/versions/{package['version']}/index.json"


def provenance_receipt_payload_path(package: dict[str, Any]) -> str:
    return (
        f"v0/packages/{package['package_id']}/versions/"
        f"{package['version']}/provenance-receipt/index.json"
    )


def capability_payload_path(capability_id: str) -> str:
    return f"v0/capabilities/{capability_id}/packages/index.json"


def intent_payload_path(intent_id: str) -> str:
    return f"v0/intents/{intent_id}/packages/index.json"


def intent_summary_payload_path(intent_id: str) -> str:
    return f"v0/intents/{intent_id}/index.json"


def intent_index_payload_path() -> str:
    return "v0/intents/index.json"


def public_index_url(registry_url: str, parts: list[str]) -> str:
    base = registry_url.rstrip("/")
    path = "/".join(quote(part, safe="._-+") for part in parts)
    return f"{base}/{path}"


def is_allowed_public_index_registry_url(registry_url: str) -> bool:
    if not isinstance(registry_url, str) or not registry_url.strip():
        return False
    parsed = urlparse(registry_url.strip())
    if parsed.username or parsed.password or parsed.params or parsed.query or parsed.fragment:
        return False
    if parsed.scheme == "https" and parsed.netloc:
        return True
    return (
        parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        and not parsed.username
        and not parsed.password
    )


def relative_output_path(output_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(output_dir.resolve()).as_posix()


def public_index_report(
    status: str,
    output_dir: Path,
    registry_url: str,
    written_files: list[str],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schemaVersion": PUBLIC_INDEX_REPORT_SCHEMA_VERSION,
        "status": status,
        "output": str(output_dir),
        "registry": registry_url,
        "written_count": len(written_files),
        "written_files": written_files,
        "errors": errors,
    }


def public_index_manifest_report(
    status: str,
    manifest_path: Path,
    root: Path,
    package_dirs: list[Path],
    sources: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schemaVersion": PUBLIC_INDEX_MANIFEST_REPORT_SCHEMA_VERSION,
        "status": status,
        "manifest": str(manifest_path),
        "root": str(root),
        "package_dirs": [str(package_dir) for package_dir in package_dirs],
        "sources": sources,
        "relations": relations,
        "errors": errors,
    }


def validate_public_index_repository_url(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, str) or not value.strip():
        return [
            public_index_error(
                "public_index_manifest_repository_invalid",
                "Remote public index manifest repository must be a non-empty string.",
                field=field,
            )
        ]
    if value != value.strip():
        return [
            public_index_error(
                "public_index_manifest_repository_invalid",
                "Remote public index manifest repository must not contain leading "
                "or trailing whitespace.",
                field=field,
            )
        ]

    parsed = urlparse(value)
    errors: list[dict[str, Any]] = []
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(
            public_index_error(
                "public_index_manifest_repository_url_invalid",
                "Remote public index manifest repository must be an https URL with a hostname.",
                field=field,
            )
        )
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        errors.append(
            public_index_error(
                "public_index_manifest_repository_url_path_invalid",
                "Remote public index manifest repository URL must include an owner "
                "and repository path.",
                field=field,
            )
        )
    if parsed.username or parsed.password:
        errors.append(
            public_index_error(
                "public_index_manifest_repository_url_credentials",
                "Remote public index manifest repository URL must not embed credentials.",
                field=field,
            )
        )
    if parsed.params or parsed.query:
        errors.append(
            public_index_error(
                "public_index_manifest_repository_url_query",
                "Remote public index manifest repository URL must not include query parameters.",
                field=field,
            )
        )
    if parsed.fragment:
        errors.append(
            public_index_error(
                "public_index_manifest_repository_url_fragment",
                "Remote public index manifest repository URL must not include a fragment.",
                field=field,
            )
        )
    return errors


def validate_public_index_ref(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, str) or not value.strip():
        return [
            public_index_error(
                "public_index_manifest_ref_invalid",
                "Remote public index manifest ref must be a non-empty string.",
                field=field,
            )
        ]
    ref = value.strip()
    if value != ref:
        return [
            public_index_error(
                "public_index_manifest_ref_invalid",
                "Remote public index manifest ref must not contain leading or trailing whitespace.",
                field=field,
            )
        ]
    if (
        not GIT_REF_PATTERN.fullmatch(ref)
        or ".." in ref
        or "@{" in ref
        or ref.startswith(("-", "/", "."))
        or ref.endswith(("/", ".", ".lock"))
        or "//" in ref
    ):
        return [
            public_index_error(
                "public_index_manifest_ref_invalid",
                "Remote public index manifest ref must be a safe branch or tag name.",
                field=field,
            )
        ]
    return []


def validate_public_index_revision(value: Any, field: str) -> list[dict[str, Any]]:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not GIT_REVISION_PATTERN.fullmatch(value)
    ):
        return [
            public_index_error(
                "public_index_manifest_revision_invalid",
                "Remote public index manifest revision must be a 40-character Git commit SHA.",
                field=field,
            )
        ]
    return []


def checkout_public_index_repository(
    repository_url: str,
    ref: str,
    checkout: Path,
) -> dict[str, Any]:
    if checkout.exists():
        shutil.rmtree(checkout)
    checkout.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--filter",
        "blob:none",
        "--no-tags",
        "--no-recurse-submodules",
        "--single-branch",
        "--branch",
        ref,
        repository_url,
        str(checkout),
    ]
    env = os.environ.copy()
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    completed = run_public_index_git_command(command, env=env)
    if completed["status"] != "ok":
        return completed

    revision = run_public_index_git_command(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        env=env,
    )
    if revision["status"] != "ok":
        return revision
    return {
        "status": "ok",
        "revision": revision["stdout"].strip().lower(),
        "errors": [],
    }


def run_public_index_git_command(command: list[str], *, env: dict[str, str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "invalid",
            "stdout": "",
            "errors": [
                public_index_error(
                    "public_index_manifest_repository_checkout_failed",
                    f"Remote public index package source could not be checked out: {exc}",
                )
            ],
        }
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        return {
            "status": "invalid",
            "stdout": completed.stdout,
            "errors": [
                public_index_error(
                    "public_index_manifest_repository_checkout_failed",
                    message,
                )
            ],
        }
    return {"status": "ok", "stdout": completed.stdout, "errors": []}


def public_index_checkout_dir_name(repository_url: str, ref: str, revision: str) -> str:
    digest = hashlib.sha256(f"{repository_url}\0{ref}\0{revision}".encode()).hexdigest()
    name = Path(urlparse(repository_url).path).name.removesuffix(".git") or "repository"
    sanitized = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in name)
    return f"{sanitized}-{digest[:12]}"


def public_index_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    issue = Issue("error", code, message, "public-index", field).to_dict()
    if detail is not None:
        issue["detail"] = detail
    return issue
