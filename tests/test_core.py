from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

import yaml

from specpm.cli import main
from specpm.core import (
    add_package,
    diff_packages,
    index_package,
    inspect_inbox_bundle,
    inspect_package,
    list_inbox,
    pack_package,
    search_index,
    validate_package,
)

ROOT = Path(__file__).resolve().parents[1]
SPECGRAPH_FIXTURE_ROOT = ROOT / "tests/fixtures/specgraph_exports"
GOLDEN_FIXTURE_ROOT = ROOT / "tests/fixtures/golden"


def write_index_payload(index_path: Path, packages: list[dict[str, Any]]) -> None:
    capabilities: dict[str, list[dict[str, str]]] = {}
    for package in packages:
        package_id = package["package_id"]
        version = package["version"]
        for capability in package.get("provided_capabilities", []):
            capabilities.setdefault(capability, []).append(
                {"package_id": package_id, "version": version}
            )
    index_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "packages": packages,
                "capabilities": capabilities,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def indexed_email_entry(tmp_path: Path) -> dict[str, Any]:
    index_path = tmp_path / "source-index.json"
    index_package(ROOT / "examples/email_tools", index_path)
    return json.loads(index_path.read_text(encoding="utf-8"))["packages"][0]


def load_yaml_file(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def write_yaml_file(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def copy_email_package(tmp_path: Path, name: str) -> Path:
    package = tmp_path / name
    shutil.copytree(ROOT / "examples/email_tools", package)
    return package


def assert_golden_json(
    fixture_name: str, payload: dict[str, Any], tmp_path: Path | None = None
) -> None:
    expected = json.loads((GOLDEN_FIXTURE_ROOT / fixture_name).read_text(encoding="utf-8"))
    assert normalize_json_contract(payload, tmp_path) == expected


def normalize_json_contract(payload: Any, tmp_path: Path | None = None) -> Any:
    replacements = path_replacements(tmp_path)
    return normalize_json_contract_value(payload, replacements)


def path_replacements(tmp_path: Path | None = None) -> list[tuple[str, str]]:
    replacements = path_variants(ROOT, "<repo>")
    if tmp_path is not None:
        replacements.extend(path_variants(tmp_path, "<tmp>"))
    return sorted(set(replacements), key=lambda item: len(item[0]), reverse=True)


def path_variants(path: Path, placeholder: str) -> list[tuple[str, str]]:
    variants = {str(path), str(path.resolve())}
    for variant in list(variants):
        if variant.startswith("/private/"):
            variants.add(variant.removeprefix("/private"))
        else:
            variants.add(f"/private{variant}")
    return [(variant, placeholder) for variant in variants]


def normalize_json_contract_value(value: Any, replacements: list[tuple[str, str]]) -> Any:
    if isinstance(value, dict):
        return {
            key: normalize_json_contract_value(item, replacements) for key, item in value.items()
        }
    if isinstance(value, list):
        return [normalize_json_contract_value(item, replacements) for item in value]
    if isinstance(value, str):
        normalized = value
        for prefix, placeholder in replacements:
            normalized = normalized.replace(prefix, placeholder)
        return normalized
    return value


def test_rfc_example_validates() -> None:
    report = validate_package(ROOT / "examples/email_tools")

    assert report["status"] == "valid"
    assert report["error_count"] == 0
    assert report["capabilities"] == ["document_conversion.email_to_markdown"]


def test_specgraph_export_is_visible_as_warning_only_draft() -> None:
    report = validate_package(SPECGRAPH_FIXTURE_ROOT / "specgraph.core_repository_facade")
    fixture = json.loads(
        (ROOT / "tests/fixtures/specgraph_core_repository_facade.validation.json").read_text(
            encoding="utf-8"
        )
    )

    assert report == fixture


def test_golden_validation_json_contract() -> None:
    assert_golden_json(
        "validate-email-tools.json",
        validate_package(ROOT / "examples/email_tools"),
    )


def test_golden_inspect_json_contract() -> None:
    assert_golden_json(
        "inspect-email-tools.json",
        inspect_package(ROOT / "examples/email_tools"),
    )


def test_golden_search_json_contract(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    assert_golden_json(
        "search-email-tools.json",
        search_index("document_conversion.email_to_markdown", index_path),
        tmp_path,
    )


def test_golden_pack_json_contract(tmp_path: Path) -> None:
    assert_golden_json(
        "pack-email-tools.json",
        pack_package(ROOT / "examples/email_tools", tmp_path / "email_tools.specpm.tgz"),
        tmp_path,
    )


def test_golden_add_json_contract(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    index_package(ROOT / "examples/email_tools", index_path)

    assert_golden_json(
        "add-email-tools.json",
        add_package("document_conversion.email_to_markdown", index_path, project),
        tmp_path,
    )


def test_golden_inbox_list_json_contract() -> None:
    assert_golden_json(
        "inbox-list-specgraph.json",
        list_inbox(SPECGRAPH_FIXTURE_ROOT),
    )


def test_golden_inbox_inspect_json_contract() -> None:
    assert_golden_json(
        "inbox-inspect-specgraph.json",
        inspect_inbox_bundle(SPECGRAPH_FIXTURE_ROOT, "specgraph.core_repository_facade"),
    )


def test_golden_diff_json_contract() -> None:
    assert_golden_json(
        "diff-email-tools-unchanged.json",
        diff_packages(ROOT / "examples/email_tools", ROOT / "examples/email_tools"),
    )


def test_inbox_lists_specgraph_export() -> None:
    report = list_inbox(SPECGRAPH_FIXTURE_ROOT)
    bundle = report["bundles"][0]

    assert bundle["package_id"] == "specgraph.core_repository_facade"
    assert bundle["inbox_status"] == "draft_visible"
    assert bundle["layout"]["has_manifest"] is True
    assert bundle["layout"]["has_main_spec"] is True
    assert bundle["layout"]["has_handoff"] is True
    assert bundle["handoff_summary"]["handoff_id"] == (
        "specpm_handoff::specgraph_core_repository_facade"
    )


def test_inbox_inspect_returns_viewer_card_payload() -> None:
    report = inspect_inbox_bundle(SPECGRAPH_FIXTURE_ROOT, "specgraph.core_repository_facade")

    assert report["found"] is True
    assert report["inbox_status"] == "draft_visible"
    assert report["validation_status"] == "warning_only"
    assert report["package_identity"]["package_id"] == "specgraph.core_repository_facade"
    assert report["inspection"]["package"]["capabilities"] == ["specgraph.repository_facade"]
    assert report["handoff_summary"]["source_handoff_artifact"] == (
        "runs/specpm_handoff_packets.json"
    )


def test_inspect_boundary_summary_exposes_viewer_contract() -> None:
    report = inspect_package(ROOT / "examples/email_tools")

    spec = report["boundary_specs"][0]
    warning_codes = {issue["code"] for issue in report["contract_warnings"]}
    assert spec["scope"]["includes"][0] == "Parse email message input."
    assert spec["effects"]["sideEffects"][0]["kind"] == "filesystem_read"
    assert spec["foreign_artifacts"] == []
    assert spec["implementation_bindings"] == []
    assert spec["provenance_confidence"] == {
        "intent": "medium",
        "boundary": "medium",
        "behavior": "low",
    }
    assert "security_sensitive_effect" in warning_codes
    assert any(
        issue.get("field") == "effects.sideEffects.0.kind" for issue in report["contract_warnings"]
    )


def test_inspect_contract_warnings_include_sensitive_capabilities(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "sensitive")
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["requires"]["capabilities"] = [
        {"id": "storage.local_filesystem", "summary": "Read local files."}
    ]
    write_yaml_file(spec_path, spec)

    report = inspect_package(package)

    assert any(
        issue["code"] == "security_sensitive_capability"
        and "storage.local_filesystem" in issue["message"]
        and issue.get("field") == "requires.capabilities"
        for issue in report["contract_warnings"]
    )


def test_inbox_lists_incomplete_bundle_with_actionable_gaps(tmp_path: Path) -> None:
    bundle = tmp_path / "incomplete.bundle"
    bundle.mkdir()
    (bundle / "handoff.json").write_text(
        json.dumps({"handoff_id": "missing_main", "handoff_status": "ready_for_review"}),
        encoding="utf-8",
    )

    report = list_inbox(tmp_path)

    assert report["bundles"][0]["package_id"] == "incomplete.bundle"
    assert report["bundles"][0]["inbox_status"] == "invalid"
    gap_codes = {gap["code"] for gap in report["bundles"][0]["gaps"]}
    assert "inbox_manifest_missing" in gap_codes
    assert "inbox_main_spec_missing" in gap_codes


def test_inbox_malformed_handoff_blocks_valid_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "broken_handoff"
    shutil.copytree(SPECGRAPH_FIXTURE_ROOT / "specgraph.core_repository_facade", bundle)
    (bundle / "handoff.json").write_text("{", encoding="utf-8")

    report = inspect_inbox_bundle(tmp_path, "broken_handoff")

    assert report["found"] is True
    assert report["inbox_status"] == "blocked"
    assert report["handoff"] is None
    assert report["handoff_summary"]["handoff_status"] == "invalid"
    assert any(gap["code"] == "handoff_invalid" for gap in report["gaps"])


def test_cli_validate_json(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["validate", str(ROOT / "examples/email_tools"), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "valid"


def test_cli_inspect_surfaces_provenance_and_contract_warnings(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["inspect", str(ROOT / "examples/email_tools")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Provenance confidence: behavior=low, boundary=medium, intent=medium" in captured.out
    assert "warning security_sensitive_effect" in captured.out


def test_cli_inspect_handles_non_mapping_compatibility(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    package = copy_email_package(tmp_path, "bad-compatibility")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["compatibility"] = ["not", "a", "mapping"]
    write_yaml_file(manifest_path, manifest)

    report = inspect_package(package)
    exit_code = main(["inspect", str(package)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert report["package"]["compatibility"] == {}
    assert "Compatibility:" not in captured.out
    assert "valid: document_conversion.email_tools" in captured.out


def test_cli_inbox_list_handles_invalid_manifest_identity(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    bundle = tmp_path / "broken.bundle"
    bundle.mkdir()
    (bundle / "specpm.yaml").write_text("apiVersion: [", encoding="utf-8")

    exit_code = main(["inbox", "list", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "broken.bundle unknown [invalid]" in captured.out


def test_manifest_rejects_malformed_capability_entries(tmp_path: Path) -> None:
    package = tmp_path / "malformed"
    shutil.copytree(ROOT / "examples/email_tools", package)
    (package / "specpm.yaml").write_text(
        """
apiVersion: specpm.dev/v0.1
kind: SpecPackage
metadata:
  id: document_conversion.email_tools
  name: Email Tools
  version: 0.1.0
  summary: Boundary specifications for email document conversion.
  license: MIT
specs:
  - path: specs/email-to-markdown.spec.yaml
index:
  provides:
    capabilities:
      - 123
""".strip(),
        encoding="utf-8",
    )

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "manifest_capability_entry_invalid" for issue in report["errors"])


def test_validator_rejects_unknown_top_level_fields(tmp_path: Path) -> None:
    package = tmp_path / "unknown"
    shutil.copytree(ROOT / "examples/email_tools", package)
    manifest = package / "specpm.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "\nnotInRfc: true\n",
        encoding="utf-8",
    )

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "unknown_top_level_field" for issue in report["errors"])


def test_validator_warns_on_missing_foreign_and_implementation_paths(tmp_path: Path) -> None:
    package = tmp_path / "advisory"
    shutil.copytree(ROOT / "examples/email_tools", package)
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8")
        + """
foreignArtifacts:
  - id: missing_openapi
    format: openapi
    path: foreign/openapi.yaml
    role: api_contract
implementationBindings:
  - id: python_email_converter
    language: python
    files:
      owned:
        - src/email_converter.py
""",
        encoding="utf-8",
    )

    report = validate_package(package)

    assert report["status"] == "warning_only"
    warning_codes = {issue["code"] for issue in report["warnings"]}
    assert "foreign_artifact_path_missing" in warning_codes
    assert "implementation_binding_path_missing" in warning_codes


def test_pack_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.specpm.tgz"
    second = tmp_path / "second.specpm.tgz"

    first_report = pack_package(ROOT / "examples/email_tools", first)
    second_report = pack_package(ROOT / "examples/email_tools", second)

    assert first_report["status"] == "packed"
    assert second_report["status"] == "packed"
    assert first_report["digest"] == second_report["digest"]
    assert first.read_bytes() == second.read_bytes()
    with tarfile.open(first, "r:gz") as archive:
        assert archive.getnames() == sorted(
            [
                "evidence/README.md",
                "specpm.yaml",
                "specs/email-to-markdown.spec.yaml",
            ]
        )


def test_index_directory_package_creates_file_backed_index(tmp_path: Path) -> None:
    index_path = tmp_path / ".specpm/index.json"

    report = index_package(ROOT / "examples/email_tools", index_path)

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert report["status"] == "indexed"
    assert report["entry"]["package_id"] == "document_conversion.email_tools"
    assert report["entry"]["provided_capabilities"] == ["document_conversion.email_to_markdown"]
    assert index_payload["schemaVersion"] == 1
    assert index_payload["capabilities"]["document_conversion.email_to_markdown"] == [
        {"package_id": "document_conversion.email_tools", "version": "0.1.0"}
    ]


def test_index_directory_package_is_idempotent(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"

    first = index_package(ROOT / "examples/email_tools", index_path)
    second = index_package(ROOT / "examples/email_tools", index_path)

    assert first["status"] == "indexed"
    assert second["status"] == "unchanged"
    assert len(json.loads(index_path.read_text(encoding="utf-8"))["packages"]) == 1


def test_index_rejects_duplicate_package_version_with_different_digest(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    changed = tmp_path / "changed"
    shutil.copytree(ROOT / "examples/email_tools", changed)
    evidence = changed / "evidence/README.md"
    evidence.write_text(evidence.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")

    first = index_package(ROOT / "examples/email_tools", index_path)
    second = index_package(changed, index_path)

    assert first["status"] == "indexed"
    assert second["status"] == "invalid"
    assert any(issue["code"] == "duplicate_package_conflict" for issue in second["errors"])


def test_index_archive_package_uses_archive_digest(tmp_path: Path) -> None:
    archive = tmp_path / "email_tools.specpm.tgz"
    index_path = tmp_path / "index.json"
    pack_report = pack_package(ROOT / "examples/email_tools", archive)

    report = index_package(archive, index_path)

    assert pack_report["status"] == "packed"
    assert report["status"] == "indexed"
    assert report["entry"]["source"]["kind"] == "archive"
    assert report["entry"]["source"]["digest"] == pack_report["digest"]


def test_cli_index_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    index_path = tmp_path / "index.json"

    exit_code = main(
        ["index", str(ROOT / "examples/email_tools"), "--index", str(index_path), "--json"]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "indexed"
    assert index_path.is_file()


def test_index_reports_read_errors_for_existing_index_path_directory(tmp_path: Path) -> None:
    index_path = tmp_path / "index-directory"
    index_path.mkdir()

    report = index_package(ROOT / "examples/email_tools", index_path)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "index_read_failed" for issue in report["errors"])


def test_search_finds_exact_capability_match(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    report = search_index("document_conversion.email_to_markdown", index_path)

    assert report["status"] == "ok"
    assert report["result_count"] == 1
    assert report["results"][0]["package_id"] == "document_conversion.email_tools"
    assert report["results"][0]["matched_capability"] == "document_conversion.email_to_markdown"


def test_search_rebuilds_missing_capability_index_from_packages(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload.pop("capabilities")
    index_path.write_text(json.dumps(index_payload), encoding="utf-8")

    report = search_index("document_conversion.email_to_markdown", index_path)

    assert report["status"] == "ok"
    assert report["result_count"] == 1
    assert report["results"][0]["package_id"] == "document_conversion.email_tools"


def test_search_unknown_capability_returns_empty_result(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    report = search_index("document_conversion.unknown", index_path)

    assert report["status"] == "ok"
    assert report["result_count"] == 0
    assert report["results"] == []


def test_search_reports_invalid_index(tmp_path: Path) -> None:
    index_path = tmp_path / "index-directory"
    index_path.mkdir()

    report = search_index("document_conversion.email_to_markdown", index_path)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "index_read_failed" for issue in report["errors"])


def test_search_finds_specgraph_fixture_capability(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(SPECGRAPH_FIXTURE_ROOT / "specgraph.core_repository_facade", index_path)

    report = search_index("specgraph.repository_facade", index_path)

    assert report["status"] == "ok"
    assert report["result_count"] == 1
    assert report["results"][0]["package_id"] == "specgraph.core_repository_facade"


def test_cli_search_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    exit_code = main(
        [
            "search",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["result_count"] == 1


def test_add_unique_capability_writes_lock_and_project_state(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    index_package(ROOT / "examples/email_tools", index_path)

    report = add_package("document_conversion.email_to_markdown", index_path, project)

    lock_payload = json.loads((project / "specpm.lock").read_text(encoding="utf-8"))
    project_index = json.loads((project / ".specpm/index.json").read_text(encoding="utf-8"))
    cache_path = project / ".specpm/packages/document_conversion.email_tools/0.1.0/package.json"
    assert report["status"] == "added"
    assert report["package"]["package_id"] == "document_conversion.email_tools"
    assert report["package"]["cache_entry"] == (
        ".specpm/packages/document_conversion.email_tools/0.1.0/package.json"
    )
    assert lock_payload["schemaVersion"] == 1
    assert lock_payload["packages"][0]["package_id"] == "document_conversion.email_tools"
    assert project_index["packages"][0]["package_id"] == "document_conversion.email_tools"
    assert cache_path.is_file()


def test_add_unique_capability_is_idempotent(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    index_package(ROOT / "examples/email_tools", index_path)

    first = add_package("document_conversion.email_to_markdown", index_path, project)
    lock_before = (project / "specpm.lock").read_text(encoding="utf-8")
    second = add_package("document_conversion.email_to_markdown", index_path, project)

    assert first["status"] == "added"
    assert second["status"] == "unchanged"
    assert (project / "specpm.lock").read_text(encoding="utf-8") == lock_before


def test_add_rejects_invalid_lock_before_project_mutation(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    project.mkdir()
    (project / "specpm.lock").write_text("{", encoding="utf-8")
    index_package(ROOT / "examples/email_tools", index_path)

    report = add_package("document_conversion.email_to_markdown", index_path, project)

    assert report["status"] == "invalid"
    assert report["resolved_by"] == "capability"
    assert any(issue["code"] == "lock_json_invalid" for issue in report["errors"])
    assert not (project / ".specpm").exists()


def test_add_rejects_lock_conflict_before_project_mutation(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    project.mkdir()
    entry = indexed_email_entry(tmp_path)
    (project / "specpm.lock").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "packages": [
                    {
                        "package_id": entry["package_id"],
                        "version": entry["version"],
                        "source": {
                            "digest": {
                                "algorithm": "sha256",
                                "value": "d" * 64,
                            }
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    index_package(ROOT / "examples/email_tools", index_path)

    report = add_package("document_conversion.email_to_markdown", index_path, project)

    assert report["status"] == "invalid"
    assert report["resolved_by"] == "capability"
    assert any(issue["code"] == "lock_package_conflict" for issue in report["errors"])
    assert not (project / ".specpm").exists()


def test_add_selects_highest_stable_version_for_same_package(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    old_entry = indexed_email_entry(tmp_path)
    new_entry = dict(old_entry)
    new_entry["version"] = "0.2.0"
    new_entry["source"] = {
        **old_entry["source"],
        "digest": {"algorithm": "sha256", "value": "b" * 64},
    }
    write_index_payload(index_path, [old_entry, new_entry])

    report = add_package("document_conversion.email_to_markdown", index_path, project)

    assert report["status"] == "added"
    assert report["package"]["version"] == "0.2.0"


def test_add_ambiguous_capability_requires_review(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    first_entry = indexed_email_entry(tmp_path)
    second_entry = dict(first_entry)
    second_entry["package_id"] = "document_conversion.alt_email_tools"
    second_entry["name"] = "Alt Email Tools"
    second_entry["source"] = {
        **first_entry["source"],
        "digest": {"algorithm": "sha256", "value": "c" * 64},
    }
    write_index_payload(index_path, [first_entry, second_entry])

    report = add_package("document_conversion.email_to_markdown", index_path, project)

    assert report["status"] == "ambiguous"
    assert report["candidate_count"] == 2
    assert not (project / "specpm.lock").exists()


def test_add_exact_package_ref_from_index(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    index_package(ROOT / "examples/email_tools", index_path)

    report = add_package("document_conversion.email_tools@0.1.0", index_path, project)

    assert report["status"] == "added"
    assert report["resolved_by"] == "package_ref"
    assert report["package"]["package_id"] == "document_conversion.email_tools"


def test_add_exact_package_ref_rejects_yanked_package(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    entry = indexed_email_entry(tmp_path)
    entry["yanked"] = True
    write_index_payload(index_path, [entry])

    report = add_package("document_conversion.email_tools@0.1.0", index_path, project)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "package_yanked" for issue in report["errors"])
    assert not (project / "specpm.lock").exists()


def test_add_package_path_without_source_index(tmp_path: Path) -> None:
    project = tmp_path / "project"

    report = add_package(str(ROOT / "examples/email_tools"), tmp_path / "missing.json", project)

    assert report["status"] == "added"
    assert report["resolved_by"] == "path"
    assert (project / ".specpm/index.json").is_file()
    assert (project / "specpm.lock").is_file()


def test_add_package_path_rejects_invalid_lock_before_local_index(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "specpm.lock").write_text("{", encoding="utf-8")

    report = add_package(str(ROOT / "examples/email_tools"), tmp_path / "missing.json", project)

    assert report["status"] == "invalid"
    assert report["resolved_by"] == "path"
    assert any(issue["code"] == "lock_json_invalid" for issue in report["errors"])
    assert not (project / ".specpm").exists()


def test_cli_add_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    index_package(ROOT / "examples/email_tools", index_path)

    exit_code = main(
        [
            "add",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--project",
            str(project),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "added"
    assert payload["package"]["package_id"] == "document_conversion.email_tools"


def test_diff_identical_package_is_unchanged() -> None:
    report = diff_packages(ROOT / "examples/email_tools", ROOT / "examples/email_tools")

    assert report["status"] == "ok"
    assert report["classification"] == "unchanged"
    assert report["has_changes"] is False


def test_diff_removed_capability_is_breaking(tmp_path: Path) -> None:
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    new_capability = "document_conversion.email_to_text"
    manifest_path = new_package / "specpm.yaml"
    spec_path = new_package / "specs/email-to-markdown.spec.yaml"
    manifest = load_yaml_file(manifest_path)
    spec = load_yaml_file(spec_path)
    manifest["index"]["provides"]["capabilities"] = [new_capability]
    spec["provides"]["capabilities"][0]["id"] = new_capability
    write_yaml_file(manifest_path, manifest)
    write_yaml_file(spec_path, spec)

    report = diff_packages(old_package, new_package)

    assert report["status"] == "ok"
    assert report["classification"] == "breaking"
    assert report["changes"]["capabilities"]["removed"] == ["document_conversion.email_to_markdown"]
    assert report["changes"]["capabilities"]["added"] == [new_capability]
    assert any(item["code"] == "capability_removed" for item in report["impact"]["breaking"])


def test_diff_added_capability_requires_review(tmp_path: Path) -> None:
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    new_capability = "document_conversion.email_to_text"
    manifest_path = new_package / "specpm.yaml"
    spec_path = new_package / "specs/email-to-markdown.spec.yaml"
    manifest = load_yaml_file(manifest_path)
    spec = load_yaml_file(spec_path)
    manifest["index"]["provides"]["capabilities"].append(new_capability)
    spec["provides"]["capabilities"].append(
        {
            "id": new_capability,
            "role": "secondary",
            "summary": "Convert email content into plain text.",
        }
    )
    write_yaml_file(manifest_path, manifest)
    write_yaml_file(spec_path, spec)

    report = diff_packages(old_package, new_package)

    assert report["status"] == "ok"
    assert report["classification"] == "review_required"
    assert report["changes"]["capabilities"]["added"] == [new_capability]
    assert any(item["code"] == "capability_added" for item in report["impact"]["review_required"])


def test_diff_added_required_capability_is_breaking(tmp_path: Path) -> None:
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    required_capability = "storage.local_filesystem"
    manifest_path = new_package / "specpm.yaml"
    spec_path = new_package / "specs/email-to-markdown.spec.yaml"
    manifest = load_yaml_file(manifest_path)
    spec = load_yaml_file(spec_path)
    manifest["index"]["requires"]["capabilities"] = [required_capability]
    spec["requires"]["capabilities"] = [{"id": required_capability, "summary": "Read local files."}]
    write_yaml_file(manifest_path, manifest)
    write_yaml_file(spec_path, spec)

    report = diff_packages(old_package, new_package)

    assert report["status"] == "ok"
    assert report["classification"] == "breaking"
    assert report["changes"]["required_capabilities"]["added"] == [required_capability]
    assert any(item["code"] == "required_capability_added" for item in report["impact"]["breaking"])


def test_diff_removed_interface_is_breaking(tmp_path: Path) -> None:
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    spec_path = new_package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["interfaces"]["inbound"] = []
    write_yaml_file(spec_path, spec)

    report = diff_packages(old_package, new_package)

    assert report["status"] == "ok"
    assert report["classification"] == "breaking"
    assert report["changes"]["interfaces"]["removed"][0]["id"] == "email_file_input"
    assert any(item["code"] == "interface_removed" for item in report["impact"]["breaking"])


def test_diff_duplicate_interface_ids_do_not_overwrite(tmp_path: Path) -> None:
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    spec_path = old_package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["interfaces"]["inbound"].append(
        {
            "id": "email_file_input",
            "kind": "file",
            "summary": "Accepts a legacy duplicate email file input.",
        }
    )
    write_yaml_file(spec_path, spec)

    report = diff_packages(old_package, new_package)

    removed = report["changes"]["interfaces"]["removed"]
    assert report["status"] == "ok"
    assert report["classification"] == "breaking"
    assert len(removed) == 1
    assert removed[0]["id"] == "email_file_input"
    assert removed[0]["summary"] == "Accepts a legacy duplicate email file input."
    assert removed[0]["occurrence"] == 1
    assert any(item["code"] == "interface_removed" for item in report["impact"]["breaking"])


def test_diff_changed_must_constraint_is_breaking(tmp_path: Path) -> None:
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    spec_path = new_package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["constraints"][0]["statement"] = (
        "Converting a local email file may require configured network access."
    )
    write_yaml_file(spec_path, spec)

    report = diff_packages(old_package, new_package)

    assert report["status"] == "ok"
    assert report["classification"] == "breaking"
    assert report["changes"]["must_constraints"]["changed"][0]["old"]["id"] == (
        "no_network_access_required"
    )
    assert any(item["code"] == "must_constraint_changed" for item in report["impact"]["breaking"])


def test_diff_duplicate_must_constraint_ids_do_not_overwrite(tmp_path: Path) -> None:
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    old_spec_path = old_package / "specs/email-to-markdown.spec.yaml"
    new_spec_path = new_package / "specs/email-to-markdown.spec.yaml"
    old_spec = load_yaml_file(old_spec_path)
    new_spec = load_yaml_file(new_spec_path)
    old_spec["constraints"].append(
        {
            "id": "no_network_access_required",
            "level": "MUST",
            "statement": "Conversion must preserve visible email body text.",
        }
    )
    new_spec["constraints"].append(
        {
            "id": "no_network_access_required",
            "level": "MUST",
            "statement": "Conversion must preserve visible email body text and headers.",
        }
    )
    write_yaml_file(old_spec_path, old_spec)
    write_yaml_file(new_spec_path, new_spec)

    report = diff_packages(old_package, new_package)

    changed = report["changes"]["must_constraints"]["changed"]
    assert report["status"] == "ok"
    assert report["classification"] == "breaking"
    assert len(changed) == 1
    assert changed[0]["old"]["id"] == "no_network_access_required"
    assert changed[0]["old"]["occurrence"] == 1
    assert changed[0]["new"]["occurrence"] == 1
    assert changed[0]["old"]["statement"] == "Conversion must preserve visible email body text."
    assert changed[0]["new"]["statement"] == (
        "Conversion must preserve visible email body text and headers."
    )
    assert any(item["code"] == "must_constraint_changed" for item in report["impact"]["breaking"])


def test_cli_diff_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    old_package = copy_email_package(tmp_path, "old")
    new_package = copy_email_package(tmp_path, "new")
    manifest_path = new_package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["metadata"]["summary"] = "Updated summary."
    write_yaml_file(manifest_path, manifest)

    exit_code = main(["diff", str(old_package), str(new_package), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["classification"] == "review_required"
    assert payload["changes"]["package_metadata"]["changed"][0]["field"] == "summary"


def test_cli_pack_rejects_invalid_packages(tmp_path: Path) -> None:
    package = tmp_path / "invalid"
    package.mkdir()
    (package / "specpm.yaml").write_text("apiVersion: [", encoding="utf-8")
    archive = tmp_path / "invalid.specpm.tgz"

    exit_code = main(["pack", str(package), "-o", str(archive), "--json"])

    assert exit_code == 1
    assert not archive.exists()


def test_cli_pack_failure_prints_validation_details(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    package = tmp_path / "invalid"
    package.mkdir()
    (package / "specpm.yaml").write_text("apiVersion: [", encoding="utf-8")

    exit_code = main(["pack", str(package), "-o", str(tmp_path / "invalid.specpm.tgz")])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error validation_failed" in captured.err
    assert "error yaml_parse_error" in captured.err


def test_pack_rejects_output_path_overlapping_source_file(tmp_path: Path) -> None:
    package = tmp_path / "overlap"
    shutil.copytree(ROOT / "examples/email_tools", package)
    manifest = package / "specpm.yaml"
    original_manifest = manifest.read_text(encoding="utf-8")

    report = pack_package(package, manifest)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "pack_output_overlaps_source" for issue in report["errors"])
    assert manifest.read_text(encoding="utf-8") == original_manifest


def test_pack_write_failure_removes_partial_archive(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    archive = tmp_path / "partial.specpm.tgz"

    def fail_after_partial_write(root: Path, files: list[str], archive_path: Path) -> None:
        archive_path.write_bytes(b"partial")
        raise OSError("disk full")

    monkeypatch.setattr("specpm.core.write_deterministic_tar_gz", fail_after_partial_write)

    report = pack_package(ROOT / "examples/email_tools", archive)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "pack_write_failed" for issue in report["errors"])
    assert not archive.exists()


def test_pack_rejects_symlinks(tmp_path: Path) -> None:
    package = tmp_path / "symlink"
    shutil.copytree(ROOT / "examples/email_tools", package)
    (package / "evidence/target.md").write_text("target", encoding="utf-8")
    (package / "evidence/README.md").unlink()
    (package / "evidence/README.md").symlink_to("target.md")

    report = pack_package(package, tmp_path / "symlink.specpm.tgz")

    assert report["status"] == "invalid"
    assert any(issue["code"] == "pack_symlink_unsupported" for issue in report["errors"])


def test_restricted_yaml_rejects_anchors(tmp_path: Path) -> None:
    package = tmp_path / "bad"
    package.mkdir()
    (package / "specpm.yaml").write_text(
        """
apiVersion: specpm.dev/v0.1
kind: SpecPackage
metadata: &metadata
  id: bad.package
  name: Bad
  version: 0.1.0
  summary: Bad package
  license: MIT
specs: []
index:
  provides:
    capabilities:
      - bad.package
""".strip(),
        encoding="utf-8",
    )

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "yaml_anchor_unsupported" for issue in report["errors"])
