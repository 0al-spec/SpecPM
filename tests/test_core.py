from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path

from specpm.cli import main
from specpm.core import list_inbox, pack_package, validate_package

ROOT = Path(__file__).resolve().parents[1]
SPECGRAPH_FIXTURE_ROOT = ROOT / "tests/fixtures/specgraph_exports"


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


def test_inbox_lists_specgraph_export() -> None:
    report = list_inbox(SPECGRAPH_FIXTURE_ROOT)

    assert report["bundles"][0]["package_id"] == "specgraph.core_repository_facade"
    assert report["bundles"][0]["inbox_status"] == "draft_visible"


def test_cli_validate_json(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["validate", str(ROOT / "examples/email_tools"), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "valid"


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


def test_cli_pack_rejects_invalid_packages(tmp_path: Path) -> None:
    package = tmp_path / "invalid"
    package.mkdir()
    (package / "specpm.yaml").write_text("apiVersion: [", encoding="utf-8")
    archive = tmp_path / "invalid.specpm.tgz"

    exit_code = main(["pack", str(package), "-o", str(archive), "--json"])

    assert exit_code == 1
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
