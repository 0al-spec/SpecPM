from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from specpm import core as core_module
from specpm import index_submission as index_submission_module
from specpm import public_index as public_index_module
from specpm.cli import build_parser, main
from specpm.core import (
    add_package,
    diff_packages,
    get_remote_package,
    get_remote_package_index,
    get_remote_package_version,
    get_remote_registry_status,
    index_package,
    inspect_inbox_bundle,
    inspect_package,
    list_inbox,
    pack_package,
    search_index,
    search_remote_registry,
    unyank_index_package,
    validate_package,
    validate_remote_registry_payload,
    yank_index_package,
)
from specpm.index_submission import (
    parse_submission_issue_body,
    render_submission_report_markdown,
    validate_submission_body,
)
from specpm.public_index import (
    generate_public_index,
    generate_public_index_from_inputs,
    load_public_index_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
SPECGRAPH_FIXTURE_ROOT = ROOT / "tests/fixtures/specgraph_exports"
GOLDEN_FIXTURE_ROOT = ROOT / "tests/fixtures/golden"
CONFORMANCE_SUITE = ROOT / "tests/fixtures/conformance/specpm-conformance-v0.json"
ADD_SPECPACKAGES_ISSUE_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/add-specpackages.yml"
REMOVE_SPECPACKAGES_ISSUE_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/remove-specpackages.yml"
CLAIM_NAMESPACE_ISSUE_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/claim-namespace.yml"
NAMESPACE_CLAIM_POLICY = ROOT / "specs/NAMESPACE_CLAIM_POLICY.md"
PACKAGE_SUBMISSION_WORKFLOW = ROOT / ".github/workflows/package-submission-check.yml"
NAMESPACE_CLAIM_TRIAGE_WORKFLOW = ROOT / ".github/workflows/namespace-claim-triage.yml"
DOCS_WORKFLOW = ROOT / ".github/workflows/docs.yml"
COMPOSE_FILE = ROOT / "compose.yaml"
PUBLIC_INDEX_ACCEPTED_MANIFEST = ROOT / "public-index/accepted-packages.yml"
PULL_REQUEST_TEMPLATE = ROOT / ".github/PULL_REQUEST_TEMPLATE.md"
CONFORMANCE_CASE_KINDS = {
    "registry_lifecycle",
    "remote_registry_payload",
    "validate_package",
}
REMOTE_REGISTRY_API_VERSION = "specpm.registry/v0"
REMOTE_REGISTRY_PAYLOAD_KINDS = {
    "RemoteCapabilitySearch",
    "RemotePackage",
    "RemotePackageIndex",
    "RemotePackageVersion",
    "RemoteRegistryStatus",
    "RemoteRegistryError",
}
REMOTE_REGISTRY_STATUSES = {"invalid", "not_found", "ok"}


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


def issue_codes(issues: list[dict[str, Any]]) -> set[str]:
    return {issue["code"] for issue in issues}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_conformance_suite() -> dict[str, Any]:
    suite = json.loads(CONFORMANCE_SUITE.read_text(encoding="utf-8"))
    assert suite["schemaVersion"] == 1
    case_ids = [case["id"] for case in suite["cases"]]
    assert len(case_ids) == len(set(case_ids))
    case_kinds = {case["kind"] for case in suite["cases"]}
    assert case_kinds <= CONFORMANCE_CASE_KINDS
    return suite


def load_remote_registry_fixture(name: str) -> dict[str, Any]:
    loaded = json.loads(
        (ROOT / "tests/fixtures/conformance/remote_registry" / name).read_text(encoding="utf-8")
    )
    assert isinstance(loaded, dict)
    return loaded


class FakeRemoteResponse:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    def __enter__(self) -> FakeRemoteResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def assert_sha256_digest(value: dict[str, Any]) -> None:
    assert value["algorithm"] == "sha256"
    assert isinstance(value["value"], str)
    assert len(value["value"]) == 64
    int(value["value"], 16)


def assert_remote_registry_source(value: dict[str, Any]) -> None:
    assert value["kind"] == "archive"
    assert value["format"] == "specpm-tar-gzip-v0"
    assert_sha256_digest(value["digest"])
    assert isinstance(value["size"], int)
    assert value["size"] > 0
    assert isinstance(value["url"], str)
    assert value["url"].startswith("https://registry.example.invalid/")


def assert_remote_registry_payload_shape(payload: dict[str, Any]) -> None:
    assert payload["apiVersion"] == REMOTE_REGISTRY_API_VERSION
    assert payload["schemaVersion"] == 1
    assert payload["kind"] in REMOTE_REGISTRY_PAYLOAD_KINDS
    assert payload["status"] in REMOTE_REGISTRY_STATUSES

    if payload["kind"] == "RemotePackage":
        package = payload["package"]
        assert isinstance(package["package_id"], str)
        assert isinstance(package["name"], str)
        assert isinstance(package["capabilities"], list)
        assert isinstance(package["versions"], list)
        for version in package["versions"]:
            assert isinstance(version["version"], str)
            assert isinstance(version["yanked"], bool)
            assert isinstance(version["deprecated"], bool)
        return

    if payload["kind"] == "RemotePackageIndex":
        assert isinstance(payload["package_count"], int)
        assert isinstance(payload["version_count"], int)
        assert isinstance(payload["packages"], list)
        assert payload["package_count"] == len(payload["packages"])
        assert payload["version_count"] == sum(
            len(package["versions"]) for package in payload["packages"]
        )
        for package in payload["packages"]:
            assert isinstance(package["package_id"], str)
            assert isinstance(package["name"], str)
            assert isinstance(package["capabilities"], list)
            assert isinstance(package["versions"], list)
        return

    if payload["kind"] == "RemotePackageVersion":
        package = payload["package"]
        assert isinstance(package["package_id"], str)
        assert isinstance(package["name"], str)
        assert isinstance(package["version"], str)
        assert isinstance(package["provided_capabilities"], list)
        assert isinstance(package["required_capabilities"], list)
        assert isinstance(package["state"]["yanked"], bool)
        assert isinstance(package["state"]["deprecated"], bool)
        assert_remote_registry_source(package["source"])
        return

    if payload["kind"] == "RemoteCapabilitySearch":
        assert payload["query"]["match"] == "exact"
        assert isinstance(payload["result_count"], int)
        assert payload["result_count"] == len(payload["results"])
        for result in payload["results"]:
            assert isinstance(result["package_id"], str)
            assert isinstance(result["version"], str)
            assert isinstance(result["matched_capability"], str)
            assert isinstance(result["provided_capabilities"], list)
            assert isinstance(result["required_capabilities"], list)
            assert isinstance(result["yanked"], bool)
            assert isinstance(result["deprecated"], bool)
            assert_remote_registry_source(result["source"])
        return

    if payload["kind"] == "RemoteRegistryStatus":
        registry = payload["registry"]
        assert isinstance(registry["profile"], str)
        assert registry["profile"]
        assert isinstance(registry["api_version"], str)
        assert isinstance(registry["read_only"], bool)
        assert isinstance(registry["authority"], str)
        assert isinstance(registry["package_count"], int)
        assert isinstance(registry["version_count"], int)
        assert isinstance(registry["capability_count"], int)
        return

    assert payload["kind"] == "RemoteRegistryError"
    assert payload["status"] in {"invalid", "not_found"}
    assert isinstance(payload["error"]["code"], str)
    assert isinstance(payload["error"]["message"], str)


def cli_command_names() -> set[str]:
    parser = build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("SpecPM CLI parser does not expose subcommands")


def copy_email_package(tmp_path: Path, name: str) -> Path:
    package = tmp_path / name
    shutil.copytree(ROOT / "examples/email_tools", package)
    return package


def update_email_package(
    package: Path,
    *,
    package_id: str | None = None,
    package_name: str | None = None,
    version: str | None = None,
    capability_id: str | None = None,
) -> None:
    manifest_path = package / "specpm.yaml"
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    manifest = load_yaml_file(manifest_path)
    spec = load_yaml_file(spec_path)

    if package_id is not None:
        manifest["metadata"]["id"] = package_id
    if package_name is not None:
        manifest["metadata"]["name"] = package_name
    if version is not None:
        manifest["metadata"]["version"] = version
        spec["metadata"]["version"] = version
    if capability_id is not None:
        manifest["index"]["provides"]["capabilities"] = [capability_id]
        spec["metadata"]["id"] = capability_id
        spec["provides"]["capabilities"][0]["id"] = capability_id
        spec["evidence"][0]["supports"] = [f"provides.capabilities.{capability_id}"]

    write_yaml_file(manifest_path, manifest)
    write_yaml_file(spec_path, spec)


def run_cli_json(args: list[str], capsys, expected_exit: int = 0) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    exit_code = main(args)
    captured = capsys.readouterr()
    assert exit_code == expected_exit, captured.err
    loaded = json.loads(captured.out)
    assert isinstance(loaded, dict)
    return loaded


def assert_golden_json(
    fixture_name: str, payload: dict[str, Any], tmp_path: Path | None = None
) -> None:
    expected = json.loads((GOLDEN_FIXTURE_ROOT / fixture_name).read_text(encoding="utf-8"))
    assert_json_contract_contains(normalize_json_contract(payload, tmp_path), expected)


def assert_json_contract_contains(actual: Any, expected: Any, path: str = "$") -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected object, got {type(actual).__name__}"
        missing = sorted(set(expected) - set(actual))
        assert not missing, f"{path}: missing keys {missing}"
        for key, expected_value in expected.items():
            assert_json_contract_contains(actual[key], expected_value, f"{path}.{key}")
        return
    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        assert len(actual) == len(expected), (
            f"{path}: expected {len(expected)} items, got {len(actual)}"
        )
        for index, expected_value in enumerate(expected):
            assert_json_contract_contains(actual[index], expected_value, f"{path}[{index}]")
        return
    assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"


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


def test_json_contract_subset_allows_additive_fields() -> None:
    actual = {
        "status": "ok",
        "new_top_level_field": True,
        "nested": {"stable": 1, "new_nested_field": "kept"},
        "items": [{"id": "first", "new_item_field": "kept"}],
    }
    expected = {"status": "ok", "nested": {"stable": 1}, "items": [{"id": "first"}]}

    assert_json_contract_contains(actual, expected)


def test_add_specpackages_issue_template_matches_public_index_contract() -> None:
    loaded = load_yaml_file(ADD_SPECPACKAGES_ISSUE_TEMPLATE)
    assert loaded["name"] == "Add SpecPackage(s)"
    assert "package-submission" in loaded["labels"]

    body = loaded["body"]
    assert isinstance(body, list)
    fields = {item.get("id"): item for item in body if isinstance(item, dict) and "id" in item}
    assert fields["package_urls"]["type"] == "textarea"
    assert fields["package_urls"]["validations"]["required"] is True
    assert fields["package_path"]["validations"]["required"] is False
    assert fields["acknowledgements"]["type"] == "checkboxes"

    acknowledgements = fields["acknowledgements"]["attributes"]["options"]
    assert len(acknowledgements) >= 4
    assert all(option["required"] is True for option in acknowledgements)

    template_text = ADD_SPECPACKAGES_ISSUE_TEMPLATE.read_text(encoding="utf-8").lower()
    assert "specpm publish" in template_text
    assert "does not define" in template_text
    for forbidden in ("password", "token", "private key", "signing key", "secret"):
        assert forbidden not in template_text


def test_remove_specpackages_issue_template_matches_public_index_boundary() -> None:
    loaded = load_yaml_file(REMOVE_SPECPACKAGES_ISSUE_TEMPLATE)
    assert loaded["name"] == "Remove SpecPackage(s)"
    assert "package-removal" in loaded["labels"]

    body = loaded["body"]
    assert isinstance(body, list)
    fields = {item.get("id"): item for item in body if isinstance(item, dict) and "id" in item}
    assert fields["package_refs"]["type"] == "textarea"
    assert fields["package_refs"]["validations"]["required"] is True
    assert fields["removal_scope"]["type"] == "dropdown"
    assert fields["removal_scope"]["validations"]["required"] is True
    assert fields["reason"]["type"] == "dropdown"
    assert fields["rationale"]["validations"]["required"] is True
    assert fields["requester_relationship"]["validations"]["required"] is True
    assert fields["acknowledgements"]["type"] == "checkboxes"

    acknowledgements = fields["acknowledgements"]["attributes"]["options"]
    assert len(acknowledgements) >= 4
    assert all(option["required"] is True for option in acknowledgements)

    template_text = REMOVE_SPECPACKAGES_ISSUE_TEMPLATE.read_text(encoding="utf-8").lower()
    assert "does not automatically mutate the registry" in template_text
    assert "public-index/accepted-packages.yml" in template_text
    assert "specpm publish" in template_text
    assert "remote mutation api" in template_text
    assert "package content execution" in template_text


def test_claim_namespace_issue_template_matches_public_index_boundary() -> None:
    loaded = load_yaml_file(CLAIM_NAMESPACE_ISSUE_TEMPLATE)
    assert loaded["name"] == "Claim Namespace"
    assert "namespace-claim" in loaded["labels"]

    body = loaded["body"]
    assert isinstance(body, list)
    fields = {item.get("id"): item for item in body if isinstance(item, dict) and "id" in item}
    assert fields["namespace_id"]["type"] == "input"
    assert fields["namespace_id"]["validations"]["required"] is True
    assert fields["claim_scope"]["type"] == "dropdown"
    assert fields["claim_scope"]["validations"]["required"] is True
    assert fields["claimant"]["validations"]["required"] is True
    assert fields["evidence_urls"]["type"] == "textarea"
    assert fields["evidence_urls"]["validations"]["required"] is True
    assert fields["intended_use"]["validations"]["required"] is True
    assert fields["public_contact"]["validations"]["required"] is True
    assert fields["acknowledgements"]["type"] == "checkboxes"

    acknowledgements = fields["acknowledgements"]["attributes"]["options"]
    assert len(acknowledgements) >= 5
    assert all(option["required"] is True for option in acknowledgements)

    template_text = CLAIM_NAMESPACE_ISSUE_TEMPLATE.read_text(encoding="utf-8").lower()
    assert "does not automatically grant exclusive namespace ownership" in template_text
    assert "reviewed pull requests" in template_text
    assert "specpm publish" in template_text
    assert "remote mutation api" in template_text
    assert "enterprise namespace governance" in template_text
    assert "package content execution" in template_text


def test_namespace_claim_policy_documents_review_boundary() -> None:
    policy_text = NAMESPACE_CLAIM_POLICY.read_text(encoding="utf-8").lower()

    for status_label in (
        "namespace:needs-info",
        "namespace:under-review",
        "namespace:accepted",
        "namespace:rejected",
        "namespace:contested",
        "namespace:superseded",
    ):
        assert status_label in policy_text

    assert "does not automatically grant exclusive namespace ownership" in policy_text
    assert "not a machine-enforced ownership contract" in policy_text
    assert ".github/workflows/namespace-claim-triage.yml" in policy_text
    assert "public-index/accepted-packages.yml" in policy_text
    assert "reviewed pull request" in policy_text
    assert "specpm publish" in policy_text
    assert "remote mutation api" in policy_text
    assert "authentication" in policy_text
    assert "enterprise namespace governance" in policy_text
    assert "package content execution" in policy_text


def test_pull_request_template_requires_motivation_and_goals() -> None:
    template = PULL_REQUEST_TEMPLATE.read_text(encoding="utf-8")

    expected_sections = [
        "## Motivation",
        "## Goals",
        "## Changes",
        "## Validation",
        "## Boundaries and Non-Goals",
        "## Notes",
    ]
    for section in expected_sections:
        assert section in template

    assert "Do not claim checks that were not run." in template
    assert "security boundaries" in template


def test_package_submission_workflow_runs_only_for_submission_label() -> None:
    loaded = load_yaml_file(PACKAGE_SUBMISSION_WORKFLOW)

    assert loaded["name"] == "Package Submission Check"
    assert loaded["permissions"] == {"contents": "read", "issues": "write"}
    assert loaded["on"]["issues"]["types"] == ["opened", "edited", "reopened", "labeled"]

    job = loaded["jobs"]["validate-submission"]
    assert "package-submission" in job["if"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    assert "Validate submitted packages" in steps
    assert "Comment validation report" in steps
    assert "Fail invalid submissions" in steps
    validate_run = steps["Validate submitted packages"]["run"]
    assert "scripts/validate_index_submission.py" in validate_run
    assert "--issue-body-file submission-issue.md" in validate_run
    assert "--markdown-output submission-report.md" in validate_run
    comment_script = steps["Comment validation report"]["with"]["script"]
    assert "package-submission-validation-report" in comment_script
    assert "listComments" in comment_script
    assert "updateComment" in comment_script
    assert "createComment" in comment_script


def test_namespace_claim_triage_workflow_applies_review_labels_only() -> None:
    loaded = load_yaml_file(NAMESPACE_CLAIM_TRIAGE_WORKFLOW)

    assert loaded["name"] == "Namespace Claim Triage"
    assert loaded["permissions"] == {"contents": "read", "issues": "write"}
    assert loaded["on"]["issues"]["types"] == ["opened", "edited", "reopened", "labeled"]

    job = loaded["jobs"]["triage-namespace-claim"]
    assert "namespace-claim" in job["if"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    assert "Apply namespace review triage" in steps

    script = steps["Apply namespace review triage"]["with"]["script"]
    for status_label in (
        "namespace:needs-info",
        "namespace:under-review",
        "namespace:accepted",
        "namespace:rejected",
        "namespace:contested",
        "namespace:superseded",
    ):
        assert status_label in script
    assert "specs/NAMESPACE_CLAIM_POLICY.md" in script
    assert "namespace-claim-triage" in script
    assert "addLabels" in script
    assert "createLabel" in script
    assert "listComments" in script
    assert "updateComment" in script
    assert "createComment" in script
    assert "does not grant namespace ownership" in script
    assert "public-index/accepted-packages.yml" in script
    for forbidden in ("specpm publish", "public-index generate", "validate_index_submission.py"):
        assert forbidden not in script


def test_docs_workflow_publishes_public_index_metadata_with_docc() -> None:
    loaded = load_yaml_file(DOCS_WORKFLOW)

    trigger = loaded.get("on") or loaded.get(True)
    paths = set(trigger["push"]["paths"])
    assert {
        "src/specpm/**",
        "examples/**",
        "public-index/**",
        "pyproject.toml",
        ".github/workflows/docs.yml",
    } <= paths

    build = loaded["jobs"]["build"]
    steps = build["steps"]
    step_names = [step["name"] for step in steps if "name" in step]
    assert step_names.index("Build Documentation") < step_names.index(
        "Generate public index metadata"
    )
    assert step_names.index("Generate public index metadata") < step_names.index(
        "Add .nojekyll and index.html redirect"
    )

    steps_by_name = {step["name"]: step for step in steps if "name" in step}
    assert steps_by_name["Set up Python"]["uses"] == "actions/setup-python@v5"
    assert steps_by_name["Install SpecPM"]["run"] == 'python -m pip install -e ".[dev]"'

    generate = steps_by_name["Generate public index metadata"]
    assert generate["env"]["SPECPM_PUBLIC_INDEX_REGISTRY_URL"] == (
        "https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}"
    )
    assert "python -m specpm.cli public-index generate" in generate["run"]
    assert "--manifest public-index/accepted-packages.yml" in generate["run"]
    assert "--output ./.docc-build" in generate["run"]
    assert '--registry "$SPECPM_PUBLIC_INDEX_REGISTRY_URL"' in generate["run"]

    upload = steps_by_name["Upload artifact"]
    assert upload["with"]["path"] == "./.docc-build"


def test_public_index_compose_service_exposes_local_registry() -> None:
    loaded = load_yaml_file(COMPOSE_FILE)
    service = loaded["services"]["public-index"]

    assert service["image"] == "specpm:dev"
    assert "${SPECPM_PUBLIC_INDEX_PORT:-8081}:8081" in service["ports"]
    assert service["entrypoint"] == ["python", "scripts/serve_public_index.py"]
    assert service["environment"]["SPECPM_PUBLIC_INDEX_PORT"] == (
        "${SPECPM_PUBLIC_INDEX_PORT:-8081}"
    )
    assert service["environment"]["SPECPM_PUBLIC_INDEX_MANIFEST"] == (
        "${SPECPM_PUBLIC_INDEX_MANIFEST:-public-index/accepted-packages.yml}"
    )


def sample_submission_issue_body(
    urls: str = "https://github.com/example/email-tools.git",
    package_path: str = ".",
) -> str:
    return f"""
### New SpecPackage repositories

{urls}

### Package path

{package_path}

### Notes

Optional maintainer context.

### Submission acknowledgements

- [x] The repositories are public and reviewable.
- [x] The submitted packages contain `specpm.yaml` and referenced `specs/*.spec.yaml` files.
- [x] The package content is data and does not require execution during validation.
- [x] The package content complies with the index policy and code of conduct.
""".strip()


def test_submission_issue_body_parser_extracts_urls_and_package_path() -> None:
    issue = parse_submission_issue_body(
        sample_submission_issue_body(
            urls=(
                "https://github.com/example/email-tools.git\n"
                "https://github.com/example/specgraph-bridge.git"
            ),
            package_path="packages/email-tools",
        )
    )

    assert issue.errors == []
    assert issue.package_urls == [
        "https://github.com/example/email-tools.git",
        "https://github.com/example/specgraph-bridge.git",
    ]
    assert issue.package_path == "packages/email-tools"


def test_submission_issue_body_treats_no_response_package_path_as_root() -> None:
    issue = parse_submission_issue_body(sample_submission_issue_body(package_path="_No response_"))

    assert issue.errors == []
    assert issue.package_path == "."


def test_submission_issue_body_rejects_insecure_url_and_path_escape() -> None:
    issue = parse_submission_issue_body(
        sample_submission_issue_body(
            urls="http://github.com/example/email-tools.git",
            package_path="../outside",
        )
    )

    assert {error["code"] for error in issue.errors} == {
        "package_path_escape",
        "repository_url_invalid",
    }


def test_submission_issue_body_rejects_empty_path_and_query_without_secret_echo() -> None:
    issue = parse_submission_issue_body(
        sample_submission_issue_body(
            urls=(
                "https://github.com\nhttps://github.com/example/email-tools.git?token=secret-value"
            )
        )
    )

    assert {error["code"] for error in issue.errors} == {
        "repository_url_path_invalid",
        "repository_url_query",
    }
    assert all("secret-value" not in error["message"] for error in issue.errors)


def test_clone_repository_limits_download_behavior(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        if "rev-parse" in command:
            return subprocess.CompletedProcess(command, 0, stdout=f"{'a' * 40}\n", stderr="")
        if "branch" in command:
            return subprocess.CompletedProcess(command, 0, stdout="main\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(index_submission_module.subprocess, "run", fake_run)

    result = index_submission_module.clone_repository(
        "https://github.com/example/email-tools.git",
        tmp_path / "checkout",
    )

    assert result == {"status": "cloned", "ref": "main", "revision": "a" * 40, "errors": []}
    command, kwargs = calls[0]
    assert "--filter" in command
    assert command[command.index("--filter") + 1] == "blob:none"
    assert "--no-recurse-submodules" in command
    assert "--single-branch" in command
    assert kwargs["env"]["GIT_LFS_SKIP_SMUDGE"] == "1"
    assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"


def test_clone_repository_does_not_default_unknown_ref_to_head(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "rev-parse" in command:
            return subprocess.CompletedProcess(command, 0, stdout=f"{'a' * 40}\n", stderr="")
        if "branch" in command:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(index_submission_module.subprocess, "run", fake_run)

    result = index_submission_module.clone_repository(
        "https://github.com/example/email-tools.git",
        tmp_path / "checkout",
    )

    assert result["status"] == "cloned"
    assert result["ref"] is None
    assert result["revision"] == "a" * 40


def test_submission_validation_uses_specpm_validate_without_package_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_clone_repository(url: str, checkout: Path) -> dict[str, Any]:
        shutil.copytree(ROOT / "examples/email_tools", checkout)
        return {"status": "cloned", "ref": "main", "revision": "a" * 40, "errors": []}

    monkeypatch.setattr(index_submission_module, "clone_repository", fake_clone_repository)

    report = validate_submission_body(sample_submission_issue_body(), clone_root=tmp_path)

    assert report["status"] == "valid"
    assert report["repository_count"] == 1
    assert report["repositories"][0]["status"] == "valid"
    assert report["repositories"][0]["validation_status"] == "valid"
    assert report["repositories"][0]["package_identity"]["package_id"] == (
        "document_conversion.email_tools"
    )
    assert report["repositories"][0]["source"] == {
        "repository": "https://github.com/example/email-tools.git",
        "ref": "main",
        "revision": "a" * 40,
        "path": ".",
    }


def test_submission_cli_uses_temporary_clone_root_by_default(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    issue_body = tmp_path / "issue.md"
    issue_body.write_text(sample_submission_issue_body(), encoding="utf-8")
    clone_roots: list[Path | None] = []

    def fake_validate_submission_body(body: str, *, clone_root: Path | None) -> dict[str, Any]:
        clone_roots.append(clone_root)
        return {
            "schemaVersion": 1,
            "status": "valid",
            "package_path": ".",
            "repository_count": 0,
            "repositories": [],
            "errors": [],
        }

    monkeypatch.setattr(
        index_submission_module,
        "validate_submission_body",
        fake_validate_submission_body,
    )

    exit_code = index_submission_module.main(["--issue-body-file", str(issue_body)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["status"] == "valid"
    assert clone_roots == [None]


def test_submission_report_markdown_is_reviewable() -> None:
    report = {
        "status": "invalid",
        "package_path": ".",
        "repository_count": 0,
        "repositories": [],
        "errors": [
            {
                "severity": "error",
                "code": "package_urls_missing",
                "message": "At least one package URL is required.",
            }
        ],
    }

    markdown = render_submission_report_markdown(report)

    assert "SpecPM Index Submission Check" in markdown
    assert "package_urls_missing" in markdown
    assert "does not execute package content" in markdown


def test_submission_report_markdown_includes_accepted_manifest_candidate() -> None:
    report = {
        "status": "valid",
        "package_path": ".",
        "repository_count": 1,
        "repositories": [
            {
                "url": "https://github.com/example/email-tools.git",
                "status": "valid",
                "stage": "validate",
                "package_identity": {
                    "package_id": "document_conversion.email_tools",
                    "version": "0.1.0",
                },
                "source": {
                    "repository": "https://github.com/example/email-tools.git",
                    "ref": "main",
                    "revision": "a" * 40,
                    "path": ".",
                },
                "errors": [],
            }
        ],
        "errors": [],
    }

    markdown = render_submission_report_markdown(report)

    assert "Accepted manifest candidate" in markdown
    assert "repository: https://github.com/example/email-tools.git" in markdown
    assert f"revision: {'a' * 40}" in markdown


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


def test_repository_root_is_self_describing_specpackage() -> None:
    report = validate_package(ROOT)
    assert report["status"] == "valid"
    assert report["package_identity"] == {
        "package_id": "specpm.core",
        "name": "SpecPM",
        "version": "0.1.0",
    }
    assert report["errors"] == []
    assert report["warnings"] == []

    inspection = inspect_package(ROOT)
    capabilities = set(inspection["package"]["capabilities"])
    assert {
        "specpm.cli.public_surface",
        "specpm.public_api.core_functions",
        "specpm.package.validate",
        "specpm.documentation.docc_site",
    } <= capabilities

    boundary_spec = inspection["boundary_specs"][0]
    inbound_interfaces = {item["id"]: item for item in boundary_spec["interfaces"]["inbound"]}
    expected_cli_interface_ids = {f"cli_{command}" for command in cli_command_names()}
    documented_cli_interface_ids = {
        interface_id for interface_id in inbound_interfaces if interface_id.startswith("cli_")
    }
    assert documented_cli_interface_ids == expected_cli_interface_ids
    assert "python_core_api" in inbound_interfaces
    assert set(inbound_interfaces["python_core_api"]["functions"]) == {
        *core_module.__all__,
    }


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


def test_conformance_validate_cases() -> None:
    suite = load_conformance_suite()

    validate_cases = [case for case in suite["cases"] if case["kind"] == "validate_package"]
    assert validate_cases
    for case in validate_cases:
        report = validate_package(ROOT / case["package"])
        expected = case["expected"]
        assert report["status"] == expected["status"], case["id"]
        if "capabilities" in expected:
            assert report["capabilities"] == expected["capabilities"], case["id"]
        assert issue_codes(report["errors"]) == set(expected.get("error_codes", [])), case["id"]
        assert issue_codes(report["warnings"]) == set(expected.get("warning_codes", [])), case["id"]


def test_conformance_registry_lifecycle_cases(tmp_path: Path) -> None:
    suite = load_conformance_suite()
    lifecycle_cases = [case for case in suite["cases"] if case["kind"] == "registry_lifecycle"]
    assert lifecycle_cases

    for case in lifecycle_cases:
        expected = case["expected"]
        index_path = tmp_path / f"{case['id']}.index.json"
        project = tmp_path / case["id"]

        indexed = index_package(ROOT / case["package"], index_path)
        yanked = yank_index_package(case["package_ref"], index_path, case["yank_reason"])
        search_yanked = search_index(case["capability"], index_path)
        add_yanked = add_package(case["package_ref"], index_path, project)
        unyanked = unyank_index_package(case["package_ref"], index_path)
        add_unyanked = add_package(case["capability"], index_path, project)

        assert indexed["status"] == expected["index_status"], case["id"]
        assert yanked["status"] == expected["yank_status"], case["id"]
        assert search_yanked["results"][0]["yanked"] is expected["search_yanked"], case["id"]
        assert add_yanked["status"] == expected["add_yanked_status"], case["id"]
        assert issue_codes(add_yanked["errors"]) == set(expected["add_yanked_error_codes"])
        assert unyanked["status"] == expected["unyank_status"], case["id"]
        assert add_unyanked["status"] == expected["add_unyanked_status"], case["id"]


def test_conformance_remote_registry_payload_cases() -> None:
    suite = load_conformance_suite()
    remote_cases = [case for case in suite["cases"] if case["kind"] == "remote_registry_payload"]
    assert remote_cases

    fixture_root = (ROOT / "tests/fixtures/conformance/remote_registry").resolve()
    for case in remote_cases:
        payload_path = (ROOT / case["payload"]).resolve()
        assert payload_path.is_relative_to(fixture_root), case["id"]
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict), case["id"]
        assert_remote_registry_payload_shape(payload)

        expected = case["expected"]
        assert payload["kind"] == expected["kind"], case["id"]
        assert payload["status"] == expected["status"], case["id"]
        if payload["kind"] == "RemoteRegistryError":
            assert payload["error"]["code"] == expected["error_code"], case["id"]
        if "profile" in expected:
            assert payload["registry"]["profile"] == expected["profile"], case["id"]
        if "package_count" in expected:
            actual = (
                payload["registry"]["package_count"]
                if payload["kind"] == "RemoteRegistryStatus"
                else payload["package_count"]
            )
            assert actual == expected["package_count"], case["id"]
        if "version_count" in expected:
            actual = (
                payload["registry"]["version_count"]
                if payload["kind"] == "RemoteRegistryStatus"
                else payload["version_count"]
            )
            assert actual == expected["version_count"], case["id"]
        if "package_id" in expected:
            assert payload["package"]["package_id"] == expected["package_id"], case["id"]
        if "version" in expected:
            assert payload["package"]["version"] == expected["version"], case["id"]
        if "yanked" in expected:
            assert payload["package"]["state"]["yanked"] is expected["yanked"], case["id"]
        if "capability_id" in expected:
            assert payload["query"]["capability_id"] == expected["capability_id"], case["id"]
        if "result_count" in expected:
            assert payload["result_count"] == expected["result_count"], case["id"]


def test_remote_registry_payload_validator_rejects_incomplete_source() -> None:
    payload = load_remote_registry_fixture("capability-search.json")
    del payload["results"][0]["source"]["size"]

    errors = validate_remote_registry_payload(payload)

    assert any(
        issue.code == "remote_registry_field_invalid" and issue.field == "results.0.source.size"
        for issue in errors
    )


def test_remote_registry_search_fetches_exact_capability(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    payload = load_remote_registry_fixture("capability-search.json")

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        captured["url"] = request.full_url
        captured["accept"] = request.get_header("Accept")
        captured["timeout"] = timeout
        return FakeRemoteResponse(payload)

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = search_remote_registry(
        "https://registry.example.invalid",
        "document_conversion.email_to_markdown",
        timeout=2.5,
    )

    assert_golden_json("remote-search-email-tools.json", report)
    assert captured == {
        "url": (
            "https://registry.example.invalid/v0/capabilities/"
            "document_conversion.email_to_markdown/packages"
        ),
        "accept": "application/json",
        "timeout": 2.5,
    }


def test_remote_registry_package_and_version_fetch_expected_endpoints(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payloads = {
        "https://registry.example.invalid/v0/packages/document_conversion.email_tools": (
            load_remote_registry_fixture("package-metadata.json")
        ),
        (
            "https://registry.example.invalid/v0/packages/"
            "document_conversion.email_tools/versions/0.1.0"
        ): load_remote_registry_fixture("package-version.json"),
    }
    seen: list[str] = []

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        seen.append(request.full_url)
        return FakeRemoteResponse(payloads[request.full_url])

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    package = get_remote_package(
        "https://registry.example.invalid",
        "document_conversion.email_tools",
    )
    version = get_remote_package_version(
        "https://registry.example.invalid",
        "document_conversion.email_tools@0.1.0",
    )

    assert package["status"] == "ok"
    assert package["payload"]["kind"] == "RemotePackage"
    assert version["status"] == "ok"
    assert version["payload"]["kind"] == "RemotePackageVersion"
    assert seen == list(payloads)


def test_remote_registry_status_and_package_index_fetch_expected_endpoints(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payloads = {
        "https://registry.example.invalid/v0/status": (
            load_remote_registry_fixture("registry-status.json")
        ),
        "https://registry.example.invalid/v0/packages": (
            load_remote_registry_fixture("package-index.json")
        ),
    }
    seen: list[str] = []

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        seen.append(request.full_url)
        return FakeRemoteResponse(payloads[request.full_url])

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    status = get_remote_registry_status("https://registry.example.invalid")
    package_index = get_remote_package_index("https://registry.example.invalid")

    assert status["status"] == "ok"
    assert status["payload"]["kind"] == "RemoteRegistryStatus"
    assert status["payload"]["registry"]["profile"] == "public_static_index"
    assert package_index["status"] == "ok"
    assert package_index["payload"]["kind"] == "RemotePackageIndex"
    assert package_index["payload"]["package_count"] == 1
    assert seen == list(payloads)


def test_remote_registry_error_payload_returns_not_found(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(load_remote_registry_fixture("error-not-found.json"))

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = get_remote_package(
        "https://registry.example.invalid",
        "missing.package",
    )

    assert report["status"] == "not_found"
    assert report["payload"]["kind"] == "RemoteRegistryError"
    assert issue_codes(report["errors"]) == {"package_not_found"}


def test_remote_registry_rejects_package_target_mismatch(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payload = load_remote_registry_fixture("package-version.json")
    payload["package"]["package_id"] = "document_conversion.other_tools"

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(payload)

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = get_remote_package_version(
        "https://registry.example.invalid",
        "document_conversion.email_tools@0.1.0",
    )

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"remote_registry_target_mismatch"}
    assert report["errors"][0]["field"] == "package.package_id"


def test_remote_registry_rejects_version_target_mismatch(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payload = load_remote_registry_fixture("package-version.json")
    payload["package"]["version"] = "0.2.0"

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(payload)

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = get_remote_package_version(
        "https://registry.example.invalid",
        "document_conversion.email_tools@0.1.0",
    )

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"remote_registry_target_mismatch"}
    assert report["errors"][0]["field"] == "package.version"


def test_remote_registry_rejects_capability_target_mismatch(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payload = load_remote_registry_fixture("capability-search.json")
    payload["results"][0]["matched_capability"] = "document_conversion.other"

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(payload)

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = search_remote_registry(
        "https://registry.example.invalid",
        "document_conversion.email_to_markdown",
    )

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"remote_registry_target_mismatch"}
    assert report["errors"][0]["field"] == "results.0.matched_capability"


def test_remote_registry_invalid_input_does_not_fetch(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fail_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        raise AssertionError("remote registry client should not fetch invalid input")

    monkeypatch.setattr(core_module, "urlopen", fail_urlopen)

    report = search_remote_registry("https://registry.example.invalid", "BadCapability")

    assert report["status"] == "invalid"
    assert report["endpoint"] is None
    assert issue_codes(report["errors"]) == {"capability_id_invalid"}


def test_public_index_generate_writes_static_remote_registry_payloads(tmp_path: Path) -> None:
    output = tmp_path / "site"

    report = generate_public_index(
        [ROOT / "examples/email_tools"],
        output,
        "https://registry.example.invalid",
    )

    assert report["status"] == "ok"
    status_payload = json.loads((output / "v0/status/index.json").read_text(encoding="utf-8"))
    package_index_payload = json.loads(
        (output / "v0/packages/index.json").read_text(encoding="utf-8")
    )
    package_payload = json.loads(
        (output / "v0/packages/document_conversion.email_tools/index.json").read_text(
            encoding="utf-8"
        )
    )
    package_directory_index = json.loads(
        (output / "v0/packages/document_conversion.email_tools/index.html").read_text(
            encoding="utf-8"
        )
    )
    version_payload = json.loads(
        (
            output / "v0/packages/document_conversion.email_tools/versions/0.1.0/index.json"
        ).read_text(encoding="utf-8")
    )
    capability_payload = json.loads(
        (
            output / "v0/capabilities/document_conversion.email_to_markdown/packages/index.json"
        ).read_text(encoding="utf-8")
    )
    archive = (
        output
        / "v0/packages/document_conversion.email_tools/versions/0.1.0/"
        / "document_conversion.email_tools-0.1.0.specpm.tgz"
    )

    assert archive.is_file()
    assert_remote_registry_payload_shape(status_payload)
    assert_remote_registry_payload_shape(package_index_payload)
    assert_remote_registry_payload_shape(package_payload)
    assert package_directory_index == package_payload
    assert_remote_registry_payload_shape(version_payload)
    assert_remote_registry_payload_shape(capability_payload)
    assert status_payload["registry"] == {
        "profile": "public_static_index",
        "api_version": "v0",
        "read_only": True,
        "authority": "metadata_only",
        "package_count": 1,
        "version_count": 1,
        "capability_count": 1,
    }
    assert package_index_payload["packages"][0]["package_id"] == ("document_conversion.email_tools")
    assert package_payload["package"]["latest_version"] == "0.1.0"
    assert capability_payload["results"][0]["matched_capability"] == (
        "document_conversion.email_to_markdown"
    )
    assert version_payload["package"]["source"]["url"] == (
        "https://registry.example.invalid/v0/packages/"
        "document_conversion.email_tools/versions/0.1.0/"
        "document_conversion.email_tools-0.1.0.specpm.tgz"
    )
    assert version_payload["package"]["source"]["digest"]["value"] == sha256_path(archive)
    assert version_payload["package"]["source"]["size"] == archive.stat().st_size
    assert sorted(report["written_files"]) == report["written_files"]


def test_public_index_generate_rejects_duplicate_version_conflict(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    output = tmp_path / "site"
    shutil.copytree(ROOT / "examples/email_tools", first)
    shutil.copytree(ROOT / "examples/email_tools", second)
    (second / "evidence/README.md").write_text("Changed evidence.\n", encoding="utf-8")

    report = generate_public_index(
        [first, second],
        output,
        "https://0al-spec.github.io/SpecPM",
    )

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"public_index_duplicate_package_conflict"}
    assert not output.exists()


def test_public_index_generate_replaces_stale_v0_output(tmp_path: Path) -> None:
    first = copy_email_package(tmp_path, "first")
    second = copy_email_package(tmp_path, "second")
    update_email_package(
        second,
        package_id="document_conversion.text_tools",
        package_name="Text Tools",
        capability_id="document_conversion.email_to_text",
    )
    output = tmp_path / "site"

    first_report = generate_public_index([first], output, "https://registry.example.invalid")
    second_report = generate_public_index([second], output, "https://registry.example.invalid")

    assert first_report["status"] == "ok"
    assert second_report["status"] == "ok"
    assert not (output / "v0/packages/document_conversion.email_tools/index.json").exists()
    assert not (
        output / "v0/capabilities/document_conversion.email_to_markdown/packages/index.json"
    ).exists()
    assert (output / "v0/packages/document_conversion.text_tools/index.json").is_file()
    assert (
        output / "v0/capabilities/document_conversion.email_to_text/packages/index.json"
    ).is_file()


def test_public_index_generate_rejects_malformed_registry_urls(tmp_path: Path) -> None:
    package = ROOT / "examples/email_tools"
    bad_urls = [
        "https://",
        "https://user:secret@registry.example.invalid",
        "https://registry.example.invalid?token=secret-value",
        "https://registry.example.invalid#fragment",
        "http://registry.example.invalid",
    ]

    for index, registry_url in enumerate(bad_urls):
        output = tmp_path / f"site-{index}"
        report = generate_public_index([package], output, registry_url)

        assert report["status"] == "invalid", registry_url
        assert issue_codes(report["errors"]) == {"public_index_registry_url_invalid"}
        assert not output.exists()
        assert all("secret-value" not in error["message"] for error in report["errors"])


def test_public_index_generate_prefers_stable_release_for_latest_version(
    tmp_path: Path,
) -> None:
    prerelease = copy_email_package(tmp_path, "prerelease")
    stable = copy_email_package(tmp_path, "stable")
    update_email_package(prerelease, version="1.0.0-rc.1")
    update_email_package(stable, version="1.0.0")
    output = tmp_path / "site"

    report = generate_public_index(
        [prerelease, stable],
        output,
        "https://registry.example.invalid",
    )

    package_payload = json.loads(
        (output / "v0/packages/document_conversion.email_tools/index.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["status"] == "ok"
    assert package_payload["package"]["latest_version"] == "1.0.0"
    assert [item["version"] for item in package_payload["package"]["versions"]] == [
        "1.0.0-rc.1",
        "1.0.0",
    ]


def test_public_index_accepted_manifest_resolves_repository_relative_packages() -> None:
    report = load_public_index_manifest(PUBLIC_INDEX_ACCEPTED_MANIFEST, root=ROOT)

    assert report["status"] == "ok"
    assert report["package_dirs"] == [str((ROOT / "examples/email_tools").resolve())]
    assert report["sources"] == [
        {
            "kind": "local",
            "path": "examples/email_tools",
            "package_dir": str((ROOT / "examples/email_tools").resolve()),
        }
    ]
    assert report["errors"] == []


def test_public_index_accepted_manifest_resolves_pinned_remote_sources(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    revision = "a" * 40
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - repository: https://github.com/0al-spec/email-tools.git",
                "    ref: main",
                f"    revision: {revision}",
                "    path: packages/email_tools",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def fake_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        assert repository_url == "https://github.com/0al-spec/email-tools.git"
        assert ref == "main"
        package_dir = checkout / "packages/email_tools"
        package_dir.parent.mkdir(parents=True)
        shutil.copytree(ROOT / "examples/email_tools", package_dir)
        return {"status": "ok", "revision": revision, "errors": []}

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fake_checkout)

    report = load_public_index_manifest(
        manifest,
        root=tmp_path,
        remote_root=tmp_path / "remote-sources",
    )

    assert report["status"] == "ok"
    package_dir = Path(report["package_dirs"][0])
    assert package_dir.name == "email_tools"
    assert (package_dir / "specpm.yaml").is_file()
    assert report["sources"] == [
        {
            "kind": "git",
            "repository": "https://github.com/0al-spec/email-tools.git",
            "ref": "main",
            "revision": revision,
            "path": "packages/email_tools",
            "package_dir": str(package_dir),
        }
    ]
    assert report["errors"] == []


def test_public_index_accepted_manifest_normalizes_remote_revision_for_checkout(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    revision = "A" * 40
    normalized_revision = revision.lower()
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - repository: https://github.com/0al-spec/email-tools.git",
                "    ref: main",
                f"    revision: {revision}",
                "    path: .",
                "",
            ]
        ),
        encoding="utf-8",
    )
    checkouts: list[Path] = []

    def fake_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        checkouts.append(checkout)
        shutil.copytree(ROOT / "examples/email_tools", checkout)
        return {"status": "ok", "revision": normalized_revision, "errors": []}

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fake_checkout)

    report = load_public_index_manifest(
        manifest,
        root=tmp_path,
        remote_root=tmp_path / "remote-sources",
    )

    expected_checkout_name = public_index_module.public_index_checkout_dir_name(
        "https://github.com/0al-spec/email-tools.git",
        "main",
        normalized_revision,
    )
    assert report["status"] == "ok"
    assert checkouts[0].name == expected_checkout_name
    assert report["sources"][0]["revision"] == normalized_revision


def test_public_index_accepted_manifest_rejects_remote_revision_mismatch(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - repository: https://github.com/0al-spec/email-tools.git",
                "    ref: main",
                f"    revision: {'a' * 40}",
                "    path: .",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def fake_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        checkout.mkdir(parents=True)
        return {"status": "ok", "revision": "b" * 40, "errors": []}

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fake_checkout)

    report = load_public_index_manifest(
        manifest,
        root=tmp_path,
        remote_root=tmp_path / "remote-sources",
    )

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"public_index_manifest_repository_revision_mismatch"}


def test_public_index_accepted_manifest_adds_context_to_remote_checkout_errors(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - repository: https://github.com/0al-spec/email-tools.git",
                "    ref: main",
                f"    revision: {'a' * 40}",
                "    path: .",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def fake_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        return {
            "status": "invalid",
            "errors": [
                public_index_module.public_index_error(
                    "public_index_manifest_repository_checkout_failed",
                    "checkout failed",
                )
            ],
        }

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fake_checkout)

    report = load_public_index_manifest(
        manifest,
        root=tmp_path,
        remote_root=tmp_path / "remote-sources",
    )

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"public_index_manifest_repository_checkout_failed"}
    assert report["errors"][0]["field"] == "packages[0]"
    assert report["errors"][0]["detail"] == {
        "repository": "https://github.com/0al-spec/email-tools.git",
        "ref": "main",
    }


def test_public_index_accepted_manifest_skips_checkout_for_schema_invalid_remote_entry(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - repository: https://github.com/0al-spec/email-tools.git",
                "    ref: main",
                f"    revision: {'a' * 40}",
                "    path: .",
                "    unexpected: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def fail_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        raise AssertionError("schema-invalid manifest entry should not be checked out")

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fail_checkout)

    report = load_public_index_manifest(
        manifest,
        root=tmp_path,
        remote_root=tmp_path / "remote-sources",
    )

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"public_index_manifest_package_field_unknown"}


def test_public_index_generate_accepts_pinned_remote_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    revision = "a" * 40
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - repository: https://github.com/0al-spec/email-tools.git",
                "    ref: main",
                f"    revision: {revision}",
                "    path: .",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def fake_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        shutil.copytree(ROOT / "examples/email_tools", checkout)
        return {"status": "ok", "revision": revision, "errors": []}

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fake_checkout)

    report = generate_public_index_from_inputs(
        [],
        tmp_path / "site",
        "https://registry.example.invalid",
        manifest_path=manifest,
        root=tmp_path,
    )

    assert report["status"] == "ok"
    assert (tmp_path / "site/v0/packages/document_conversion.email_tools/index.json").is_file()


def test_public_index_accepted_manifest_rejects_path_escape(tmp_path: Path) -> None:
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "schemaVersion: 1\npackages:\n  - path: ../outside\n",
        encoding="utf-8",
    )

    report = load_public_index_manifest(manifest, root=tmp_path / "repo")

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"public_index_manifest_package_path_escape"}


def test_public_index_accepted_manifest_rejects_unknown_entry_fields(tmp_path: Path) -> None:
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "schemaVersion: 1\npackages:\n  - path: examples/email_tools\n    extra: false\n",
        encoding="utf-8",
    )

    report = load_public_index_manifest(manifest, root=ROOT)

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"public_index_manifest_package_field_unknown"}


def test_cli_public_index_generate_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(
        [
            "public-index",
            "generate",
            str(ROOT / "examples/email_tools"),
            "--output",
            str(tmp_path / "site"),
            "--registry",
            "http://localhost:8081",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["written_count"] == 11


def test_cli_public_index_generate_accepts_reviewed_manifest(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(
        [
            "public-index",
            "generate",
            "--manifest",
            str(PUBLIC_INDEX_ACCEPTED_MANIFEST),
            "--output",
            str(tmp_path / "site"),
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert (tmp_path / "site/v0/packages/document_conversion.email_tools/index.json").is_file()


def test_cli_public_index_generate_requires_package_or_manifest(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SystemExit) as error:
        main(
            [
                "public-index",
                "generate",
                "--output",
                str(tmp_path / "site"),
                "--registry",
                "https://registry.example.invalid",
                "--json",
            ]
        )

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert "requires at least one package directory or --manifest" in captured.err


def test_cli_remote_search_json(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(load_remote_registry_fixture("capability-search.json"))

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    exit_code = main(
        [
            "remote",
            "search",
            "document_conversion.email_to_markdown",
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["payload"]["kind"] == "RemoteCapabilitySearch"


def test_cli_remote_status_and_packages_json(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    payloads = {
        "https://registry.example.invalid/v0/status": (
            load_remote_registry_fixture("registry-status.json")
        ),
        "https://registry.example.invalid/v0/packages": (
            load_remote_registry_fixture("package-index.json")
        ),
    }

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(payloads[request.full_url])

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    status_exit = main(
        [
            "remote",
            "status",
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ]
    )
    status_output = json.loads(capsys.readouterr().out)
    packages_exit = main(
        [
            "remote",
            "packages",
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ]
    )
    packages_output = json.loads(capsys.readouterr().out)

    assert status_exit == 0
    assert status_output["payload"]["kind"] == "RemoteRegistryStatus"
    assert packages_exit == 0
    assert packages_output["payload"]["kind"] == "RemotePackageIndex"


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


def test_cli_exit_code_contract_for_success_and_failure_paths(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    invalid_package = tmp_path / "invalid-package"
    invalid_package.mkdir()
    (invalid_package / "specpm.yaml").write_text("apiVersion: [", encoding="utf-8")
    index_package(ROOT / "examples/email_tools", index_path)

    valid_commands = [
        ["validate", str(ROOT / "examples/email_tools"), "--json"],
        ["inspect", str(ROOT / "examples/email_tools"), "--json"],
        [
            "pack",
            str(ROOT / "examples/email_tools"),
            "-o",
            str(tmp_path / "email_tools.specpm.tgz"),
            "--json",
        ],
        ["index", str(ROOT / "examples/email_tools"), "--index", str(index_path), "--json"],
        [
            "search",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--json",
        ],
        [
            "yank",
            "document_conversion.email_tools@0.1.0",
            "--index",
            str(index_path),
            "--reason",
            "exit code smoke",
            "--json",
        ],
        [
            "unyank",
            "document_conversion.email_tools@0.1.0",
            "--index",
            str(index_path),
            "--json",
        ],
        [
            "add",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--project",
            str(project),
            "--json",
        ],
        ["diff", str(ROOT / "examples/email_tools"), str(ROOT / "examples/email_tools"), "--json"],
        ["inbox", "list", "--root", str(SPECGRAPH_FIXTURE_ROOT), "--json"],
        [
            "inbox",
            "inspect",
            "specgraph.core_repository_facade",
            "--root",
            str(SPECGRAPH_FIXTURE_ROOT),
            "--json",
        ],
        [
            "public-index",
            "generate",
            str(ROOT / "examples/email_tools"),
            "--output",
            str(tmp_path / "public-index"),
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ],
    ]
    invalid_commands = [
        ["validate", str(invalid_package), "--json"],
        ["inspect", str(invalid_package), "--json"],
        ["pack", str(invalid_package), "-o", str(tmp_path / "invalid.specpm.tgz"), "--json"],
        ["index", str(tmp_path / "missing-package"), "--index", str(index_path), "--json"],
        [
            "search",
            "BadCapability",
            "--index",
            str(index_path),
            "--json",
        ],
        [
            "yank",
            "BadPackage@0.1.0",
            "--index",
            str(index_path),
            "--reason",
            "invalid smoke",
            "--json",
        ],
        [
            "unyank",
            "BadPackage@0.1.0",
            "--index",
            str(index_path),
            "--json",
        ],
        [
            "add",
            "BadCapability",
            "--index",
            str(index_path),
            "--project",
            str(project),
            "--json",
        ],
        ["diff", str(invalid_package), str(ROOT / "examples/email_tools"), "--json"],
        [
            "inbox",
            "inspect",
            "missing.bundle",
            "--root",
            str(SPECGRAPH_FIXTURE_ROOT),
            "--json",
        ],
        [
            "public-index",
            "generate",
            str(ROOT / "examples/email_tools"),
            "--output",
            str(tmp_path / "invalid-public-index"),
            "--registry",
            "http://registry.example.invalid",
            "--json",
        ],
    ]

    for command in valid_commands:
        assert main(command) == 0, command
        capsys.readouterr()
    for command in invalid_commands:
        assert main(command) == 1, command
        capsys.readouterr()


def test_cli_add_ambiguity_returns_nonzero_exit_code(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    index_path = tmp_path / "index.json"
    first_entry = indexed_email_entry(tmp_path)
    second_entry = dict(first_entry)
    second_entry["package_id"] = "document_conversion.alt_email_tools"
    second_entry["name"] = "Alt Email Tools"
    second_entry["source"] = {
        **first_entry["source"],
        "digest": {"algorithm": "sha256", "value": "e" * 64},
    }
    write_index_payload(index_path, [first_entry, second_entry])

    exit_code = main(
        [
            "add",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--project",
            str(tmp_path / "project"),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["status"] == "ambiguous"


def test_cli_end_to_end_local_package_workflow(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    package = ROOT / "examples/email_tools"
    archive = tmp_path / "email_tools.specpm.tgz"
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"

    validation = run_cli_json(["validate", str(package), "--json"], capsys)
    inspection = run_cli_json(["inspect", str(package), "--json"], capsys)
    pack = run_cli_json(["pack", str(package), "-o", str(archive), "--json"], capsys)
    indexed = run_cli_json(
        ["index", str(archive), "--index", str(index_path), "--json"],
        capsys,
    )
    search = run_cli_json(
        [
            "search",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--json",
        ],
        capsys,
    )
    yanked = run_cli_json(
        [
            "yank",
            "document_conversion.email_tools@0.1.0",
            "--index",
            str(index_path),
            "--reason",
            "end-to-end lifecycle smoke",
            "--json",
        ],
        capsys,
    )
    yanked_search = run_cli_json(
        [
            "search",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--json",
        ],
        capsys,
    )
    unyanked = run_cli_json(
        [
            "unyank",
            "document_conversion.email_tools@0.1.0",
            "--index",
            str(index_path),
            "--json",
        ],
        capsys,
    )
    added = run_cli_json(
        [
            "add",
            "document_conversion.email_to_markdown",
            "--index",
            str(index_path),
            "--project",
            str(project),
            "--json",
        ],
        capsys,
    )
    inbox_list = run_cli_json(
        ["inbox", "list", "--root", str(SPECGRAPH_FIXTURE_ROOT), "--json"],
        capsys,
    )
    inbox_inspect = run_cli_json(
        [
            "inbox",
            "inspect",
            "specgraph.core_repository_facade",
            "--root",
            str(SPECGRAPH_FIXTURE_ROOT),
            "--json",
        ],
        capsys,
    )
    diff = run_cli_json(["diff", str(package), str(package), "--json"], capsys)

    assert validation["status"] == "valid"
    assert inspection["package"]["identity"]["package_id"] == "document_conversion.email_tools"
    assert pack["status"] == "packed"
    assert archive.is_file()
    assert indexed["status"] == "indexed"
    assert indexed["entry"]["source"]["kind"] == "archive"
    assert search["result_count"] == 1
    assert yanked["status"] == "yanked"
    assert yanked_search["results"][0]["yanked"] is True
    assert unyanked["status"] == "unyanked"
    assert added["status"] == "added"
    assert (project / "specpm.lock").is_file()
    assert inbox_list["bundle_count"] == 1
    assert inbox_inspect["inbox_status"] == "draft_visible"
    assert diff["classification"] == "unchanged"


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


def test_validator_rejects_missing_manifest(tmp_path: Path) -> None:
    package = tmp_path / "missing-manifest"
    package.mkdir()

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "manifest_missing" for issue in report["errors"])


def test_validator_rejects_missing_referenced_spec(tmp_path: Path) -> None:
    package = tmp_path / "missing-spec"
    package.mkdir()
    (package / "specpm.yaml").write_text(
        """
apiVersion: specpm.dev/v0.1
kind: SpecPackage
metadata:
  id: missing.spec
  name: Missing Spec
  version: 0.1.0
  summary: Package with missing referenced spec.
  license: MIT
specs:
  - path: specs/missing.spec.yaml
index:
  provides:
    capabilities:
      - missing.spec
""".strip(),
        encoding="utf-8",
    )

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "spec_missing" for issue in report["errors"])


def test_validator_rejects_spec_path_traversal(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "spec-traversal")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["specs"] = [{"path": "../outside.spec.yaml"}]
    write_yaml_file(manifest_path, manifest)

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "path_escape" for issue in report["errors"])


def test_validator_rejects_evidence_path_escape(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "evidence-traversal")
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["evidence"][0]["path"] = "../outside.md"
    write_yaml_file(spec_path, spec)

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "path_escape" for issue in report["errors"])


def test_validator_rejects_malformed_boundary_spec_yaml(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "malformed-spec")
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    spec_path.write_text("apiVersion: [", encoding="utf-8")

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "yaml_parse_error" for issue in report["errors"])


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


def test_search_reports_corrupted_index_json(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text("{", encoding="utf-8")

    report = search_index("document_conversion.email_to_markdown", index_path)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "index_json_invalid" for issue in report["errors"])


def test_search_reports_unsupported_index_schema(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text(
        json.dumps({"schemaVersion": 999, "packages": [], "capabilities": {}}),
        encoding="utf-8",
    )

    report = search_index("document_conversion.email_to_markdown", index_path)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "index_schema_unsupported" for issue in report["errors"])


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


def test_yank_index_package_marks_entry_and_blocks_add(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    index_package(ROOT / "examples/email_tools", index_path)

    report = yank_index_package(
        "document_conversion.email_tools@0.1.0",
        index_path,
        "superseded by a local smoke test",
    )
    search = search_index("document_conversion.email_to_markdown", index_path)
    add_report = add_package("document_conversion.email_tools@0.1.0", index_path, project)
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    package = index_payload["packages"][0]

    assert report["status"] == "yanked"
    assert report["package"]["yanked"] is True
    assert report["package"]["yank"]["reason"] == "superseded by a local smoke test"
    assert package["yanked"] is True
    assert package["yank"]["reason"] == "superseded by a local smoke test"
    assert search["results"][0]["yanked"] is True
    assert add_report["status"] == "invalid"
    assert any(issue["code"] == "package_yanked" for issue in add_report["errors"])


def test_yank_is_idempotent_and_unyank_reenables_add(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    project = tmp_path / "project"
    index_package(ROOT / "examples/email_tools", index_path)

    first = yank_index_package(
        "document_conversion.email_tools@0.1.0",
        index_path,
        "temporary local yank",
    )
    second = yank_index_package(
        "document_conversion.email_tools@0.1.0",
        index_path,
        "temporary local yank",
    )
    unyanked = unyank_index_package("document_conversion.email_tools@0.1.0", index_path)
    add_report = add_package("document_conversion.email_to_markdown", index_path, project)
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    package = index_payload["packages"][0]

    assert first["status"] == "yanked"
    assert second["status"] == "unchanged"
    assert unyanked["status"] == "unyanked"
    assert package["yanked"] is False
    assert "yank" not in package
    assert add_report["status"] == "added"


def test_yank_missing_package_ref_is_invalid(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    report = yank_index_package(
        "document_conversion.email_tools@9.9.9",
        index_path,
        "missing package",
    )

    assert report["status"] == "invalid"
    assert any(issue["code"] == "package_ref_not_found" for issue in report["errors"])


def test_add_rejects_corrupted_index_package_entry(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    write_index_payload(
        index_path,
        [
            {
                "package_id": "document_conversion.email_tools",
                "version": "0.1.0",
                "provided_capabilities": "not-a-list",
                "source": {},
            }
        ],
    )

    report = add_package(
        "document_conversion.email_tools@0.1.0",
        index_path,
        tmp_path / "project",
    )

    assert report["status"] == "invalid"
    error_codes = {issue["code"] for issue in report["errors"]}
    assert "package_digest_missing" in error_codes
    assert "package_capabilities_invalid" in error_codes


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


def test_cli_yank_and_unyank_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    yanked = run_cli_json(
        [
            "yank",
            "document_conversion.email_tools@0.1.0",
            "--index",
            str(index_path),
            "--reason",
            "cli lifecycle smoke",
            "--json",
        ],
        capsys,
    )
    unyanked = run_cli_json(
        [
            "unyank",
            "document_conversion.email_tools@0.1.0",
            "--index",
            str(index_path),
            "--json",
        ],
        capsys,
    )

    assert yanked["status"] == "yanked"
    assert yanked["package"]["yanked"] is True
    assert yanked["package"]["yank"]["reason"] == "cli lifecycle smoke"
    assert unyanked["status"] == "unyanked"
    assert unyanked["package"]["yanked"] is False


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


def test_index_rejects_corrupted_archive(tmp_path: Path) -> None:
    archive = tmp_path / "corrupted.specpm.tgz"
    archive.write_bytes(b"not a gzip tar archive")

    report = index_package(archive, tmp_path / "index.json")

    assert report["status"] == "invalid"
    assert any(issue["code"] == "archive_extract_failed" for issue in report["errors"])


def test_index_rejects_archive_member_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.specpm.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("../evil.txt")
        payload = b"escape"
        member.size = len(payload)
        tar.addfile(member, fileobj=io.BytesIO(payload))

    report = index_package(archive, tmp_path / "index.json")

    assert report["status"] == "invalid"
    assert any(issue["code"] == "archive_extract_failed" for issue in report["errors"])


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


def test_pack_rejects_nested_symlink_in_artifact_directory(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "nested-symlink")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["foreignArtifacts"] = [
        {
            "id": "foreign_docs",
            "format": "docs",
            "path": "foreign",
            "role": "documentation",
        }
    ]
    write_yaml_file(manifest_path, manifest)
    foreign_dir = package / "foreign"
    foreign_dir.mkdir()
    (tmp_path / "outside.md").write_text("outside", encoding="utf-8")
    (foreign_dir / "outside.md").symlink_to(tmp_path / "outside.md")

    report = pack_package(package, tmp_path / "nested-symlink.specpm.tgz")

    assert report["status"] == "invalid"
    assert any(issue["code"] == "pack_symlink_unsupported" for issue in report["errors"])


def test_pack_rejects_foreign_artifact_path_traversal(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "foreign-traversal")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["foreignArtifacts"] = [
        {
            "id": "outside",
            "format": "docs",
            "path": "../outside.md",
            "role": "documentation",
        }
    ]
    write_yaml_file(manifest_path, manifest)

    report = pack_package(package, tmp_path / "foreign-traversal.specpm.tgz")

    assert report["status"] == "invalid"
    assert any(issue["code"] == "validation_failed" for issue in report["errors"])
    assert any(issue["code"] == "path_escape" for issue in report["validation"]["errors"])


def test_pack_includes_large_evidence_file(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "large-evidence")
    evidence_path = package / "evidence/large.bin"
    evidence_path.write_bytes(b"specpm-large-evidence\n" * 65536)
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["evidence"].append(
        {
            "id": "large_fixture",
            "kind": "documentation",
            "path": "evidence/large.bin",
            "supports": ["intent.summary"],
        }
    )
    write_yaml_file(spec_path, spec)
    archive = tmp_path / "large-evidence.specpm.tgz"

    report = pack_package(package, archive)

    assert report["status"] == "packed"
    assert "evidence/large.bin" in report["included_files"]
    with tarfile.open(archive, "r:gz") as tar:
        member = tar.getmember("evidence/large.bin")
        assert member.size == evidence_path.stat().st_size


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
