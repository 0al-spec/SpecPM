from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from specpm.core import (
    REMOTE_REGISTRY_API_VERSION,
    REMOTE_REGISTRY_SCHEMA_VERSION,
    Issue,
    get_field,
    inspect_package,
    pack_package,
    semver_key,
    validate_remote_registry_payload,
    write_json_file,
)

PUBLIC_INDEX_REPORT_SCHEMA_VERSION = 1


def generate_public_index(
    package_dirs: list[Path],
    output_dir: Path,
    registry_url: str,
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
            package_result = prepare_public_index_package(package_dir, staging_output, registry_url)
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

        payloads = build_public_index_payloads(packages)
        payload_errors = validate_public_index_payloads(payloads)
        if payload_errors:
            return public_index_report("invalid", resolved_output, registry_url, [], payload_errors)

        written_files = write_public_index_payloads(staging_output, payloads)
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
            "compatibility": package_summary.get("compatibility", {}),
            "state": {"yanked": False, "deprecated": False},
            "source": {
                "kind": "archive",
                "format": pack_report["format"],
                "digest": pack_report["digest"],
                "size": pack_report["archive_size"],
                "url": source_url,
            },
            "archive_path": str(archive_path),
        },
        "errors": [],
    }


def build_public_index_payloads(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packages = sorted(packages, key=public_index_package_sort_key)
    payloads: list[dict[str, Any]] = [
        {
            "path": registry_status_payload_path(),
            "payload": remote_registry_status_payload(packages),
        },
        {
            "path": package_index_payload_path(),
            "payload": remote_package_index_payload(packages),
        },
    ]

    packages_by_id: dict[str, list[dict[str, Any]]] = {}
    capability_matches: dict[str, list[dict[str, Any]]] = {}
    for package in packages:
        packages_by_id.setdefault(package["package_id"], []).append(package)
        payloads.append(
            {
                "path": version_payload_path(package),
                "payload": remote_package_version_payload(package),
            }
        )
        for capability_id in package["provided_capabilities"]:
            capability_matches.setdefault(capability_id, []).append(package)

    for package_id, versions in sorted(packages_by_id.items()):
        payloads.append(
            {
                "path": package_payload_path(package_id),
                "payload": remote_package_payload(versions),
            }
        )

    for capability_id, matches in sorted(capability_matches.items()):
        payloads.append(
            {
                "path": capability_payload_path(capability_id),
                "payload": remote_capability_search_payload(capability_id, matches),
            }
        )

    return sorted(payloads, key=lambda item: item["path"])


def remote_registry_status_payload(packages: list[dict[str, Any]]) -> dict[str, Any]:
    package_ids = {package["package_id"] for package in packages}
    capabilities = {
        capability
        for package in packages
        for capability in package.get("provided_capabilities", [])
        if isinstance(capability, str)
    }
    return {
        "apiVersion": REMOTE_REGISTRY_API_VERSION,
        "schemaVersion": REMOTE_REGISTRY_SCHEMA_VERSION,
        "kind": "RemoteRegistryStatus",
        "status": "ok",
        "registry": {
            "profile": "public_static_index",
            "api_version": "v0",
            "read_only": True,
            "authority": "metadata_only",
            "package_count": len(package_ids),
            "version_count": len(packages),
            "capability_count": len(capabilities),
        },
    }


def remote_package_index_payload(packages: list[dict[str, Any]]) -> dict[str, Any]:
    packages_by_id: dict[str, list[dict[str, Any]]] = {}
    for package in sorted(packages, key=public_index_package_sort_key):
        packages_by_id.setdefault(package["package_id"], []).append(package)

    package_summaries = [
        remote_package_payload(versions)["package"]
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


def remote_package_payload(versions: list[dict[str, Any]]) -> dict[str, Any]:
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
    return {
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


def remote_package_version_payload(package: dict[str, Any]) -> dict[str, Any]:
    return {
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
            "compatibility": package["compatibility"],
            "state": package["state"],
            "source": package["source"],
        },
    }


def remote_capability_search_payload(
    capability_id: str,
    packages: list[dict[str, Any]],
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
                "provided_capabilities": package["provided_capabilities"],
                "required_capabilities": package["required_capabilities"],
                "license": package["license"],
                "yanked": package["state"]["yanked"],
                "deprecated": package["state"]["deprecated"],
                "source": package["source"],
            }
            for package in packages
        ],
    }


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


def package_payload_path(package_id: str) -> str:
    return f"v0/packages/{package_id}/index.json"


def package_index_payload_path() -> str:
    return "v0/packages/index.json"


def registry_status_payload_path() -> str:
    return "v0/status/index.json"


def version_payload_path(package: dict[str, Any]) -> str:
    return f"v0/packages/{package['package_id']}/versions/{package['version']}/index.json"


def capability_payload_path(capability_id: str) -> str:
    return f"v0/capabilities/{capability_id}/packages/index.json"


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
