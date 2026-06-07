from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from specpm import __version__
from specpm import core as core_module
from specpm import index_submission as index_submission_module
from specpm import public_index as public_index_module
from specpm.cli import build_parser, main
from specpm.core import (
    add_package,
    diff_packages,
    get_remote_intent,
    get_remote_intent_index,
    get_remote_package,
    get_remote_package_index,
    get_remote_package_version,
    get_remote_registry_status,
    index_package,
    inspect_inbox_bundle,
    inspect_package,
    list_inbox,
    observe_remote_registry,
    pack_package,
    search_index,
    search_intent_index,
    search_remote_registry,
    search_remote_registry_intent,
    unyank_index_package,
    validate_package,
    validate_remote_registry_payload,
    yank_index_package,
)
from specpm.index_submission import (
    accepted_manifest_candidates,
    parse_submission_issue_body,
    prepare_accepted_manifest_pr,
    render_accepted_manifest_candidate_yaml,
    render_accepted_manifest_pr_body,
    render_submission_report_markdown,
    validate_submission_body,
)
from specpm.producer_bundle import materialize_package_set_handoff, preflight_producer_bundle
from specpm.public_index import (
    generate_public_index,
    generate_public_index_from_inputs,
    load_public_index_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
SPECGRAPH_FIXTURE_ROOT = ROOT / "tests/fixtures/specgraph_exports"
GOLDEN_FIXTURE_ROOT = ROOT / "tests/fixtures/golden"
CONFORMANCE_SUITE = ROOT / "tests/fixtures/conformance/specpm-conformance-v0.json"
CONFORMANCE_FIXTURE_MANIFEST = ROOT / "tests/fixtures/conformance/fixture-manifest.json"
ADD_SPECPACKAGES_ISSUE_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/add-specpackages.yml"
REMOVE_SPECPACKAGES_ISSUE_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/remove-specpackages.yml"
CLAIM_NAMESPACE_ISSUE_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/claim-namespace.yml"
NAMESPACE_CLAIM_POLICY = ROOT / "specs/NAMESPACE_CLAIM_POLICY.md"
PUBLIC_INDEX_OPERATOR_GUIDE = ROOT / "specs/PUBLIC_INDEX_OPERATOR_GUIDE.md"
PACKAGE_SUBMISSION_WORKFLOW = ROOT / ".github/workflows/package-submission-check.yml"
PACKAGE_SUBMISSION_TRIAGE_WORKFLOW = ROOT / ".github/workflows/package-submission-triage.yml"
PRODUCER_BUNDLE_PREFLIGHT_WORKFLOW = ROOT / ".github/workflows/producer-bundle-preflight.yml"
NAMESPACE_CLAIM_TRIAGE_WORKFLOW = ROOT / ".github/workflows/namespace-claim-triage.yml"
NAMESPACE_CLAIM_DECISION_REPORT_WORKFLOW = (
    ROOT / ".github/workflows/namespace-claim-decision-report.yml"
)
NAMESPACE_CLAIM_DECISION_SUMMARY_WORKFLOW = (
    ROOT / ".github/workflows/namespace-claim-decision-summary.yml"
)
DOCS_WORKFLOW = ROOT / ".github/workflows/docs.yml"
DEPLOY_CONNECTION_CHECK_WORKFLOW = ROOT / ".github/workflows/deploy-connection-check.yml"
DOCKERFILE = ROOT / "Dockerfile"
MAKEFILE = ROOT / "Makefile"
AGENTS_FILE = ROOT / "AGENTS.md"
ROADMAP_DOC = ROOT / "ROADMAP.md"
DEPLOY_FIRST_DOC = ROOT / "specs/DEPLOY_FIRST.md"
PUBLIC_ALPHA_DOC = ROOT / "specs/PUBLIC_ALPHA.md"
DOWNSTREAM_REGISTRY_CONSUMER_GUIDE = ROOT / "specs/DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.md"
SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT = ROOT / "specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md"
SPECGRAPH_REGISTRY_OBSERVATION_FIXTURES = ROOT / "tests/fixtures/specgraph_registry_observation"
REGISTRY_OBSERVATION_REPORTS_DOC = ROOT / "specs/REGISTRY_OBSERVATION_REPORTS.md"
REGISTRY_OPERATIONS_DOC = ROOT / "specs/REGISTRY_OPERATIONS.md"
GITHUB_ACTIONS_MAINTENANCE_DOC = ROOT / "specs/GITHUB_ACTIONS_MAINTENANCE.md"
GITHUB_ACTIONS_PERMISSIONS_DOC = ROOT / "specs/GITHUB_ACTIONS_PERMISSIONS.md"
REMOTE_PACKAGE_ACQUISITION_DOC = ROOT / "specs/REMOTE_PACKAGE_ACQUISITION.md"
PACKAGE_SIGNING_REVOCATION_DOC = ROOT / "specs/PACKAGE_SIGNING_REVOCATION.md"
PROVENANCE_RECEIPTS_DOC = ROOT / "specs/PROVENANCE_RECEIPTS.md"
PROVENANCE_RECEIPT_FIXTURE = (
    ROOT / "tests/fixtures/provenance_receipts/public-static-receipt.example.json"
)
PRODUCER_RECEIPTS_DOC = ROOT / "specs/PRODUCER_RECEIPTS.md"
PRODUCER_BUNDLE_PROPOSAL_AUTOMATION_DOC = ROOT / "specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md"
PRODUCER_BUNDLE_FIXTURE_POLICY_DOC = ROOT / "specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md"
MULTI_PACKAGE_PRODUCER_INTAKE_DOC = ROOT / "specs/MULTI_PACKAGE_PRODUCER_INTAKE.md"
PRODUCER_RECEIPT_FIXTURE = (
    ROOT / "tests/fixtures/provenance_receipts/generated-spec-package-receipt.example.json"
)
REGISTRY_ACCEPTANCE_DECISION_DOC = ROOT / "specs/REGISTRY_ACCEPTANCE_DECISIONS.md"
REGISTRY_ACCEPTANCE_DECISION_FIXTURE = (
    ROOT / "tests/fixtures/provenance_receipts/registry-acceptance-decision.example.json"
)
INTENT_TAXONOMY_GOVERNANCE_DOC = ROOT / "specs/INTENT_TAXONOMY_GOVERNANCE.md"
DOCC_DEPLOYMENT_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/Deployment.md"
DOCC_ADD_PACKAGE_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/AddSpecPackage.md"
DOCC_PUBLIC_ALPHA_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/PublicAlphaRegistry.md"
DOCC_STATIC_REGISTRY_PIPELINE_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/StaticRegistryPipeline.md"
)
DOCC_REGISTRY_OPERATIONS_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/RegistryOperations.md"
DOCC_GITHUB_ACTIONS_MAINTENANCE_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/GitHubActionsMaintenance.md"
)
DOCC_GITHUB_ACTIONS_PERMISSIONS_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/GitHubActionsPermissions.md"
)
DOCC_REMOTE_PACKAGE_ACQUISITION_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/RemotePackageAcquisition.md"
)
DOCC_PACKAGE_SIGNING_REVOCATION_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/PackageSigningRevocation.md"
)
DOCC_PROVENANCE_RECEIPTS_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/ProvenanceReceipts.md"
DOCC_PRODUCER_RECEIPTS_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/ProducerReceipts.md"
DOCC_PRODUCER_BUNDLE_POLICY_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/ProducerBundleProposalPolicy.md"
)
DOCC_PRODUCER_BUNDLE_PROPOSAL_AUTOMATION_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/ProducerBundleProposalAutomation.md"
)
DOCC_PRODUCER_BUNDLE_FIXTURE_POLICY_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/ProducerBundleFixturePolicy.md"
)
DOCC_MULTI_PACKAGE_PRODUCER_INTAKE_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/MultiPackageProducerIntake.md"
)
DOCC_REGISTRY_ACCEPTANCE_DECISIONS_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/RegistryAcceptanceDecisions.md"
)
DOCC_INTENT_TAXONOMY_GOVERNANCE_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/IntentTaxonomyGovernance.md"
)
DOCC_ROADMAP_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/Roadmap.md"
DOCC_SPECGRAPH_INTEGRATION_PAGE = ROOT / "Sources/SpecPM/Documentation.docc/SpecGraphIntegration.md"
DOCC_SPECGRAPH_REGISTRY_OBSERVATION_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/SpecGraphRegistryObservation.md"
)
DOCC_REGISTRY_OBSERVATION_REPORTS_PAGE = (
    ROOT / "Sources/SpecPM/Documentation.docc/RegistryObservationReports.md"
)
COMPOSE_FILE = ROOT / "compose.yaml"
PUBLIC_INDEX_ACCEPTED_MANIFEST = ROOT / "public-index/accepted-packages.yml"
LANDING_PAGE = ROOT / "landing_page/index.html"
REGISTRY_VIEWER_PAGE = ROOT / "landing_page/viewer.html"
REGISTRY_VIEWER_DESIGN_CSS = ROOT / "landing_page/assets/specpm-design.css"
REGISTRY_VIEWER_CSS = ROOT / "landing_page/assets/viewer.css"
REGISTRY_VIEWER_JS = ROOT / "landing_page/assets/viewer.js"
SPECPM_RELEASE_REF = "v0.1.0"
SPECPM_RELEASE_REVISION = "0109b471bfea6dc765f4b97f2ce70b39ef08fb6f"
SPECNODE_RELEASE_REF = "v0.1.0"
SPECNODE_RELEASE_REVISION = "2ad889ed413370f79710f235a08b43aaaaecf81e"
ADD_SPECPACKAGES_ISSUE_URL = (
    "https://github.com/0al-spec/SpecPM/issues/new?template=add-specpackages.yml"
)
PULL_REQUEST_TEMPLATE = ROOT / ".github/PULL_REQUEST_TEMPLATE.md"
AGENT_SKILL_ROOT = ROOT / "skills/.experimental"
AGENT_SKILLS = {
    "specpm-author-spec": {
        "capability": "specpm.agent_skills.spec_authoring",
        "reference": "references/authoring-checklist.md",
    },
    "specpm-review-spec": {
        "capability": "specpm.agent_skills.spec_review",
        "reference": "references/review-checklist.md",
    },
}
CONFORMANCE_CASE_KINDS = {
    "public_registry_static_index",
    "registry_lifecycle",
    "remote_registry_payload",
    "validate_package",
}
REMOTE_REGISTRY_API_VERSION = "specpm.registry/v0"
REMOTE_REGISTRY_PAYLOAD_KINDS = {
    "RemoteCapabilitySearch",
    "RemoteIntent",
    "RemoteIntentIndex",
    "RemoteIntentSearch",
    "RemotePackage",
    "RemotePackageIndex",
    "RemotePackageVersion",
    "RemoteRegistryRoot",
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


def write_producer_bundle_pr_body(
    path: Path,
    *,
    manifest_digest: str = "sha256:placeholder",
    include_decision: bool = True,
) -> None:
    decision_block = ""
    if include_decision:
        decision_block = """
```json
{
  "registryAcceptanceDecision": {
    "status": "external_required",
    "requiredFor": ["public_index_acceptance"],
    "authority": "SpecPM maintainer review",
    "recordKind": "SpecPMRegistryAcceptanceDecision",
    "recordLocation": "SpecPM pull request or accepted-source review record",
    "producerReceiptAuthority": "evidence_only"
  }
}
```
"""
    path.write_text(
        f"""
# Producer-backed proposal

```json
{{
  "producerEvidenceLinks": [
    {{
      "role": "accepted_source_bundle",
      "path": "public-index/generated/example.package/0.1.0",
      "pathScope": "repo_relative",
      "required": true,
      "status": "expected"
    }},
    {{
      "role": "manifest",
      "path": "public-index/generated/example.package/0.1.0/specpm.yaml",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present",
      "digest": "{manifest_digest}"
    }},
    {{
      "role": "boundary_spec",
      "path": "public-index/generated/example.package/0.1.0/specs/example.spec.yaml",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    }},
    {{
      "role": "producer_receipt",
      "path": "public-index/generated/example.package/0.1.0/producer-receipt.json",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    }},
    {{
      "role": "validation_report",
      "path": "public-index/generated/example.package/0.1.0/validation-report.json",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    }},
    {{
      "role": "diagnostics",
      "path": "public-index/generated/example.package/0.1.0/diagnostics.json",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    }},
    {{
      "role": "producer_preflight",
      "path": "producer-preflight-report.json",
      "pathScope": "workflow_artifact",
      "required": false,
      "status": "missing"
    }},
    {{
      "role": "static_viewer",
      "path": "static-viewer/index.html",
      "pathScope": "workflow_artifact",
      "required": false,
      "status": "missing"
    }},
    {{
      "role": "accepted_source_diff",
      "path": "pull-request-diff",
      "pathScope": "pull_request",
      "required": true,
      "status": "expected"
    }}
  ]
}}
```
{decision_block}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def write_package_set_handoff_fixture(root: Path, *, bad_relation: bool = False) -> Path:
    root.mkdir(parents=True)
    members = [
        ("example.workspace", "workspace", "workspace", "main.spec.yaml"),
        ("example.member", "library", "member", "member.spec.yaml"),
    ]
    for package_id, _role, dirname, spec_name in members:
        package = root / dirname
        specs_dir = package / "specs"
        specs_dir.mkdir(parents=True)
        manifest_id = (
            "example.other" if bad_relation and package_id == "example.member" else package_id
        )
        (package / "specpm.yaml").write_text(
            f"schemaVersion: 1\nmetadata:\n  id: {manifest_id}\n  version: 0.1.0\n",
            encoding="utf-8",
        )
        (specs_dir / spec_name).write_text("apiVersion: specpm.dev/v0.1\n", encoding="utf-8")
        (package / "producer-receipt.json").write_text("{}\n", encoding="utf-8")
        (package / "validation-report.json").write_text('{"status":"valid"}\n', encoding="utf-8")
        (package / "diagnostics.json").write_text('{"status":"clean"}\n', encoding="utf-8")

    (root / "package-set-draft.json").write_text(
        '{"kind":"SpecHarvesterPackageSetDraft"}\n', encoding="utf-8"
    )
    (root / "package-relation-proposals.json").write_text(
        '{"kind":"SpecHarvesterPackageRelationProposals"}\n', encoding="utf-8"
    )
    (root / "bundle-set-preflight.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "summary": {"candidateCount": 2, "relationCount": 1, "errorCount": 0},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    relation_target = "example.missing" if bad_relation else "example.member"
    handoff = {
        "apiVersion": "spec-harvester.package-set-handoff-proposal/v0",
        "kind": "SpecHarvesterPackageSetHandoffProposal",
        "schemaVersion": 1,
        "status": "ok",
        "packageSet": {
            "id": "example.workspace",
            "candidateCount": 2,
            "relationCount": 1,
            "authority": "producer_observed_review_evidence",
        },
        "members": [
            {
                "packageId": "example.workspace",
                "role": "workspace",
                "candidatePath": "workspace",
                "manifestPath": "workspace/specpm.yaml",
                "producerReceiptPath": "workspace/producer-receipt.json",
                "validationReportPath": "workspace/validation-report.json",
                "diagnosticsReportPath": "workspace/diagnostics.json",
                "status": "ok",
                "evidenceLinks": member_handoff_links(root, "workspace", "main.spec.yaml"),
            },
            {
                "packageId": "example.member",
                "role": "library",
                "candidatePath": "member",
                "manifestPath": "member/specpm.yaml",
                "producerReceiptPath": "member/producer-receipt.json",
                "validationReportPath": "member/validation-report.json",
                "diagnosticsReportPath": "member/diagnostics.json",
                "status": "ok",
                "evidenceLinks": member_handoff_links(root, "member", "member.spec.yaml"),
            },
        ],
        "relations": [
            {
                "id": "example.workspace.contains.example.member",
                "type": "contains",
                "source": {"packageId": "example.workspace"},
                "target": {"packageId": relation_target},
                "reviewStatus": "producer_observed",
                "authority": "producer_observed_review_evidence",
            }
        ],
        "evidenceLinks": [
            handoff_link(root, "package_set_draft", "package-set-draft.json"),
            handoff_link(root, "package_relation_proposals", "package-relation-proposals.json"),
            handoff_link(root, "bundle_set_preflight", "bundle-set-preflight.json"),
            {
                "role": "package_relation_summary",
                "path": "package-relation-proposals.json",
                "pathScope": "bundle_relative",
                "status": "present",
                "relationCount": 1,
                "containsCount": 1,
            },
            {
                "role": "member_candidate_bundle",
                "path": "workspace",
                "pathScope": "bundle_relative",
                "status": "present",
                "packageId": "example.workspace",
            },
            {
                "role": "member_candidate_bundle",
                "path": "member",
                "pathScope": "bundle_relative",
                "status": "present",
                "packageId": "example.member",
            },
        ],
        "preflight": {
            "status": "passed",
            "path": "bundle-set-preflight.json",
            "candidateCount": 2,
            "relationCount": 1,
            "errorCount": 0,
            "warningCount": 0,
        },
        "registryAcceptanceDecision": {
            "status": "external_required",
            "requiredFor": ["public_index_acceptance", "package_relation_acceptance"],
            "recordKind": "SpecPMRegistryAcceptanceDecision",
            "producerAuthority": "evidence_only",
            "acceptanceAuthority": "SpecPM maintainer review",
        },
        "nonGoals": ["specpm_acceptance", "relation_acceptance", "registry_publication"],
    }
    handoff_path = root / "package-set-handoff-proposal.json"
    handoff_path.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return handoff_path


def member_handoff_links(root: Path, dirname: str, spec_name: str) -> list[dict[str, str]]:
    return [
        handoff_link(root, "member_manifest", f"{dirname}/specpm.yaml"),
        handoff_link(root, "member_boundary_spec", f"{dirname}/specs/{spec_name}"),
        handoff_link(root, "member_producer_receipt", f"{dirname}/producer-receipt.json"),
        handoff_link(root, "member_validation_report", f"{dirname}/validation-report.json"),
        handoff_link(root, "member_diagnostics", f"{dirname}/diagnostics.json"),
    ]


def handoff_link(root: Path, role: str, path: str) -> dict[str, str]:
    return {
        "role": role,
        "path": path,
        "pathScope": "bundle_relative",
        "status": "present",
        "digest": f"sha256:{sha256_path(root / path)}",
    }


def load_conformance_suite() -> dict[str, Any]:
    suite = json.loads(CONFORMANCE_SUITE.read_text(encoding="utf-8"))
    assert suite["schemaVersion"] == 1
    assert suite["suite"] == "specpm-conformance-v0"
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


def make_target_prerequisites(makefile: str, target: str) -> list[str]:
    match = re.search(rf"^{re.escape(target)}:(.*)$", makefile, re.MULTILINE)
    assert match is not None, target
    return match.group(1).split()


def make_target_recipe(makefile: str, target: str) -> str:
    lines = makefile.splitlines()
    target_line = f"{target}:"
    for index, line in enumerate(lines):
        if line.startswith(target_line):
            recipe_lines: list[str] = []
            for recipe_line in lines[index + 1 :]:
                if recipe_line and not recipe_line.startswith(("\t", " ", "@")):
                    break
                if recipe_line.strip():
                    recipe_lines.append(recipe_line)
            return " ".join(" ".join(recipe_lines).split())
    raise AssertionError(target)


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
        if "intents" in package:
            assert isinstance(package["intents"], list)
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
            if "intents" in package:
                assert isinstance(package["intents"], list)
            assert isinstance(package["versions"], list)
        return

    if payload["kind"] == "RemoteIntentIndex":
        assert payload["catalog"]["authority"] == "observed_metadata_only"
        assert payload["catalog"]["canonical"] is False
        assert isinstance(payload["catalog"]["description"], str)
        assert isinstance(payload["intent_count"], int)
        assert isinstance(payload["intents"], list)
        assert payload["intent_count"] == len(payload["intents"])
        for intent in payload["intents"]:
            assert isinstance(intent["intent_id"], str)
            assert intent["status"] == "observed"
            assert intent["canonical"] is False
            assert isinstance(intent["package_count"], int)
            assert isinstance(intent["version_count"], int)
            assert isinstance(intent["capability_count"], int)
            assert isinstance(intent["package_ids"], list)
            assert isinstance(intent["capabilities"], list)
            assert intent["package_count"] == len(intent["package_ids"])
            assert intent["capability_count"] == len(intent["capabilities"])
        return

    if payload["kind"] == "RemoteIntent":
        assert payload["catalog"]["authority"] == "observed_metadata_only"
        assert payload["catalog"]["canonical"] is False
        assert isinstance(payload["catalog"]["description"], str)
        intent = payload["intent"]
        assert isinstance(intent["intent_id"], str)
        assert intent["status"] == "observed"
        assert intent["canonical"] is False
        assert isinstance(intent["package_ids"], list)
        assert isinstance(intent["capabilities"], list)
        assert isinstance(payload["packages"], list)
        assert intent["version_count"] == len(payload["packages"])
        for package in payload["packages"]:
            assert isinstance(package["package_id"], str)
            assert isinstance(package["version"], str)
            assert isinstance(package["matched_capabilities"], list)
            assert isinstance(package["provided_intents"], list)
            assert isinstance(package["provided_capabilities"], list)
            assert isinstance(package["required_capabilities"], list)
            assert isinstance(package["yanked"], bool)
            assert isinstance(package["deprecated"], bool)
        return

    if payload["kind"] == "RemotePackageVersion":
        package = payload["package"]
        assert isinstance(package["package_id"], str)
        assert isinstance(package["name"], str)
        assert isinstance(package["version"], str)
        assert isinstance(package["provided_capabilities"], list)
        assert isinstance(package["required_capabilities"], list)
        if "provided_intents" in package:
            assert isinstance(package["provided_intents"], list)
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

    if payload["kind"] == "RemoteIntentSearch":
        assert payload["query"]["match"] == "exact"
        assert isinstance(payload["query"]["intent_id"], str)
        assert isinstance(payload["result_count"], int)
        assert payload["result_count"] == len(payload["results"])
        for result in payload["results"]:
            assert isinstance(result["package_id"], str)
            assert isinstance(result["version"], str)
            assert isinstance(result["matched_intent"], str)
            assert isinstance(result["matched_capabilities"], list)
            assert isinstance(result["provided_intents"], list)
            assert isinstance(result["provided_capabilities"], list)
            assert isinstance(result["required_capabilities"], list)
            assert isinstance(result["yanked"], bool)
            assert isinstance(result["deprecated"], bool)
            assert_remote_registry_source(result["source"])
        return

    if payload["kind"] in {"RemoteRegistryRoot", "RemoteRegistryStatus"}:
        registry = payload["registry"]
        assert isinstance(registry["profile"], str)
        assert registry["profile"]
        assert isinstance(registry["api_version"], str)
        assert isinstance(registry["read_only"], bool)
        assert isinstance(registry["authority"], str)
        assert isinstance(registry["package_count"], int)
        assert isinstance(registry["version_count"], int)
        assert isinstance(registry["capability_count"], int)
        if "intent_count" in registry:
            assert isinstance(registry["intent_count"], int)
        if "implementation" in registry:
            implementation = registry["implementation"]
            assert implementation["name"] == "SpecPM"
            assert isinstance(implementation["version"], str)
            assert implementation["version"]
            if "build" in implementation:
                build = implementation["build"]
                if "number" in build:
                    assert isinstance(build["number"], str)
                    assert build["number"]
                if "revision" in build:
                    assert isinstance(build["revision"], str)
                    assert build["revision"]
                if "revision_short" in build:
                    assert isinstance(build["revision_short"], str)
                    assert build["revision_short"]
        if payload["kind"] == "RemoteRegistryRoot":
            assert isinstance(payload["endpoints"], dict)
            assert isinstance(payload["endpoints"]["status"], str)
            assert isinstance(payload["endpoints"]["packages"], str)
            assert isinstance(payload["endpoints"]["intents"], str)
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


def public_index_receipt_test_package(
    *,
    validation: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "package_id": "document_conversion.email_tools",
        "version": "0.1.0",
        "accepted_source": {
            "kind": "local_path",
            "path": "examples/email_tools",
        },
        "source": {
            "url": (
                "https://registry.example.invalid/v0/packages/"
                "document_conversion.email_tools/versions/0.1.0/"
                "document_conversion.email_tools-0.1.0.specpm.tgz"
            ),
            "digest": {
                "algorithm": "sha256",
                "value": "a" * 64,
            },
            "size": 123,
        },
        "validation": validation
        or {
            "status": "valid",
            "warnings": [],
            "errors": [],
        },
        "state": state
        or {
            "yanked": False,
            "deprecated": False,
        },
    }


def write_fake_specnode_checkout(checkout: Path) -> None:
    checkout.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "examples/email_tools", checkout)
    update_email_package(
        checkout,
        package_id="specnode.core",
        package_name="SpecNode",
        capability_id="specnode.typed_job_protocol",
    )


def write_fake_specpm_release_checkout(checkout: Path) -> None:
    checkout.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "examples/email_tools", checkout)
    update_email_package(
        checkout,
        package_id="specpm.core",
        package_name="SpecPM",
        version="0.1.0",
        capability_id="specpm.registry.public_alpha_index",
    )


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


def test_public_index_submission_entrypoints_are_user_visible() -> None:
    landing = LANDING_PAGE.read_text(encoding="utf-8")
    registry_viewer = REGISTRY_VIEWER_PAGE.read_text(encoding="utf-8")
    registry_viewer_design_css = REGISTRY_VIEWER_DESIGN_CSS.read_text(encoding="utf-8")
    registry_viewer_css = REGISTRY_VIEWER_CSS.read_text(encoding="utf-8")
    registry_viewer_js = REGISTRY_VIEWER_JS.read_text(encoding="utf-8")
    landing_version_js = (ROOT / "landing_page/assets/site-version.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    public_alpha = PUBLIC_ALPHA_DOC.read_text(encoding="utf-8")
    index_flow = (ROOT / "specs/INDEX_SUBMISSION_FLOW.md").read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    docc_add_package = DOCC_ADD_PACKAGE_PAGE.read_text(encoding="utf-8")
    docc_public_alpha = DOCC_PUBLIC_ALPHA_PAGE.read_text(encoding="utf-8")
    docc_static_pipeline = DOCC_STATIC_REGISTRY_PIPELINE_PAGE.read_text(encoding="utf-8")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for text in (landing, readme, public_alpha, index_flow, docc_add_package, docc_public_alpha):
        assert ADD_SPECPACKAGES_ISSUE_URL in text
        assert "public-index/accepted-packages.yml" in text

    assert 'href="#add-package"' in landing
    assert 'id="add-package"' in landing
    assert "Add SpecPackage(s)" in landing
    assert "Read Submission Guide" in landing
    assert (
        'href="https://0al-spec.github.io/SpecPM/documentation/specpm/" '
        'target="_blank" rel="noopener">Read Docs' in landing
    )
    assert (
        'href="https://0al-spec.github.io/SpecPM" target="_blank" rel="noopener">Read Docs'
        not in landing
    )
    assert "https://0al-spec.github.io/SpecPM/documentation/specpm/addspecpackage/" in (landing)
    assert "passing <code>specpm validate</code>" in landing
    assert "GitHub Actions validates each package" in landing
    assert "GitHub Pages republishes static registry metadata" in landing
    assert "https://0al-spec.github.io/SpecPM/viewer/" in landing
    assert "Provider-neutral contracts" in landing
    assert 'Define an abstract <span class="serif-name">SpecPackage</span>' in landing
    assert "explicit evidence and governance" in landing
    assert "abstract package type" not in landing.lower()
    assert "automatic conformance" not in landing.lower()
    assert "Live public registry viewer" in readme
    assert "https://0al-spec.github.io/SpecPM/viewer/" in readme
    assert '<link rel="stylesheet" href="./assets/specpm-design.css" />' in landing
    assert '<script src="./assets/site-version.js" defer></script>' in landing
    assert "data-specpm-version" in landing
    assert "data-specpm-build" in landing
    assert "data-specpm-revision" in landing
    assert "data-specpm-build-line" in landing
    assert "SpecPM v__SPECPM_VERSION__" in landing
    assert "Build __SPECPM_BUILD_NUMBER__" in landing
    assert "Revision __SPECPM_BUILD_REVISION_SHORT__" in landing
    assert "./v0/status/index.json" in landing_version_js
    assert "payload?.registry?.implementation" in landing_version_js
    assert '<link rel="stylesheet" href="./assets/specpm-design.css" />' in registry_viewer
    assert '<link rel="stylesheet" href="./assets/viewer.css" />' in registry_viewer
    assert '<script src="./assets/viewer.js" defer></script>' in registry_viewer
    assert "viewer-build-badge" in registry_viewer
    assert "viewer-build-line" in registry_viewer
    assert "Static Registry Viewer" in registry_viewer
    assert "SpecPM Registry Viewer" in registry_viewer
    assert "Registry Tree" in registry_viewer
    assert "https://0al-spec.github.io/SpecPM/documentation/specpm/" in registry_viewer
    assert "Catalog Search" in registry_viewer
    assert "Search packages, intents, capabilities" in registry_viewer
    assert 'aria-label="Search packages, intents, capabilities"' in registry_viewer
    assert "Instrument Serif" in registry_viewer_design_css
    assert ".brand-mark" in registry_viewer_design_css
    assert ".json-panel" in registry_viewer_css
    assert ".route-template-form" in registry_viewer_css
    assert ".route-builder" in registry_viewer_css
    assert ".route-error" in registry_viewer_css
    assert ".tree-group" in registry_viewer_css
    assert ".catalog-grid" in registry_viewer_css
    assert (
        ".nav-inner {\n    display: flex;\n    padding: 16px 0;\n    flex-direction: column;"
        in (registry_viewer_css)
    )
    assert "routeTemplates" in registry_viewer_js
    assert "RemoteRouteTemplate" in registry_viewer_js
    assert "clearLoadedRegistryState" in registry_viewer_js
    assert "state.catalogItems" in registry_viewer_js
    assert "buildCatalogItems" in registry_viewer_js
    assert "searchText" in registry_viewer_js
    assert "RemoteRegistryLoadError" in registry_viewer_js
    assert 'url.protocol !== "http:" && url.protocol !== "https:"' in registry_viewer_js
    assert 'window.addEventListener("popstate"' in registry_viewer_js
    assert "history.pushState" in registry_viewer_js
    assert "history.replaceState" in registry_viewer_js
    assert "specpmViewerRoute" in registry_viewer_js
    assert "routeFromLocation" in registry_viewer_js
    assert "isRegistryTreeAction" in registry_viewer_js
    assert "scrollContentIntoView" in registry_viewer_js
    assert "registryImplementation" in registry_viewer_js
    assert "implementationVersionLabel" in registry_viewer_js
    assert "renderBuildMetadata" in registry_viewer_js
    assert 'window.matchMedia("(max-width: 1120px)")' in registry_viewer_js
    assert 'document.querySelector(".content")?.scrollIntoView' in registry_viewer_js
    assert '<span class="pill warn">Issue</span>' in registry_viewer_js
    assert 'data-action="route-template"' in registry_viewer_js
    assert 'data-route-template="${escapeAttr(state.routePrompt.kind)}"' in registry_viewer_js
    assert "GET /v0/packages/{package_id}/versions/{version}" in registry_viewer_js
    assert "GET /v0/capabilities/{capability_id}/packages" in registry_viewer_js
    assert "GET /v0/intents/{intent_id}/packages" in registry_viewer_js
    assert "Browse observed intents" in registry_viewer_js
    assert "catalogVisibleLimit" in registry_viewer_js
    assert "Narrow the search to see more" in registry_viewer_js
    assert 'new URL("../v0/", window.location.href)' in registry_viewer_js
    assert "https://0al-spec.github.io/SpecPM/v0/" in registry_viewer_js

    assert "<doc:AddSpecPackage>" in docc_overview
    assert "<doc:StaticRegistryPipeline>" in docc_overview
    assert "Submit public `SpecPackage` repositories" in docc_add_package
    assert "Package content cannot command the host." in docc_add_package
    assert "See <doc:AddSpecPackage>" in docc_public_alpha
    assert "See <doc:StaticRegistryPipeline>" in docc_add_package
    assert "See <doc:StaticRegistryPipeline>" in docc_public_alpha
    assert "GitHub Issue: Add SpecPackage(s)" in docc_static_pipeline
    assert "public-index/accepted-packages.yml" in docc_static_pipeline

    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "landing_page/index.html" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/AddSpecPackage.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/StaticRegistryPipeline.md" in evidence_paths


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
    assert ".github/workflows/namespace-claim-decision-report.yml" in policy_text
    assert "public-index/accepted-packages.yml" in policy_text
    assert "reviewed pull request" in policy_text
    assert "specpm publish" in policy_text
    assert "remote mutation api" in policy_text
    assert "authentication" in policy_text
    assert "enterprise namespace governance" in policy_text
    assert "package content execution" in policy_text


def test_public_index_operator_guide_documents_package_review_boundary() -> None:
    guide_text = PUBLIC_INDEX_OPERATOR_GUIDE.read_text(encoding="utf-8")
    guide_lower = guide_text.lower()
    guide_flat = guide_lower.replace("\n", " ")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index_flow = (ROOT / "specs/INDEX_SUBMISSION_FLOW.md").read_text(encoding="utf-8")
    add_spec_package = (ROOT / "Sources/SpecPM/Documentation.docc/AddSpecPackage.md").read_text(
        encoding="utf-8"
    )
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for label in (
        "package:under-review",
        "package:needs-fix",
        "package:validated",
        "package:accepted",
        "package:rejected",
        "package:blocked",
        "package:duplicate",
    ):
        assert label in guide_text

    assert "Acceptance Checklist" in guide_text
    assert "Label Transition Policy" in guide_text
    assert "Operator Flow" in guide_text
    assert "Helper Contract" in guide_text
    assert "validation report status is `valid`" in guide_text
    assert "`package:validated` means a candidate is reviewable" in guide_text
    assert "at most one terminal label" in guide_text
    assert "terminal labels are maintainer-only" in add_spec_package
    assert "Dry-run mode is the default review posture" in guide_text
    assert "reviewed accepted-manifest pull request" in guide_text
    assert "generated static registry evidence" in guide_text
    assert "Producer-Backed Candidate Bundle Intake" in guide_text
    assert "producer-receipt.json" in guide_text
    assert "validation-report.json" in guide_text
    assert "diagnostics.json" in guide_text
    assert "producer preflight report or command output" in guide_text
    assert "static viewer output or reviewer-accessible preview" in guide_text
    assert "public_index_acceptance" in guide_text
    assert "producer receipt" in guide_lower
    assert "not registry authority" in guide_lower
    assert "reviewed pull request" in guide_lower
    assert "must not decide acceptance" in guide_lower
    assert "must not apply terminal labels" in guide_lower
    assert "must not publish a package" in guide_flat
    assert "public-index/accepted-packages.yml" in guide_text
    assert ".github/workflows/package-submission-triage.yml" in guide_text
    assert "scripts/prepare_accepted_manifest_pr.py" in guide_text
    assert "--submission-report submission-report.json" in guide_text
    assert "--pr-body-output accepted-manifest-pr.md" in guide_text
    assert "Omitting `--apply` performs a dry-run report" in guide_text
    assert "specs/PUBLIC_INDEX_OPERATOR_GUIDE.md" in readme
    assert "specs/PUBLIC_INDEX_OPERATOR_GUIDE.md" in index_flow
    assert "`submission-report.json`" in index_flow
    assert "draft pull request body" in index_flow.replace("\n", " ")
    assert "Producer-backed submissions" in index_flow
    assert "SpecHarvester candidate bundles" in index_flow
    assert "producer-receipt.json" in index_flow
    assert "validation-report.json" in index_flow
    assert "diagnostics.json" in index_flow
    assert "producer preflight report" in index_flow
    assert "static viewer evidence" in index_flow

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    owned_binding_paths = {
        path
        for binding in boundary["implementationBindings"]
        for path in binding["files"].get("owned", [])
    }
    assert "specpm.registry.accepted_manifest_pr_helper" in manifest_capabilities
    assert "specpm.registry.accepted_manifest_pr_helper" in boundary_capabilities
    assert "specpm.registry.package_set_materialization_helper" in manifest_capabilities
    assert "specpm.registry.package_set_materialization_helper" in boundary_capabilities
    assert "scripts/prepare_accepted_manifest_pr.py" in evidence_paths
    assert "scripts/prepare_accepted_manifest_pr.py" in owned_binding_paths


def test_downstream_registry_consumer_guide_documents_read_only_consumption() -> None:
    guide_text = DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.read_text(encoding="utf-8")
    guide_lower = guide_text.lower()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docc_page = (
        ROOT / "Sources/SpecPM/Documentation.docc/DownstreamRegistryConsumers.md"
    ).read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    docc_integration = DOCC_SPECGRAPH_INTEGRATION_PAGE.read_text(encoding="utf-8")
    docc_reports = DOCC_REGISTRY_OBSERVATION_REPORTS_PAGE.read_text(encoding="utf-8")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for endpoint in (
        "GET /v0/status",
        "GET /v0/packages",
        "GET /v0/packages/{package_id}",
        "GET /v0/packages/{package_id}/versions/{version}",
        "GET /v0/intents",
        "GET /v0/intents/{intent_id}",
        "GET /v0/intents/{intent_id}/packages",
        "GET /v0/capabilities/{capability_id}/packages",
    ):
        assert endpoint in guide_text

    for consumer in ("SpecGraph", "ContextBuilder", "SpecNode"):
        assert consumer in guide_text

    assert "specpm.registry/v0" in guide_text
    assert "specpm.dev/v0.1" in guide_text
    assert "Normative Endpoint Classes" in guide_text
    assert "Minimum Evidence Envelope" in guide_text
    assert "Failure Semantics" in guide_text
    assert '"observedAt": "2026-06-01T00:00:00Z"' in guide_text
    assert '"httpStatus": 200' in guide_text
    assert "unsupported_api_version" in guide_text
    assert "malformed_payload" in guide_text
    assert "missing_subject" in guide_text
    assert "lifecycle_blocked" in guide_text
    assert "SpecPM owns the registry metadata shape" in guide_text
    assert "Downstream consumers own policy" in guide_text
    assert "remote observe" in guide_text
    assert "specnode.typed_job_protocol" in guide_text
    assert "read-only" in guide_lower
    assert "should not execute package content" in guide_lower
    assert "semantic search" in guide_lower
    assert "endpoint classes, minimum evidence fields" in readme
    assert "specs/DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.md" in readme
    assert "specs/DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.md" in docc_page
    assert "observed timestamp, HTTP response status" in docc_page
    assert "<doc:DownstreamRegistryConsumers>" in docc_overview
    assert "<doc:DownstreamRegistryConsumers>" in docc_integration
    assert "<doc:DownstreamRegistryConsumers>" in docc_reports

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    owned_binding_paths = {
        path
        for binding in boundary["implementationBindings"]
        for path in binding["files"].get("owned", [])
    }
    assert "specpm.registry.downstream_consumer_contract" in manifest_capabilities
    assert "specpm.registry.downstream_consumer_contract" in boundary_capabilities
    assert "specs/DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/DownstreamRegistryConsumers.md" in evidence_paths
    assert "specs/DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.md" in owned_binding_paths


def test_specgraph_registry_observation_contract_documents_evidence_boundary() -> None:
    contract = SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.read_text(encoding="utf-8")
    consumer_guide = DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.read_text(encoding="utf-8")
    docc_page = DOCC_SPECGRAPH_REGISTRY_OBSERVATION_PAGE.read_text(encoding="utf-8")
    docc_integration = DOCC_SPECGRAPH_INTEGRATION_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")
    contract_flat = contract.replace("\n", " ")

    expected_endpoints = {
        "GET /v0/status",
        "GET /v0/packages",
        "GET /v0/packages/{package_id}",
        "GET /v0/packages/{package_id}/versions/{version}",
        "GET /v0/capabilities/{capability_id}/packages",
        "GET /v0/intents/{intent_id}",
        "GET /v0/intents/{intent_id}/packages",
    }
    endpoint_pattern = re.compile(r"`(GET /v0/[A-Za-z0-9_{}./-]+)`")
    contract_endpoints = set(endpoint_pattern.findall(contract))
    docc_endpoints = set(endpoint_pattern.findall(docc_page))
    assert expected_endpoints.issubset(contract_endpoints)
    assert expected_endpoints.issubset(docc_endpoints)

    for status in (
        "visible",
        "missing",
        "yanked",
        "deprecated",
        "drift",
        "unavailable",
        "inconclusive",
    ):
        assert f"`{status}`" in contract
        assert f"`{status}`" in docc_page

    for boundary_text in (
        "SpecPM remains the metadata substrate",
        "SpecGraph remains responsible for graph reasoning",
        "does not add a new registry endpoint",
        "`specpm publish`",
        "Observed intent IDs are metadata observations",
    ):
        assert boundary_text in contract_flat

    assert "specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md" in consumer_guide
    assert "specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md" in readme
    assert "<doc:SpecGraphRegistryObservation>" in docc_integration
    assert "<doc:SpecGraphRegistryObservation>" in docc_overview

    allowed_statuses = {
        "visible",
        "missing",
        "yanked",
        "deprecated",
        "drift",
        "unavailable",
        "inconclusive",
    }
    fixture_statuses: set[str] = set()
    for fixture_name in ("package-visible.json", "package-drift.json"):
        payload = json.loads(
            (SPECGRAPH_REGISTRY_OBSERVATION_FIXTURES / fixture_name).read_text(encoding="utf-8")
        )
        assert payload["schemaVersion"] == 1
        assert payload["kind"] == "SpecGraphRegistryObservation"
        assert payload["registry"]["apiVersion"] == "specpm.registry/v0"
        evidence_ids = {item["id"] for item in payload["evidence"]}
        evidence_endpoints = {item["endpoint"] for item in payload["evidence"]}
        assert evidence_ids
        if fixture_name == "package-visible.json":
            assert expected_endpoints.issubset(evidence_endpoints)
        for finding in payload["findings"]:
            fixture_statuses.add(finding["status"])
            assert finding["status"] in allowed_statuses
            assert set(finding["evidence"]).issubset(evidence_ids)
    assert {"visible", "missing", "drift"}.issubset(fixture_statuses)

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    owned_binding_paths = {
        path
        for binding in boundary["implementationBindings"]
        for path in binding["files"].get("owned", [])
    }
    assert "specpm.registry.specgraph_observation_contract" in manifest_capabilities
    assert "specpm.registry.specgraph_observation_contract" in boundary_capabilities
    assert "specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md" in evidence_paths
    assert "tests/fixtures/specgraph_registry_observation" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/SpecGraphRegistryObservation.md" in evidence_paths
    assert "specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md" in owned_binding_paths
    assert "tests/fixtures/specgraph_registry_observation" in owned_binding_paths


def test_registry_observation_reports_are_reusable_review_artifacts() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    report_doc = REGISTRY_OBSERVATION_REPORTS_DOC.read_text(encoding="utf-8")
    docc_page = DOCC_REGISTRY_OBSERVATION_REPORTS_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    json_contracts = (ROOT / "specs/JSON_CONTRACTS.md").read_text(encoding="utf-8")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for text in (report_doc, docc_page, readme):
        assert "make public-index-observation-report" in text
        assert "make pages-observation-report" in text
        assert ".specpm/registry-observations" in text

    for expected in (
        "local-public-index-observation.json",
        "pages-public-index-observation.json",
        "specpm.core",
        "specnode.core",
        "specpm.registry.public_alpha_index",
        "specnode.typed_job_protocol",
        "intent.registry.intent_lookup",
        "intent.document_conversion.email_to_markdown",
    ):
        assert expected in report_doc

    assert "do not commit routine report output" in report_doc
    assert "diff -u" in report_doc
    assert "package, version, capability, and intent visibility" in report_doc
    assert "--intent <intent-id>" in json_contracts
    assert "intent_ids: string[]" in json_contracts
    assert "intents: object" in json_contracts
    assert "intent_count: number | null" in json_contracts
    assert "<doc:RegistryObservationReports>" in docc_overview

    public_index_report_recipe = make_target_recipe(makefile, "public-index-observation-report")
    pages_report_recipe = make_target_recipe(makefile, "pages-observation-report")
    assert "remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS)" in public_index_report_recipe
    assert "remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS)" in pages_report_recipe
    assert "--intent intent.registry.intent_lookup" in makefile
    assert "--intent $(PUBLIC_INDEX_SMOKE_INTENT)" in makefile

    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    owned_binding_paths = {
        path
        for binding in boundary["implementationBindings"]
        for path in binding["files"].get("owned", [])
    }
    assert "specs/REGISTRY_OBSERVATION_REPORTS.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/RegistryObservationReports.md" in evidence_paths
    assert "specs/REGISTRY_OBSERVATION_REPORTS.md" in owned_binding_paths
    assert "Sources/SpecPM/Documentation.docc/RegistryObservationReports.md" in owned_binding_paths


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


def test_package_submission_triage_workflow_applies_review_labels_only() -> None:
    loaded = load_yaml_file(PACKAGE_SUBMISSION_TRIAGE_WORKFLOW)

    assert loaded["name"] == "Package Submission Triage"
    assert loaded["permissions"] == {"contents": "read", "issues": "write"}
    assert loaded["on"]["issues"]["types"] == ["opened", "edited", "reopened", "labeled"]

    job = loaded["jobs"]["triage-submission"]
    assert "package-submission" in job["if"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    script = steps["Prepare package submission review labels"]["with"]["script"]

    for status_label in (
        "package:needs-fix",
        "package:under-review",
        "package:validated",
        "package:accepted",
        "package:rejected",
        "package:blocked",
        "package:duplicate",
    ):
        assert status_label in script

    assert "issues.createLabel" in script
    assert "createError.status !== 422" in script
    assert "issues.addLabels" in script
    assert "package:under-review" in script
    assert "Public Index Operator Guide" in script
    assert "github.rest.repos.get" in script
    assert "repository.default_branch" in script
    assert "context.serverUrl" in script
    assert "package-submission-triage" in script
    assert 'comment.user?.login === "github-actions[bot]"' in script
    assert "let page = 1" in script
    assert "comments.length < 100" in script
    assert "does not decide acceptance" in script
    assert "public-index/accepted-packages.yml" in script
    for forbidden in ("public-index generate", "validate_index_submission.py", "specpm publish"):
        assert forbidden not in script


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
    assert "createError.status !== 422" in script
    assert "github.rest.repos.get" in script
    assert "repository.default_branch" in script
    assert "policyUrl" in script
    assert "listComments" in script
    assert "page += 1" in script
    assert 'comment.user?.login === "github-actions[bot]"' in script
    assert "updateComment" in script
    assert "createComment" in script
    assert "does not grant namespace ownership" in script
    assert "public-index/accepted-packages.yml" in script
    for forbidden in ("specpm publish", "public-index generate", "validate_index_submission.py"):
        assert forbidden not in script


def test_namespace_claim_decision_report_workflow_is_report_only() -> None:
    loaded = load_yaml_file(NAMESPACE_CLAIM_DECISION_REPORT_WORKFLOW)

    assert loaded["name"] == "Namespace Claim Decision Report"
    assert loaded["permissions"] == {"contents": "read", "issues": "write"}
    assert loaded["on"]["issues"]["types"] == [
        "opened",
        "edited",
        "reopened",
        "labeled",
        "unlabeled",
    ]

    job = loaded["jobs"]["report-namespace-claim-decision"]
    assert "namespace-claim" in job["if"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    assert "Report namespace claim decision label" in steps

    script = steps["Report namespace claim decision label"]["with"]["script"]
    for decision_label in (
        "namespace:accepted",
        "namespace:rejected",
        "namespace:contested",
        "namespace:superseded",
    ):
        assert decision_label in script
    assert "namespace-claim-decision-report" in script
    assert "No namespace claim decision label is present" in script
    assert "No namespace claim decision label is currently present" in script
    assert "activeDecisionLabels.length === 0 && !existingComment" in script
    assert "activeDecisionLabels.length > 1" in script
    assert "Multiple maintainer-applied decision labels are present" in script
    assert "exactly one terminal namespace decision label" in script
    assert "github.rest.repos.get" in script
    assert "repository.default_branch" in script
    assert "policyUrl" in script
    assert "listComments" in script
    assert "page += 1" in script
    assert 'comment.user?.login === "github-actions[bot]"' in script
    assert "updateComment" in script
    assert "createComment" in script
    assert "maintainer-applied issue label" in script
    assert "does not apply terminal decision labels by itself" in script
    assert "public-index/accepted-packages.yml" in script
    for forbidden in ("addLabels", "createLabel", "specpm publish", "public-index generate"):
        assert forbidden not in script


def test_namespace_claim_decision_summary_workflow_is_read_only() -> None:
    loaded = load_yaml_file(NAMESPACE_CLAIM_DECISION_SUMMARY_WORKFLOW)

    assert loaded["name"] == "Namespace Claim Decision Summary"
    assert loaded["permissions"] == {"contents": "read", "issues": "read"}
    assert "workflow_dispatch" in loaded["on"]
    assert loaded["on"]["schedule"][0]["cron"] == "17 3 * * 1"

    job = loaded["jobs"]["summarize-namespace-claim-decisions"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    assert "Build namespace claim decision summary" in steps
    assert "Upload namespace claim decision summary" in steps

    script = steps["Build namespace claim decision summary"]["with"]["script"]
    for decision_label in (
        "namespace:accepted",
        "namespace:rejected",
        "namespace:contested",
        "namespace:superseded",
    ):
        assert decision_label in script
    assert "github.rest.search.issuesAndPullRequests" in script
    assert 'label:"namespace-claim"' in script
    assert 'label:"${label}"' in script
    assert "const searchPageLimit = 10" in script
    assert "data.total_count" in script
    assert "search_warnings" in script
    assert "search_metadata" in script
    assert "truncated" in script
    assert "inclusive_search_counts" in script
    assert "active_decision_labels" in script
    assert "Unambiguous issues" in script
    assert "ambiguous_count" in script
    assert "namespace-claim-decision-summary.json" in script
    assert "namespace-claim-decision-summary.md" in script
    assert "core.summary.addRaw" in script
    assert "This summary is read-only" in script
    assert "public-index/accepted-packages.yml" in script

    upload = steps["Upload namespace claim decision summary"]
    assert upload["uses"] == "actions/upload-artifact@v7"
    assert upload["with"]["name"] == "namespace-claim-decision-summary"

    for forbidden in (
        "addLabels",
        "createLabel",
        "createComment",
        "updateComment",
        "specpm publish",
        "public-index generate",
    ):
        assert forbidden not in script


def test_github_workflows_use_node24_action_generations() -> None:
    action_ref_pattern = re.compile(r"uses:\s*[\"']?(actions/[-\w]+)@v(\d+)(?:\.\d+){0,2}[\"']?")
    assert action_ref_pattern.findall('uses: "actions/checkout@v6.0.2"') == [
        ("actions/checkout", "6")
    ]
    assert action_ref_pattern.findall("uses: 'actions/setup-python@v6'") == [
        ("actions/setup-python", "6")
    ]

    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    )
    action_refs = action_ref_pattern.findall(workflow_text)

    minimum_major_by_action = {
        "actions/checkout": 6,
        "actions/setup-python": 6,
        "actions/upload-artifact": 7,
        "actions/download-artifact": 8,
        "actions/upload-pages-artifact": 5,
        "actions/deploy-pages": 5,
        "actions/github-script": 9,
    }

    for action, minimum_major in minimum_major_by_action.items():
        observed_majors = {
            int(major) for observed_action, major in action_refs if observed_action == action
        }
        if not observed_majors:
            continue
        assert min(observed_majors) >= minimum_major, (
            f"{action} uses majors {sorted(observed_majors)}, expected >= v{minimum_major}"
        )


def test_github_actions_maintenance_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    policy = GITHUB_ACTIONS_MAINTENANCE_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_GITHUB_ACTIONS_MAINTENANCE_PAGE.read_text(encoding="utf-8")
    docc_deployment = DOCC_DEPLOYMENT_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    required_actions = (
        "actions/checkout",
        "actions/setup-python",
        "actions/upload-artifact",
        "actions/download-artifact",
        "actions/upload-pages-artifact",
        "actions/deploy-pages",
        "actions/github-script",
    )
    for action in required_actions:
        assert action in policy

    for required_text in (
        "Node.js 20 actions are deprecated",
        "`pull_request_target`",
        "first `main` run after merge",
        "tests/test_core.py",
        "full semantic version",
        "third-party actions",
        "not define SpecPM package versioning",
    ):
        assert required_text in policy

    assert "specs/GITHUB_ACTIONS_MAINTENANCE.md" in readme
    assert "specs/GITHUB_ACTIONS_MAINTENANCE.md" in docc_overview
    assert "<doc:GitHubActionsMaintenance>" in docc_overview
    assert "<doc:GitHubActionsMaintenance>" in docc_deployment
    assert "pull_request_target" in docc_policy

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.deployment.github_actions_maintenance_policy" in manifest_capabilities
    assert "specpm.deployment.github_actions_maintenance_policy" in boundary_capabilities
    assert "specs/GITHUB_ACTIONS_MAINTENANCE.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/GitHubActionsMaintenance.md" in evidence_paths


def test_github_actions_permissions_and_secrets_boundary_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    policy = GITHUB_ACTIONS_PERMISSIONS_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_GITHUB_ACTIONS_PERMISSIONS_PAGE.read_text(encoding="utf-8")
    docc_maintenance = DOCC_GITHUB_ACTIONS_MAINTENANCE_PAGE.read_text(encoding="utf-8")
    docc_deployment = DOCC_DEPLOYMENT_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    workflow_permissions = {
        ROOT / ".github/workflows/ci.yml": {"contents": "read"},
        DOCS_WORKFLOW: {"contents": "read"},
        DEPLOY_CONNECTION_CHECK_WORKFLOW: {"contents": "read"},
        PACKAGE_SUBMISSION_WORKFLOW: {"contents": "read", "issues": "write"},
        PACKAGE_SUBMISSION_TRIAGE_WORKFLOW: {"contents": "read", "issues": "write"},
        PRODUCER_BUNDLE_PREFLIGHT_WORKFLOW: {"contents": "read"},
        NAMESPACE_CLAIM_TRIAGE_WORKFLOW: {"contents": "read", "issues": "write"},
        NAMESPACE_CLAIM_DECISION_REPORT_WORKFLOW: {"contents": "read", "issues": "write"},
        NAMESPACE_CLAIM_DECISION_SUMMARY_WORKFLOW: {"contents": "read", "issues": "read"},
    }
    for workflow_path, expected_permissions in workflow_permissions.items():
        loaded = load_yaml_file(workflow_path)
        assert loaded.get("permissions") == expected_permissions
        assert f"`{workflow_path.relative_to(ROOT)}`" in policy

    docs_workflow = load_yaml_file(DOCS_WORKFLOW)
    assert docs_workflow["jobs"]["deploy"]["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }
    assert "pages: write" in policy
    assert "id-token: write" in policy

    static_host_job = docs_workflow["jobs"]["deploy-static-host"]
    static_host_steps = {step["name"]: step for step in static_host_job["steps"] if "name" in step}
    static_host_summary = static_host_steps["Summarize static host artifact"]["run"]
    static_host_upload = static_host_steps["Upload to SpecPM.dev over SFTP"]
    upload_script = static_host_upload["run"]
    assert static_host_job["timeout-minutes"] == 30
    assert static_host_upload["timeout-minutes"] == 25
    assert "wc -l < /tmp/specpm-static-site-files.txt" in static_host_summary
    assert "du -sb specpm-static-site" in static_host_summary
    assert "Largest static host files:" in static_host_summary
    assert "sort -nr > /tmp/specpm-static-site-largest-files.txt" in static_host_summary
    assert "head -20 /tmp/specpm-static-site-largest-files.txt" in static_host_summary
    assert "Uploading $FILE_COUNT files ($BYTE_SIZE bytes)" in upload_script
    assert "timeout --kill-after=30s 18m lftp" in upload_script
    assert "set cmd:trace yes" in upload_script
    assert "set xfer:log yes" in upload_script
    assert 'set xfer:log-file "$TRANSFER_LOG"' in upload_script
    assert "mirror -R --verbose=2" in upload_script
    assert "SFTP upload exited with status $UPLOAD_STATUS" in upload_script
    assert 'tail -40 "$TRANSFER_LOG"' in upload_script

    ftp_secrets = {"FTP_HOST", "FTP_PORT", "FTP_USER", "FTP_PASS", "FTP_REMOTE_ROOT"}
    secret_ref_pattern = re.compile(
        r"\${{\s*secrets(?:\.([A-Z0-9_]+)|\[\s*[\"']([A-Z0-9_]+)[\"']\s*\])\s*}}"
    )
    for workflow_path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        observed_secrets = set()
        for match in secret_ref_pattern.findall(workflow_path.read_text(encoding="utf-8")):
            observed_secrets.add(next(part for part in match if part))
        expected_secrets = (
            ftp_secrets
            if workflow_path in {DOCS_WORKFLOW, DEPLOY_CONNECTION_CHECK_WORKFLOW}
            else set()
        )
        assert observed_secrets == expected_secrets

    for secret_name in ftp_secrets:
        assert secret_name in policy
        assert secret_name in docc_policy

    pull_request_target_workflows = []
    for workflow_path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        loaded = load_yaml_file(workflow_path)
        trigger = loaded.get("on") or loaded.get(True)
        if isinstance(trigger, dict) and "pull_request_target" in trigger:
            pull_request_target_workflows.append(workflow_path)
    assert pull_request_target_workflows == [DEPLOY_CONNECTION_CHECK_WORKFLOW]

    connection_check = load_yaml_file(DEPLOY_CONNECTION_CHECK_WORKFLOW)
    job = connection_check["jobs"]["deploy-connection-check"]
    assert job["if"] == "github.event.pull_request.head.repo.full_name == github.repository"
    checkout_step = {step["name"]: step for step in job["steps"] if "name" in step}[
        "Checkout trusted workflow"
    ]
    assert checkout_step["with"]["ref"] == "${{ github.event.pull_request.base.sha }}"

    for required_text in (
        "No repository or environment secrets",
        "Pull request checks are build and policy evidence",
        "`pull_request_target` workflows must not execute pull request head code",
        "read-only SFTP directory listing",
        "GitHub Pages: the first successful `main` documentation deploy run",
        "file count and byte size",
        "explicit wall-clock timeout",
        "recent transfer log entries",
    ):
        assert required_text in policy

    assert "specs/GITHUB_ACTIONS_PERMISSIONS.md" in readme
    assert "specs/GITHUB_ACTIONS_PERMISSIONS.md" in docc_overview
    assert "<doc:GitHubActionsPermissions>" in docc_overview
    assert "<doc:GitHubActionsPermissions>" in docc_deployment
    assert "<doc:GitHubActionsPermissions>" in docc_maintenance
    assert "pull_request_target" in docc_policy
    assert "safe deployment diagnostics" in docc_policy

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    constraint_ids = {constraint["id"] for constraint in boundary["constraints"]}
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.deployment.github_actions_permissions_policy" in manifest_capabilities
    assert "specpm.deployment.github_actions_permissions_policy" in boundary_capabilities
    assert "github_actions_least_privilege" in constraint_ids
    assert "specs/GITHUB_ACTIONS_PERMISSIONS.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/GitHubActionsPermissions.md" in evidence_paths


def test_producer_bundle_preflight_workflow_is_read_only_and_evidence_scoped() -> None:
    loaded = load_yaml_file(PRODUCER_BUNDLE_PREFLIGHT_WORKFLOW)
    trigger = loaded.get("on") or loaded.get(True)
    assert "pull_request" in trigger
    assert "pull_request_target" not in trigger
    assert loaded["permissions"] == {"contents": "read"}

    job = loaded["jobs"]["producer-bundle-preflight"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    proposal_script = steps["Write pull request body"]["run"]
    preflight_script = steps["Preflight producer bundle evidence"]["run"]

    assert "producerEvidenceLinks" in proposal_script
    assert "registryAcceptanceDecision" in proposal_script
    assert "json.loads" in proposal_script
    assert "```json" in proposal_script
    assert "RUNNER_TEMP" in proposal_script
    assert "should_run" in proposal_script
    assert "false" in proposal_script
    assert steps["Check out pull request"]["uses"] == "actions/checkout@v6"
    assert steps["Set up Python"]["uses"] == "actions/setup-python@v6"
    assert "producer-bundle preflight" in preflight_script
    assert "steps.proposal.outputs.body_path" in preflight_script
    assert '--root "$GITHUB_WORKSPACE"' in preflight_script
    assert "--json" in preflight_script


def test_remote_package_acquisition_boundary_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    policy = REMOTE_PACKAGE_ACQUISITION_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_REMOTE_PACKAGE_ACQUISITION_PAGE.read_text(encoding="utf-8")
    docc_deployment = DOCC_DEPLOYMENT_PAGE.read_text(encoding="utf-8")
    docc_registry_operations = DOCC_REGISTRY_OPERATIONS_PAGE.read_text(encoding="utf-8")
    docc_roadmap = DOCC_ROADMAP_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for required_text in (
        "`specpm remote ...` reads `/v0` metadata",
        "metadata evidence",
        "Remote acquisition must not treat mutable labels as trust roots",
        "digest mismatch",
        "cache collision",
        "yanked package version",
        "mutable source reference without an exact revision",
        "content-addressed layout",
        "Acquisition State Machine",
        "`observed_metadata`",
        "`verified_archive`",
        "`locked_package`",
        "Cache and lock writes must be atomic",
        "Digest verification is required for acquisition, but it proves only byte",
        "Retry and Partial Write Behavior",
        "`trust_policy_unmet`",
        "`partial_write_recovered`",
        "Never execute package content",
        "Package content can describe desired outputs.",
        "Package content cannot command",
    ):
        assert required_text in policy

    for required_text in (
        "does not currently install or fetch remote package archives",
        "Mutable labels are not trust roots",
        "digest verification before cache or lock writes",
        "Package content remains untrusted data",
        "`observed_metadata`",
        "`locked_package`",
        "Digest verification proves bytes, not publisher authority",
        "partial-write recovery",
    ):
        assert required_text in docc_policy

    assert "specs/REMOTE_PACKAGE_ACQUISITION.md" in readme
    assert "specs/REMOTE_PACKAGE_ACQUISITION.md" in docc_overview
    assert "<doc:RemotePackageAcquisition>" in docc_overview
    assert "<doc:RemotePackageAcquisition>" in docc_deployment
    assert "<doc:RemotePackageAcquisition>" in docc_registry_operations
    assert "<doc:RemotePackageAcquisition>" in docc_roadmap
    assert "<doc:PackageSigningRevocation>" in docc_policy
    assert "remote package acquisition boundary" in roadmap
    assert "remote package acquisition boundary" in docc_roadmap
    assert "Remote package acquisition design invariants are now documented" in roadmap
    assert "Remote package acquisition design invariants are now documented" in docc_roadmap
    assert "- [x] Separate registry metadata lookup from archive acquisition." in workplan
    assert "- [x] Preserve the rule that package content is never executed during" in workplan
    assert "Phase 62. Remote Package Acquisition Design Invariants" in workplan
    assert "- [x] Define explicit acquisition states from `observed_metadata` through" in workplan

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    constraint_ids = {constraint["id"] for constraint in boundary["constraints"]}
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.registry.remote_package_acquisition_policy" in manifest_capabilities
    assert "specpm.registry.remote_package_acquisition_policy" in boundary_capabilities
    assert "remote_acquisition_fail_closed" in constraint_ids
    assert "specs/REMOTE_PACKAGE_ACQUISITION.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/RemotePackageAcquisition.md" in evidence_paths


def test_package_signing_revocation_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    policy = PACKAGE_SIGNING_REVOCATION_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_PACKAGE_SIGNING_REVOCATION_PAGE.read_text(encoding="utf-8")
    docc_receipts = DOCC_PROVENANCE_RECEIPTS_PAGE.read_text(encoding="utf-8")
    docc_registry_operations = DOCC_REGISTRY_OPERATIONS_PAGE.read_text(encoding="utf-8")
    docc_remote_acquisition = DOCC_REMOTE_PACKAGE_ACQUISITION_PAGE.read_text(encoding="utf-8")
    docc_roadmap = DOCC_ROADMAP_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for required_text in (
        "Current SpecPM does not verify package signatures",
        "Digest verification proves bytes, not publisher authority",
        "package ID",
        "package version",
        "archive digest algorithm and value",
        "issuer identity or public key identity",
        "Verification runtime must fail closed",
        "Revocation is a policy decision, not deletion",
        "`deprecated`: visible and usually eligible",
        "`yanked`: visible for audit and reproducibility",
        "`revoked`: cryptographic or governance trust is withdrawn",
        "No private keys, signing tokens, recovery codes, or credential material",
        "Package content can describe desired outputs. Package content cannot command the",
    ):
        assert required_text in policy

    for required_text in (
        "does not verify package signatures",
        "Digest verification proves bytes, not publisher authority",
        "Verification runtime must fail closed",
        "Revocation is a policy decision, not deletion",
        "`visible`, `deprecated`, `yanked`,",
        "Future provenance receipts should record package ID and version",
    ):
        assert required_text in docc_policy

    assert "specs/PACKAGE_SIGNING_REVOCATION.md" in readme
    assert "specs/PACKAGE_SIGNING_REVOCATION.md" in docc_overview
    assert "<doc:PackageSigningRevocation>" in docc_overview
    assert "<doc:PackageSigningRevocation>" in docc_registry_operations
    assert "<doc:PackageSigningRevocation>" in docc_remote_acquisition
    assert "<doc:PackageSigningRevocation>" in docc_roadmap
    assert "<doc:ProvenanceReceipts>" in docc_policy
    assert "specs/PROVENANCE_RECEIPTS.md" in docc_receipts
    assert "Package signing and revocation policy is now documented" in roadmap
    assert "Package signing and revocation policy is now documented" in docc_roadmap
    assert "Provenance receipt schema and audit evidence profile" in roadmap
    assert "SpecPMProvenanceReceipt" in docc_roadmap

    for checked_item in (
        "- [x] Document that current SpecPM does not verify package signatures",
        "- [x] Separate archive digest verification from publisher authority.",
        "- [x] Define the minimum future signature subject for package ID, version,",
        "- [x] Define fail-closed verification behavior when a trust policy requires a",
        "- [x] Document revocation, yanked, deprecated, removed, and visible lifecycle",
        "- [x] Define stronger provenance receipt expectations without choosing a storage",
        "- [x] Keep runtime signature verification, key management, revocation feed",
    ):
        assert checked_item in workplan

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    constraint_ids = {constraint["id"] for constraint in boundary["constraints"]}
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.registry.package_signing_revocation_policy" in manifest_capabilities
    assert "specpm.registry.package_signing_revocation_policy" in boundary_capabilities
    assert "package_trust_policy_no_runtime_enforcement" in constraint_ids
    assert "specs/PACKAGE_SIGNING_REVOCATION.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/PackageSigningRevocation.md" in evidence_paths


def test_provenance_receipt_schema_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    policy = PROVENANCE_RECEIPTS_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_PROVENANCE_RECEIPTS_PAGE.read_text(encoding="utf-8")
    docc_signing = DOCC_PACKAGE_SIGNING_REVOCATION_PAGE.read_text(encoding="utf-8")
    docc_roadmap = DOCC_ROADMAP_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    receipt_fixture = json.loads(PROVENANCE_RECEIPT_FIXTURE.read_text(encoding="utf-8"))
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for required_text in (
        "SpecPMProvenanceReceipt",
        "Receipts are evidence, not authority",
        "Current SpecPM generates non-authoritative provenance receipt artifacts",
        "apiVersion: specpm.receipts/v0",
        "receiptProfile: public_static_index_build_v0",
        "subject",
        "source",
        "archive",
        "review",
        "build",
        "validation",
        "trust",
        "lifecycle",
        "audit",
        "Absence of a receipt means no receipt evidence is available",
        "must not be used as trust evidence",
    ):
        assert required_text in policy

    for required_text in (
        "Receipts are evidence, not authority",
        "apiVersion: specpm.receipts/v0",
        "kind: SpecPMProvenanceReceipt",
        "public_static_index_build_v0",
        "Current SpecPM generates non-authoritative provenance receipt artifacts",
    ):
        assert required_text in docc_policy

    assert "specs/PROVENANCE_RECEIPTS.md" in readme
    assert "specs/PROVENANCE_RECEIPTS.md" in docc_overview
    assert "<doc:ProvenanceReceipts>" in docc_overview
    assert "<doc:ProvenanceReceipts>" in docc_signing
    assert "<doc:ProvenanceReceipts>" in docc_roadmap
    assert "Provenance receipt schema and audit evidence profile" in roadmap
    assert "Provenance receipt schema and audit evidence profile" in docc_roadmap
    assert "implementation: public static provenance receipt artifacts" in roadmap
    assert "public static provenance receipt JSON artifacts" in docc_roadmap

    assert receipt_fixture["apiVersion"] == "specpm.receipts/v0"
    assert receipt_fixture["kind"] == "SpecPMProvenanceReceipt"
    assert receipt_fixture["schemaVersion"] == 1
    assert receipt_fixture["receiptProfile"] == "public_static_index_build_v0"
    assert receipt_fixture["subject"]["registryProfile"] == "public_static_index"
    assert receipt_fixture["source"]["kind"] == "git"
    assert re.fullmatch(r"[0-9a-f]{40}", receipt_fixture["source"]["revision"])
    assert receipt_fixture["archive"]["format"] == "specpm-tar-gzip-v0"
    assert receipt_fixture["archive"]["digest"]["algorithm"] == "sha256"
    assert re.fullmatch(r"[0-9a-f]{64}", receipt_fixture["archive"]["digest"]["value"])
    assert receipt_fixture["review"]["kind"] == "pull_request"
    assert receipt_fixture["validation"]["status"] == "valid"
    assert receipt_fixture["trust"]["signatureRequired"] is False
    assert receipt_fixture["trust"]["signatureStatus"] == "not_applicable"
    assert receipt_fixture["lifecycle"]["state"] == "visible"
    assert isinstance(receipt_fixture["audit"]["evidence"], list)
    assert receipt_fixture["audit"]["evidence"]

    for checked_item in (
        "- [x] Document the draft `SpecPMProvenanceReceipt` envelope.",
        "- [x] Define the initial `public_static_index_build_v0` receipt profile.",
        "- [x] Specify required subject, source, archive, review, build, validation,",
        "- [x] Define extension rules for public and enterprise profiles.",
        "- [x] Document failure interpretation when future policy requires receipts.",
        "- [x] Add a non-normative machine-readable fixture for the receipt shape.",
        "- [x] Keep receipt verification, trust enforcement, lockfile changes,",
        "- [x] Generate non-authoritative `SpecPMProvenanceReceipt` JSON artifacts",
        "- [x] Add receipt descriptors to package version metadata",
    ):
        assert checked_item in workplan

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    constraint_ids = {constraint["id"] for constraint in boundary["constraints"]}
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.registry.provenance_receipt_schema" in manifest_capabilities
    assert "specpm.registry.public_index_provenance_receipts" in manifest_capabilities
    assert "specpm.registry.provenance_receipt_schema" in boundary_capabilities
    assert "specpm.registry.public_index_provenance_receipts" in boundary_capabilities
    assert "provenance_receipts_evidence_not_authority" in constraint_ids
    assert "specs/PROVENANCE_RECEIPTS.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/ProvenanceReceipts.md" in evidence_paths
    assert "tests/fixtures/provenance_receipts/public-static-receipt.example.json" in evidence_paths


def test_producer_receipt_contract_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    provenance_policy = PROVENANCE_RECEIPTS_DOC.read_text(encoding="utf-8")
    policy = PRODUCER_RECEIPTS_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_PRODUCER_RECEIPTS_PAGE.read_text(encoding="utf-8")
    proposal_policy = (ROOT / "specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md").read_text(
        encoding="utf-8"
    )
    docc_proposal_policy = DOCC_PRODUCER_BUNDLE_POLICY_PAGE.read_text(encoding="utf-8")
    proposal_automation = PRODUCER_BUNDLE_PROPOSAL_AUTOMATION_DOC.read_text(encoding="utf-8")
    docc_proposal_automation = DOCC_PRODUCER_BUNDLE_PROPOSAL_AUTOMATION_PAGE.read_text(
        encoding="utf-8"
    )
    fixture_policy = PRODUCER_BUNDLE_FIXTURE_POLICY_DOC.read_text(encoding="utf-8")
    docc_fixture_policy = DOCC_PRODUCER_BUNDLE_FIXTURE_POLICY_PAGE.read_text(encoding="utf-8")
    acceptance_decisions = REGISTRY_ACCEPTANCE_DECISION_DOC.read_text(encoding="utf-8")
    docc_acceptance_decisions = DOCC_REGISTRY_ACCEPTANCE_DECISIONS_PAGE.read_text(encoding="utf-8")
    docc_receipts = DOCC_PROVENANCE_RECEIPTS_PAGE.read_text(encoding="utf-8")
    docc_roadmap = DOCC_ROADMAP_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    receipt_fixture = json.loads(PRODUCER_RECEIPT_FIXTURE.read_text(encoding="utf-8"))
    acceptance_decision_fixture = json.loads(
        REGISTRY_ACCEPTANCE_DECISION_FIXTURE.read_text(encoding="utf-8")
    )
    roadmap_flat = roadmap.replace("\n", " ")
    docc_roadmap_flat = docc_roadmap.replace("\n", " ")
    proposal_policy_flat = proposal_policy.replace("\n", " ")
    docc_proposal_automation_flat = docc_proposal_automation.replace("\n", " ")
    docc_proposal_policy_flat = docc_proposal_policy.replace("\n", " ")
    docc_fixture_policy_flat = docc_fixture_policy.replace("\n", " ")
    docc_acceptance_decisions_flat = docc_acceptance_decisions.replace("\n", " ")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for required_text in (
        "SpecPMProducerReceipt",
        "Producer receipts are evidence, not authority",
        "SpecHarvester",
        "tool-neutral",
        "apiVersion: specpm.receipts/v0",
        "receiptProfile: generated_spec_package_v0",
        "subject",
        "producer",
        "inputs",
        "configuration",
        "outputs",
        "validation",
        "diagnostics",
        "diagnostics: {}",
        "humanReview",
        "privacy",
        "audit",
        "producer-receipt.json",
        "validation-report.json",
        "diagnostics.json",
        "self-hash problem",
        "configuration.digest",
        "outputs[]",
        "humanReview.status: approved",
        "public_index_acceptance",
        "privacy.secretsIncluded",
        "specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md",
        "Current SpecPM does not generate, validate, require, or index producer",
        "must not be used as trust evidence",
    ):
        assert required_text in policy

    for required_text in (
        "SpecPMProducerReceipt",
        "generated_spec_package_v0",
        "SpecHarvester",
        "does not make generated content trusted",
        "producer-receipt.json",
        "configuration.digest",
        "humanReview.status: approved",
        "<doc:ProducerBundleProposalPolicy>",
        "Current SpecPM does not generate, validate, require, or index producer",
    ):
        assert required_text in docc_policy
    assert "diagnostics: {}" in docc_policy

    for required_text in (
        "Producer Candidate Bundle Proposal Policy",
        "SpecHarvester",
        "review evidence",
        "not registry authority",
        "Minimum Proposal Evidence",
        "Intake Checklist",
        "Reject Signals",
        "Warning Signals",
        "Maintainer Override",
        "producer-receipt.json",
        "validation-report.json",
        "diagnostics.json",
        "producer preflight report",
        "static viewer",
        "public_index_acceptance",
        "privacy.secretsIncluded",
        "producer receipts separate from registry authority",
        "specs/PUBLIC_INDEX_OPERATOR_GUIDE.md",
        "specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md",
        "specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md",
        "specs/REGISTRY_ACCEPTANCE_DECISIONS.md",
        "SpecHarvesterPackageSetHandoffProposal",
        "member manifest identity",
        "`contains` relation endpoints",
        "Package-Set AI Enrichment Evidence",
        "SpecHarvesterPackageSetAIEnrichmentProposal",
        "proposal_only_not_registry_acceptance",
        "automatic capability, intent, interface, or relation acceptance",
    ):
        assert required_text in proposal_policy_flat

    for required_text in (
        "Producer Bundle Proposal Policy",
        "SpecHarvester",
        "producer bundle evidence -> SpecPM proposal review -> maintainer decision",
        "not registry authority",
        "Minimum Evidence",
        "Intake Checklist",
        "Maintainer Override",
        "specs/PUBLIC_INDEX_OPERATOR_GUIDE.md",
        "<doc:ProducerBundleFixturePolicy>",
        "<doc:ProducerBundleProposalAutomation>",
        "<doc:RegistryAcceptanceDecisions>",
        "SpecHarvesterPackageSetHandoffProposal",
        "bundle-set preflight status/counts",
        "Package-Set AI Enrichment Evidence",
        "spec-harvester.package-set-ai-enrichment/v0",
        "proposal_only_not_registry_acceptance",
        "Provider receipts and usage metadata are provenance only",
    ):
        assert required_text in docc_proposal_policy_flat

    for required_text in (
        "Producer Bundle Proposal Automation Contract",
        "SpecHarvester-to-SpecPM pull request body contract",
        "producerEvidenceLinks",
        "registryAcceptanceDecision",
        "accepted_source_bundle",
        "boundary_spec",
        "producer_preflight",
        "static_viewer",
        "external_required",
        "public_index_acceptance",
        "producerReceiptAuthority",
        "evidence_only",
        "Producers must not set this status to `approved`",
        "specs/REGISTRY_ACCEPTANCE_DECISIONS.md",
        "include or link producer receipt, validation report, diagnostics report",
    ):
        assert required_text in proposal_automation
    minimal_proposal_section = proposal_automation.split("## Minimal Proposal Shape", 1)[1].split(
        "## Automation Expectations", 1
    )[0]
    assert '"producerEvidenceLinks"' in minimal_proposal_section
    assert '"registryAcceptanceDecision"' in minimal_proposal_section

    for required_text in (
        "Producer Bundle Proposal Automation",
        "producerEvidenceLinks",
        "registryAcceptanceDecision",
        "boundary_spec",
        "external_required",
        "producerReceiptAuthority",
        "evidence_only",
        "Maintainer review remains the registry acceptance authority",
        "<doc:RegistryAcceptanceDecisions>",
        "specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md",
    ):
        assert required_text in docc_proposal_automation_flat

    for required_text in (
        "Registry Acceptance Decisions",
        "SpecPMRegistryAcceptanceDecision",
        "specpm.decisions/v0",
        "producer evidence -> SpecPM maintainer review -> registry acceptance decision",
        "producer receipt -> automatic registry acceptance",
        "producerReceiptAuthority",
        "evidence_only",
        "approved",
        "rejected",
        "override",
        "withdrawn",
        "pending",
        "public_index_acceptance",
        "acceptedSourcePath",
        "make `producer-receipt.json` an authority document",
    ):
        assert required_text in acceptance_decisions

    for required_text in (
        "Registry Acceptance Decisions",
        "SpecPMRegistryAcceptanceDecision",
        "specpm.decisions/v0",
        "producer evidence -> SpecPM maintainer review -> registry acceptance decision",
        "producerReceiptAuthority",
        "evidence_only",
        "specs/REGISTRY_ACCEPTANCE_DECISIONS.md",
    ):
        assert required_text in docc_acceptance_decisions_flat

    for required_text in (
        "Producer Bundle Fixture Policy",
        "SpecPM contract examples",
        "SpecHarvester generated candidate bundle examples",
        "Neither repository should read the other repository's `main` branch",
        "Drift-Sensitive Fields",
        "producerEvidenceLinks[].role",
        "registryAcceptanceDecision.producerReceiptAuthority",
        "producer receipt `outputs[].role`",
        "Fixture alignment:",
        "make SpecHarvester output trusted",
    ):
        assert required_text in fixture_policy

    for required_text in (
        "Producer Bundle Fixture Policy",
        "SpecPM owns the consumer contract examples",
        "SpecHarvester owns generated candidate bundle examples",
        "should not treat the other repository's `main` branch as a trust root",
        "drift-sensitive fields",
        "specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md",
    ):
        assert required_text in docc_fixture_policy_flat

    assert "specs/PRODUCER_RECEIPTS.md" in readme
    assert "specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md" in readme
    assert "specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md" in readme
    assert "specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md" in readme
    assert "specs/REGISTRY_ACCEPTANCE_DECISIONS.md" in readme
    assert "specs/PRODUCER_RECEIPTS.md" in docc_overview
    assert "specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md" in docc_overview
    assert "specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md" in docc_overview
    assert "specs/REGISTRY_ACCEPTANCE_DECISIONS.md" in docc_overview
    assert "<doc:ProducerReceipts>" in docc_overview
    assert "<doc:ProducerBundleProposalPolicy>" in docc_overview
    assert "<doc:ProducerBundleProposalAutomation>" in docc_overview
    assert "<doc:ProducerBundleFixturePolicy>" in docc_overview
    assert "<doc:RegistryAcceptanceDecisions>" in docc_overview
    assert "<doc:ProducerReceipts>" in docc_receipts
    assert "<doc:ProducerReceipts>" in docc_roadmap
    assert "<doc:ProducerBundleProposalPolicy>" in docc_roadmap
    assert "specs/PRODUCER_RECEIPTS.md" in provenance_policy
    assert "SpecPMProducerReceipt" in roadmap
    assert "SpecPMProducerReceipt" in docc_roadmap
    assert "generated_spec_package_v0" in roadmap
    assert "generated_spec_package_v0" in docc_roadmap
    assert "Producer candidate bundle contract alignment is now documented" in roadmap
    assert "Producer candidate bundle contract alignment is now documented" in docc_roadmap
    assert "SpecPM-side producer bundle proposal policy is now documented" in roadmap
    assert "SpecPM-side producer bundle proposal policy is now documented" in docc_roadmap
    assert "Producer-backed public-index intake is now documented" in roadmap
    assert "Producer-backed public-index intake is now documented" in docc_roadmap
    assert "The SpecHarvester producer loop now has receipt" in roadmap_flat
    assert "The SpecHarvester producer loop now has receipt" in docc_roadmap_flat
    assert "proposal automation evidence links" in roadmap_flat
    assert "proposal automation evidence links" in docc_roadmap_flat
    assert "Shared SpecPM/SpecHarvester fixture policy is now documented" in roadmap
    assert "Shared SpecPM/SpecHarvester fixture policy is now documented" in docc_roadmap
    assert "SpecHarvester-to-SpecPM proposal automation contract is now documented" in roadmap
    assert "SpecHarvester-to-SpecPM proposal automation contract is now documented" in docc_roadmap
    assert "External registry acceptance decision records are now documented" in roadmap
    assert "External registry acceptance decision records are now documented" in docc_roadmap
    assert "SpecHarvester-to-SpecPM package-set dry-run validation" in roadmap
    assert "SpecHarvester-to-SpecPM package-set dry-run validation" in docc_roadmap
    assert "real `xyflow` checkout" in roadmap
    assert "real `xyflow` checkout" in docc_roadmap
    assert "maintainer-selected accepted-source materialization" in roadmap_flat
    assert "maintainer-selected accepted-source materialization" in docc_roadmap_flat

    assert receipt_fixture["apiVersion"] == "specpm.receipts/v0"
    assert receipt_fixture["kind"] == "SpecPMProducerReceipt"
    assert receipt_fixture["schemaVersion"] == 1
    assert receipt_fixture["receiptProfile"] == "generated_spec_package_v0"
    assert receipt_fixture["subject"]["packageApiVersion"] == "specpm.dev/v0.1"
    assert receipt_fixture["subject"]["candidateStatus"] == "review-ready"
    assert receipt_fixture["producer"]["name"] == "SpecHarvester"
    assert re.fullmatch(r"[0-9a-f]{40}", receipt_fixture["producer"]["revision"])
    assert receipt_fixture["configuration"]["deterministic"] is False
    assert receipt_fixture["configuration"]["digest"]["algorithm"] == "sha256"
    assert receipt_fixture["validation"]["status"] == "warning"
    assert receipt_fixture["validation"]["reportPath"] == "validation-report.json"
    assert receipt_fixture["diagnostics"]["status"] == "warnings"
    assert receipt_fixture["diagnostics"]["path"] == "diagnostics.json"
    assert receipt_fixture["humanReview"]["status"] == "required"
    assert "public_index_acceptance" in receipt_fixture["humanReview"]["requiredFor"]
    assert receipt_fixture["privacy"]["secretsIncluded"] is False
    assert {output["role"] for output in receipt_fixture["outputs"]} >= {
        "manifest",
        "boundary_spec",
        "validation_report",
        "diagnostics",
    }
    assert all(output["path"] != "producer-receipt.json" for output in receipt_fixture["outputs"])
    for section in ("inputs", "outputs"):
        for entry in receipt_fixture[section]:
            assert entry["digest"]["algorithm"] == "sha256"
            assert re.fullmatch(r"[0-9a-f]{64}", entry["digest"]["value"])
    assert receipt_fixture["diagnostics"]["digest"]["algorithm"] == "sha256"
    assert re.fullmatch(r"[0-9a-f]{64}", receipt_fixture["diagnostics"]["digest"]["value"])
    assert acceptance_decision_fixture["apiVersion"] == "specpm.decisions/v0"
    assert acceptance_decision_fixture["kind"] == "SpecPMRegistryAcceptanceDecision"
    assert acceptance_decision_fixture["schemaVersion"] == 1
    assert acceptance_decision_fixture["status"] == "approved"
    assert "public_index_acceptance" in acceptance_decision_fixture["requiredFor"]
    assert (
        acceptance_decision_fixture["producerEvidence"]["producerReceiptAuthority"]
        == "evidence_only"
    )
    assert acceptance_decision_fixture["subject"]["acceptedSourcePath"] == (
        "public-index/accepted-packages.yml"
    )
    assert acceptance_decision_fixture["maintainerReview"]["reviewLocation"].startswith(
        "https://github.com/0al-spec/SpecPM/pull/"
    )

    for checked_item in (
        "- [x] Document the draft `SpecPMProducerReceipt` envelope.",
        "- [x] Define the initial `generated_spec_package_v0` producer profile.",
        "- [x] Specify required subject, producer, inputs, configuration, outputs,",
        "- [x] Document the relationship between producer receipts and registry",
        "- [x] Add SpecHarvester-facing implementation requirements without making the",
        "- [x] Add a non-normative machine-readable fixture for the producer receipt",
        "- [x] Keep producer execution, analyzer execution, LLM prompt execution,",
        "Phase 63. Producer Candidate Bundle Contract Alignment",
        "- [x] Define `producer-receipt.json` as the machine-readable candidate",
        "- [x] Exclude `producer-receipt.json` from `outputs[]` to avoid the",
        "- [x] Define candidate bundle preflight rejection diagnostics without adding a",
        "Phase 64. SpecHarvester Producer Bundle Intake",
        "- [x] Document SpecPM-side proposal policy for producer candidate bundles,",
        "- [x] Add a candidate bundle intake checklist to public-index proposal and",
        "- [x] Align SpecHarvester-to-SpecPM proposal automation so proposal pull",
        "- [x] Add an optional SpecPM CI preflight gate for producer-backed proposals,",
        "- [x] Define a shared cross-repository fixture policy so SpecPM contract",
        "- [x] Define an external registry acceptance decision record that links",
    ):
        assert checked_item in workplan

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    constraint_ids = {constraint["id"] for constraint in boundary["constraints"]}
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.specs.producer_receipt_contract" in manifest_capabilities
    assert "specpm.specs.producer_bundle_proposal_policy" in manifest_capabilities
    assert "specpm.specs.producer_bundle_proposal_automation" in manifest_capabilities
    assert "specpm.specs.producer_bundle_fixture_policy" in manifest_capabilities
    assert "specpm.specs.ai_enrichment_consumer_policy" in manifest_capabilities
    assert "specpm.registry.acceptance_decision_record" in manifest_capabilities
    assert "specpm.specs.producer_receipt_contract" in boundary_capabilities
    assert "specpm.specs.producer_bundle_proposal_policy" in boundary_capabilities
    assert "specpm.specs.producer_bundle_proposal_automation" in boundary_capabilities
    assert "specpm.specs.producer_bundle_fixture_policy" in boundary_capabilities
    assert "specpm.specs.ai_enrichment_consumer_policy" in boundary_capabilities
    assert "specpm.registry.acceptance_decision_record" in boundary_capabilities
    assert "producer_receipts_not_generation_authority" in constraint_ids
    assert "specs/PRODUCER_RECEIPTS.md" in evidence_paths
    assert "specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md" in evidence_paths
    assert "specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md" in evidence_paths
    assert "specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md" in evidence_paths
    assert "specs/REGISTRY_ACCEPTANCE_DECISIONS.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/ProducerReceipts.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/ProducerBundleProposalPolicy.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/ProducerBundleProposalAutomation.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/ProducerBundleFixturePolicy.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/RegistryAcceptanceDecisions.md" in evidence_paths
    assert (
        "tests/fixtures/provenance_receipts/registry-acceptance-decision.example.json"
        in evidence_paths
    )
    assert "specpm producer-bundle preflight" in proposal_policy
    assert "producerEvidenceLinks" in proposal_policy
    assert "registryAcceptanceDecision" in proposal_policy
    assert "evidence_only" in proposal_policy
    assert "specpm producer-bundle preflight" in docc_proposal_policy
    assert "producerEvidenceLinks" in docc_proposal_policy
    assert "registryAcceptanceDecision" in docc_proposal_policy
    assert "evidence_only" in docc_proposal_policy
    assert (
        "tests/fixtures/provenance_receipts/generated-spec-package-receipt.example.json"
        in evidence_paths
    )


def test_multi_package_producer_intake_checklist_is_documented() -> None:
    policy = MULTI_PACKAGE_PRODUCER_INTAKE_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_MULTI_PACKAGE_PRODUCER_INTAKE_PAGE.read_text(encoding="utf-8")
    operator_guide = PUBLIC_INDEX_OPERATOR_GUIDE.read_text(encoding="utf-8")
    proposal_policy = (ROOT / "specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md").read_text(
        encoding="utf-8"
    )
    docc_proposal_policy = (
        ROOT / "Sources/SpecPM/Documentation.docc/ProducerBundleProposalPolicy.md"
    ).read_text(encoding="utf-8")
    docc_cli_reference = (ROOT / "Sources/SpecPM/Documentation.docc/CLIReference.md").read_text(
        encoding="utf-8"
    )
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    docc_roadmap = DOCC_ROADMAP_PAGE.read_text(encoding="utf-8")
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    operator_guide_flat = re.sub(r"\s+", " ", operator_guide)
    docc_policy_flat = re.sub(r"\s+", " ", docc_policy)
    roadmap_flat = re.sub(r"\s+", " ", roadmap)
    docc_roadmap_flat = re.sub(r"\s+", " ", docc_roadmap)
    workplan_flat = re.sub(r"\s+", " ", workplan)
    proposal_policy_flat = re.sub(r"\s+", " ", proposal_policy)
    docc_proposal_policy_flat = re.sub(r"\s+", " ", docc_proposal_policy)

    for required_text in (
        "package-set-handoff-proposal.json",
        "package-set-handoff-proposal.md",
        "Package-Set Handoff Checklist",
        "producerEvidenceLinks",
        "registryAcceptanceDecision.status",
        "registryAcceptanceDecision.producerReceiptAuthority",
        "evidence_only",
        "trusted workflow boundary or dry-run artifact",
        "SPECPM_PROPOSAL_TOKEN",
        "Partial Acceptance",
        "relation proposals",
        "accepted relations",
        "dry-run handoff claims that it created, approved, or merged",
        "specpm producer-bundle preflight",
        "specpm producer-bundle materialize-package-set",
        "member manifest IDs",
        "contains",
        "package-set-ai-enrichment-proposal.json",
        "SpecHarvesterPackageSetAIEnrichmentProposal",
        "AI Enrichment Checklist",
        "proposal_only_not_registry_acceptance",
        "unsupported evidence paths are diagnostics",
        "interfaces[].kind",
        "provider receipts as provenance only",
        "must not auto-accept capabilities, intents, interfaces, summaries",
    ):
        assert required_text in policy

    for required_text in (
        "package-set-handoff-proposal.json",
        "package-set-handoff-proposal.md",
        "Handoff Checklist",
        "producerEvidenceLinks",
        "registryAcceptanceDecision.status",
        "producerReceiptAuthority",
        "evidence_only",
        "SpecPM write credentials",
        "Rejected or deferred members",
        "specpm producer-bundle preflight",
        "specpm producer-bundle materialize-package-set",
        "member manifest IDs",
        "contains",
        "package-set-ai-enrichment-proposal.json",
        "SpecHarvesterPackageSetAIEnrichmentProposal",
        "AI Enrichment Checklist",
        "proposal_only_not_registry_acceptance",
        "unsupported evidence paths remain diagnostics",
        "interfaces[].kind",
        "provider receipts are provenance only",
        "must not auto-accept capabilities, intents, interfaces, summaries",
    ):
        assert required_text in docc_policy_flat

    for required_text in (
        "Package-Set Producer Handoff Intake",
        "package-set-handoff-proposal.json",
        "package-set-handoff-proposal.md",
        "dry-run package-set automation",
        "registryAcceptanceDecision.status",
        "producerReceiptAuthority",
        "evidence_only",
        "SPECPM_PROPOSAL_TOKEN",
        "partial acceptance",
        "xyflow.workspace",
        "specpm producer-bundle preflight",
        "member IDs match manifests",
        "relation endpoints",
        "materialize-package-set",
        "package-set-ai-enrichment-proposal.json",
        "semantic review assistance only",
        "authority: proposal_only_not_registry_acceptance",
        "provider receipts are provenance, not registry authority",
    ):
        assert required_text in operator_guide_flat

    for required_text in (
        "recognize SpecHarvester package-set handoff artifacts",
        "package-set-handoff-proposal.json",
        "package-set-handoff-proposal.md",
        "dry-run review evidence",
        "SpecPM write credentials",
        "consumer-side package-set handoff preflight",
        "evidence digests",
        "SpecHarvester-to-SpecPM package-set dry-run validation",
        "real `xyflow` checkout",
        "zero errors and zero warnings",
        "maintainer-selected accepted-source materialization",
        "materialize-package-set",
        "package-set-ai-enrichment-proposal.json",
        "proposal-only review evidence",
        "SpecHarvester-to-SpecPM package-set AI enrichment",
        "explicit maintainer package/relation selection",
    ):
        assert required_text in roadmap_flat

    for required_text in (
        "SpecPM package-set intake now recognizes SpecHarvester",
        "package-set-handoff-proposal.json",
        "package-set-handoff-proposal.md",
        "dry-run review evidence",
        "maintainer decisions as the registry authority",
        "producer-bundle preflight",
        "evidence digests",
        "SpecHarvester-to-SpecPM package-set dry-run validation",
        "real `xyflow` checkout",
        "zero errors and zero warnings",
        "maintainer-selected accepted-source materialization",
        "materialize-package-set",
        "package-set-ai-enrichment-proposal.json",
        "proposal-only review evidence",
        "SpecHarvester-to-SpecPM package-set AI enrichment",
        "explicit maintainer package/relation selection",
    ):
        assert required_text in docc_roadmap_flat

    for required_text in (
        "Document the SpecPM-side package-set handoff intake checklist",
        "SpecHarvester `package-set-handoff-proposal.json`",
        "`package-set-handoff-proposal.md` dry-run evidence",
        "`SpecHarvesterPackageSetHandoffProposal` JSON artifact",
        "`contains` relation endpoints",
        "P66-T8. Maintainer-Selected Package-Set Materialization",
        "explicit maintainer selection of package IDs and relation IDs",
        "A passing SpecPM preflight remains review evidence only",
        "specpm producer-bundle materialize-package-set",
        "`--apply` copies only selected candidate directories",
        "P66-T9. Package-Set AI Enrichment Consumer Policy",
        "`SpecHarvesterPackageSetAIEnrichmentProposal` artifacts",
        "proposal_only_not_registry_acceptance",
        "The AI artifact did not alter accepted-source selection",
    ):
        assert required_text in workplan_flat

    for required_text in (
        "Package-set handoff preflight has been exercised end-to-end on a real `xyflow`",
        "zero errors and zero warnings",
        "maintainer-selected accepted-source materialization",
        "explicit selection of package IDs and relation IDs",
        "automatic registry acceptance",
        "specpm producer-bundle materialize-package-set",
        "Package-set AI enrichment has also been exercised",
        "AI artifact remained review evidence",
        "did not alter accepted-source selection",
    ):
        assert required_text in proposal_policy_flat
        assert required_text in docc_proposal_policy_flat

    for required_text in (
        "specpm producer-bundle materialize-package-set",
        "--handoff <package-set-handoff-proposal.json>",
        "--package <package-id>",
        "--relation <relation-id>",
        "--manifest-candidate-output",
        "fails closed",
    ):
        assert required_text in docc_cli_reference


def test_producer_bundle_preflight_accepts_spec_harvester_pr_body(tmp_path: Path) -> None:
    root = tmp_path / "checkout"
    package = root / "public-index/generated/example.package/0.1.0"
    package.mkdir(parents=True)
    specs_dir = package / "specs"
    specs_dir.mkdir()
    manifest = package / "specpm.yaml"
    manifest.write_text("schemaVersion: 1\nmetadata:\n  id: example.package\n", encoding="utf-8")
    (specs_dir / "example.spec.yaml").write_text("apiVersion: specpm.dev/v0.1\n", encoding="utf-8")
    for name in ("producer-receipt.json", "validation-report.json", "diagnostics.json"):
        (package / name).write_text("{}\n", encoding="utf-8")
    body = tmp_path / "body.md"
    write_producer_bundle_pr_body(body, manifest_digest=f"sha256:{sha256_path(manifest)}")

    report = preflight_producer_bundle(body, root=root)

    assert report["kind"] == "SpecPMProducerBundlePreflightReport"
    assert report["status"] == "warning"
    assert report["summary"] == {
        "producerEvidenceRoleCount": 9,
        "packageSetHandoff": None,
        "errorCount": 0,
        "warningCount": 2,
    }
    assert set(report["producerEvidenceRoles"]) == {
        "accepted_source_bundle",
        "accepted_source_diff",
        "boundary_spec",
        "diagnostics",
        "manifest",
        "producer_preflight",
        "producer_receipt",
        "static_viewer",
        "validation_report",
    }
    assert report["registryAcceptanceDecision"] == {
        "producerAuthority": None,
        "producerReceiptAuthority": "evidence_only",
        "recordKind": "SpecPMRegistryAcceptanceDecision",
        "status": "external_required",
    }
    assert issue_codes(report["warnings"]) == {"producer_evidence_optional_missing"}


def test_cli_producer_bundle_preflight_emits_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "checkout"
    package = root / "public-index/generated/example.package/0.1.0"
    package.mkdir(parents=True)
    specs_dir = package / "specs"
    specs_dir.mkdir()
    manifest = package / "specpm.yaml"
    manifest.write_text("schemaVersion: 1\nmetadata:\n  id: example.package\n", encoding="utf-8")
    (specs_dir / "example.spec.yaml").write_text("apiVersion: specpm.dev/v0.1\n", encoding="utf-8")
    for name in ("producer-receipt.json", "validation-report.json", "diagnostics.json"):
        (package / name).write_text("{}\n", encoding="utf-8")
    body = tmp_path / "body.md"
    write_producer_bundle_pr_body(body, manifest_digest=f"sha256:{sha256_path(manifest)}")

    exit_code = main(
        ["producer-bundle", "preflight", "--body", str(body), "--root", str(root), "--json"]
    )

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert exit_code == 0
    assert report["status"] == "warning"
    assert report["summary"]["errorCount"] == 0
    assert report["registryAcceptanceDecision"]["status"] == "external_required"


def test_producer_bundle_preflight_accepts_package_set_handoff(tmp_path: Path) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["status"] == "passed"
    assert report["summary"]["producerEvidenceRoleCount"] == 0
    assert report["summary"]["packageSetHandoff"] == {
        "id": "example.workspace",
        "memberCount": 2,
        "relationCount": 1,
        "evidenceRoleCount": 5,
        "preflightStatus": "passed",
        "registryAcceptanceStatus": "external_required",
    }
    assert report["packageSetHandoff"] == report["summary"]["packageSetHandoff"]
    assert report["registryAcceptanceDecision"] == {
        "producerAuthority": "evidence_only",
        "producerReceiptAuthority": None,
        "recordKind": "SpecPMRegistryAcceptanceDecision",
        "status": "external_required",
    }


def test_cli_producer_bundle_preflight_accepts_package_set_handoff_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)

    exit_code = main(
        ["producer-bundle", "preflight", "--body", str(body), "--root", str(bundle_set), "--json"]
    )

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert exit_code == 0
    assert report["status"] == "passed"
    assert report["packageSetHandoff"]["id"] == "example.workspace"
    assert report["packageSetHandoff"]["memberCount"] == 2
    assert report["packageSetHandoff"]["relationCount"] == 1


def test_producer_bundle_preflight_rejects_inconsistent_package_set_handoff(
    tmp_path: Path,
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set, bad_relation=True)

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["status"] == "failed"
    assert {
        "package_set_member_manifest_id_mismatch",
        "package_set_relation_target_missing",
    }.issubset(issue_codes(report["errors"]))


def test_producer_bundle_preflight_rejects_missing_required_package_set_evidence(
    tmp_path: Path,
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)
    handoff = json.loads(body.read_text(encoding="utf-8"))
    handoff["evidenceLinks"][0]["status"] = "missing"
    body.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["status"] == "failed"
    assert "package_set_evidence_required_missing" in issue_codes(report["errors"])


def test_producer_bundle_preflight_rejects_missing_required_member_evidence(
    tmp_path: Path,
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)
    handoff = json.loads(body.read_text(encoding="utf-8"))
    handoff["members"][0]["evidenceLinks"][0]["status"] = "missing"
    body.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["status"] == "failed"
    assert "package_set_member_evidence_required_missing" in issue_codes(report["errors"])


def test_producer_bundle_preflight_falls_back_from_null_package_set_receipt_authority(
    tmp_path: Path,
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)
    handoff = json.loads(body.read_text(encoding="utf-8"))
    handoff["registryAcceptanceDecision"]["producerReceiptAuthority"] = None
    body.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["status"] == "passed"
    assert "package_set_acceptance_decision_authority_invalid" not in issue_codes(report["errors"])


def test_producer_bundle_preflight_skips_relation_acceptance_warning_without_relations(
    tmp_path: Path,
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)
    handoff = json.loads(body.read_text(encoding="utf-8"))
    handoff["packageSet"]["relationCount"] = 0
    handoff["relations"] = []
    handoff["preflight"]["relationCount"] = 0
    handoff["registryAcceptanceDecision"]["requiredFor"] = ["public_index_acceptance"]
    body.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["status"] == "passed"
    assert "package_set_acceptance_decision_relation_scope_missing" not in issue_codes(
        report["warnings"]
    )


def test_producer_bundle_preflight_summary_counts_only_valid_package_set_evidence_roles(
    tmp_path: Path,
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)
    handoff = json.loads(body.read_text(encoding="utf-8"))
    handoff["evidenceLinks"].append(
        {
            "path": "package-set-draft.json",
            "pathScope": "bundle_relative",
            "status": "present",
        }
    )
    body.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["summary"]["packageSetHandoff"]["evidenceRoleCount"] == 5
    assert "package_set_evidence_role_missing" in issue_codes(report["errors"])


def test_producer_bundle_preflight_reports_package_set_identity_errors(
    tmp_path: Path,
) -> None:
    bundle_set = tmp_path / "package-set"
    body = write_package_set_handoff_fixture(bundle_set)
    handoff = json.loads(body.read_text(encoding="utf-8"))
    handoff["apiVersion"] = "spec-harvester.package-set-handoff-proposal/v9"
    body.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = preflight_producer_bundle(body, root=bundle_set)

    assert report["status"] == "failed"
    assert "package_set_handoff_api_version_invalid" in issue_codes(report["errors"])
    assert "producer_evidence_links_missing" not in issue_codes(report["errors"])


def test_package_set_materialization_prepares_selected_accepted_source_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace", "example.member"],
        relation_ids=["example.workspace.contains.example.member"],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
    )

    assert report["status"] == "prepared"
    assert report["applied"] is False
    assert report["summary"]["addedPackageCount"] == 2
    assert report["manifest"]["candidate"]["packages"] == [
        {"path": "public-index/generated/example.workspace/0.1.0"},
        {"path": "public-index/generated/example.member/0.1.0"},
    ]
    assert report["relations"] == [
        {
            "id": "example.workspace.contains.example.member",
            "type": "contains",
            "source": "example.workspace",
            "target": "example.member",
            "reviewStatus": "selected_for_maintainer_review",
        }
    ]
    assert not (tmp_path / "public-index/generated/example.workspace/0.1.0").exists()


def test_package_set_materialization_apply_copies_selected_subset_and_updates_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace"],
        relation_ids=[],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
        apply_update=True,
    )

    assert report["status"] == "applied"
    assert report["applied"] is True
    materialized = tmp_path / "public-index/generated/example.workspace/0.1.0"
    assert (materialized / "specpm.yaml").is_file()
    assert not (tmp_path / "public-index/generated/example.member/0.1.0").exists()
    manifest_payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["packages"] == [
        {"path": "public-index/generated/example.workspace/0.1.0"}
    ]


def test_package_set_materialization_apply_rejects_existing_output_before_copying(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")
    existing = tmp_path / "public-index/generated/example.member/0.1.0"
    existing.mkdir(parents=True)

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace", "example.member"],
        relation_ids=[],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
        apply_update=True,
    )

    assert report["status"] == "invalid"
    assert "package_set_materialization_output_exists" in issue_codes(report["errors"])
    assert not (tmp_path / "public-index/generated/example.workspace/0.1.0").exists()
    manifest_payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["packages"] == []


def test_package_set_materialization_rejects_candidate_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (bundle_set / "workspace" / "external-link").symlink_to(outside)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace"],
        relation_ids=[],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
        apply_update=True,
    )

    assert report["status"] == "invalid"
    assert "package_set_materialization_candidate_symlink" in issue_codes(report["errors"])
    assert not (tmp_path / "public-index/generated/example.workspace/0.1.0").exists()


def test_package_set_materialization_rejects_absolute_output_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace"],
        relation_ids=[],
        output_root=tmp_path / "outside-generated",
        manifest_path=manifest,
    )

    assert report["status"] == "invalid"
    assert "package_set_materialization_output_root_invalid" in issue_codes(report["errors"])


def test_package_set_materialization_rejects_parent_output_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace"],
        relation_ids=[],
        output_root=Path("../generated"),
        manifest_path=manifest,
    )

    assert report["status"] == "invalid"
    assert "package_set_materialization_output_root_invalid" in issue_codes(report["errors"])


def test_package_set_materialization_rejects_unknown_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.missing"],
        relation_ids=["example.workspace.contains.missing"],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
    )

    assert report["status"] == "invalid"
    assert {
        "package_set_materialization_package_unknown",
        "package_set_materialization_relation_unknown",
    }.issubset(issue_codes(report["errors"]))


def test_package_set_materialization_rejects_relation_when_endpoint_not_selected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace"],
        relation_ids=["example.workspace.contains.example.member"],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
    )

    assert report["status"] == "invalid"
    assert "package_set_materialization_relation_endpoint_not_selected" in issue_codes(
        report["errors"]
    )


def test_package_set_materialization_requires_passing_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    payload = json.loads(handoff.read_text(encoding="utf-8"))
    payload["preflight"]["status"] = "failed"
    handoff.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        bundle_set,
        package_ids=["example.workspace"],
        relation_ids=[],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
    )

    assert report["status"] == "invalid"
    assert "package_set_preflight_not_passed" in issue_codes(report["errors"])


def test_package_set_materialization_returns_invalid_for_missing_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        tmp_path / "missing-handoff.json",
        tmp_path,
        package_ids=["example.workspace"],
        relation_ids=[],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
    )

    assert report["status"] == "invalid"
    assert {
        "package_set_handoff_missing",
        "package_set_preflight_not_passed",
    }.issubset(issue_codes(report["errors"]))


def test_package_set_materialization_returns_invalid_for_missing_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    report = materialize_package_set_handoff(
        handoff,
        tmp_path / "missing-root",
        package_ids=["example.workspace"],
        relation_ids=[],
        output_root=Path("public-index/generated"),
        manifest_path=manifest,
    )

    assert report["status"] == "invalid"
    assert {
        "package_set_preflight_not_passed",
        "package_set_materialization_candidate_missing",
    }.issubset(issue_codes(report["errors"]))


def test_cli_package_set_materialization_writes_review_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")
    report_path = tmp_path / "materialization-report.json"
    manifest_candidate = tmp_path / "accepted-manifest-candidate.yml"
    pr_body = tmp_path / "package-set-pr.md"

    exit_code = main(
        [
            "producer-bundle",
            "materialize-package-set",
            "--handoff",
            str(handoff),
            "--root",
            str(bundle_set),
            "--manifest",
            str(manifest),
            "--output-root",
            "public-index/generated",
            "--package",
            "example.workspace",
            "--json-output",
            str(report_path),
            "--manifest-candidate-output",
            str(manifest_candidate),
            "--pr-body-output",
            str(pr_body),
        ]
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    candidate = yaml.safe_load(manifest_candidate.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["status"] == "prepared"
    assert candidate["packages"] == [{"path": "public-index/generated/example.workspace/0.1.0"}]
    assert "Selected Packages" in pr_body.read_text(encoding="utf-8")


def test_cli_package_set_materialization_defaults_to_human_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_set = tmp_path / "package-set"
    handoff = write_package_set_handoff_fixture(bundle_set)
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    exit_code = main(
        [
            "producer-bundle",
            "materialize-package-set",
            "--handoff",
            str(handoff),
            "--root",
            str(bundle_set),
            "--manifest",
            str(manifest),
            "--output-root",
            "public-index/generated",
            "--package",
            "example.workspace",
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert stdout.startswith("prepared: package-set materialization")
    assert not stdout.lstrip().startswith("{")


def test_producer_bundle_preflight_rejects_missing_registry_decision(tmp_path: Path) -> None:
    body = tmp_path / "body.md"
    write_producer_bundle_pr_body(body, include_decision=False)

    report = preflight_producer_bundle(body)

    assert report["status"] == "failed"
    assert "registry_acceptance_decision_missing" in issue_codes(report["errors"])
    assert "registry_acceptance_decision_status_invalid" in issue_codes(report["errors"])


def test_producer_bundle_preflight_rejects_missing_pull_request_path(tmp_path: Path) -> None:
    body = tmp_path / "body.md"
    write_producer_bundle_pr_body(body)
    body.write_text(
        body.read_text(encoding="utf-8").replace(
            '"path": "pull-request-diff",',
            '"path": "",',
        ),
        encoding="utf-8",
    )

    report = preflight_producer_bundle(body)

    assert report["status"] == "failed"
    assert "producer_evidence_path_missing" in issue_codes(report["errors"])


def test_producer_bundle_preflight_rejects_digest_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "checkout"
    package = root / "public-index/generated/example.package/0.1.0"
    package.mkdir(parents=True)
    specs_dir = package / "specs"
    specs_dir.mkdir()
    (package / "specpm.yaml").write_text("schemaVersion: 1\n", encoding="utf-8")
    (specs_dir / "example.spec.yaml").write_text("apiVersion: specpm.dev/v0.1\n", encoding="utf-8")
    for name in ("producer-receipt.json", "validation-report.json", "diagnostics.json"):
        (package / name).write_text("{}\n", encoding="utf-8")
    body = tmp_path / "body.md"
    write_producer_bundle_pr_body(body, manifest_digest=f"sha256:{'0' * 64}")

    report = preflight_producer_bundle(body, root=root)

    assert report["status"] == "failed"
    assert "producer_evidence_digest_mismatch" in issue_codes(report["errors"])


def test_intent_taxonomy_governance_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    policy = INTENT_TAXONOMY_GOVERNANCE_DOC.read_text(encoding="utf-8")
    docc_policy = DOCC_INTENT_TAXONOMY_GOVERNANCE_PAGE.read_text(encoding="utf-8")
    docc_roadmap = DOCC_ROADMAP_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    identifier_model = (ROOT / "specs/IDENTIFIER_MODEL.md").read_text(encoding="utf-8")
    intent_discovery = (ROOT / "specs/INTENT_DISCOVERY_BOUNDARY.md").read_text(encoding="utf-8")
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for required_text in (
        "Observation is not standardization",
        "accepted intent",
        "deprecated intent",
        "rejected intent",
        "reviewed governance process",
        "provider-neutral",
        "package-neutral",
        "experimental or private intent IDs",
        "intent.experimental.<domain>.<name>",
        "intent.private.<org>.<domain>.<name>",
        "must not hide or mutate declared metadata",
        "runtime enforcement of accepted/deprecated/rejected states",
        "SpecPM may carry intent; SpecGraph decides meaning.",
    ):
        assert required_text in policy

    for required_text in (
        "observed package declarations do not become canonical vocabulary",
        "`canonical: false`",
        "provider-neutral",
        "`observed`, `proposed`, `accepted`, `deprecated`",
        "Promotion to accepted canonical vocabulary requires normal review",
    ):
        assert required_text in docc_policy

    assert "specs/INTENT_TAXONOMY_GOVERNANCE.md" in readme
    assert "specs/INTENT_TAXONOMY_GOVERNANCE.md" in docc_overview
    assert "<doc:IntentTaxonomyGovernance>" in docc_overview
    assert "<doc:IntentTaxonomyGovernance>" in docc_roadmap
    assert "specs/INTENT_TAXONOMY_GOVERNANCE.md" in identifier_model
    assert "specs/INTENT_TAXONOMY_GOVERNANCE.md" in intent_discovery
    assert "Intent taxonomy governance is now documented" in roadmap
    assert "Intent taxonomy governance is now documented" in docc_roadmap
    assert "Package signing and revocation policy is now documented" in roadmap
    assert "Package signing and revocation policy is now documented" in docc_roadmap

    for checked_item in (
        "- [x] Define how canonical `intent.*` domains are proposed, reviewed, renamed,",
        "- [x] Document how package-owned capabilities map to package-neutral intent",
        "- [x] Specify extension rules for experimental or private intent namespaces.",
        "- [x] Define conflict handling when different packages claim similar intent",
        "- [x] Keep semantic interpretation and candidate ranking outside SpecPM core.",
    ):
        assert checked_item in workplan

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    constraint_ids = {constraint["id"] for constraint in boundary["constraints"]}
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.intent.taxonomy_governance" in manifest_capabilities
    assert "specpm.intent.taxonomy_governance" in boundary_capabilities
    assert "intent_taxonomy_observation_not_canonical" in constraint_ids
    assert "specs/INTENT_TAXONOMY_GOVERNANCE.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/IntentTaxonomyGovernance.md" in evidence_paths


def test_docs_workflow_publishes_public_index_metadata_with_docc() -> None:
    loaded = load_yaml_file(DOCS_WORKFLOW)

    trigger = loaded.get("on") or loaded.get(True)
    paths = set(trigger["push"]["paths"])
    assert {
        "src/specpm/**",
        "examples/**",
        "public-index/**",
        "landing_page/**",
        "scripts/render_pages.py",
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
        "Render GitHub Pages root redirect and viewer"
    )
    assert step_names.index("Render GitHub Pages root redirect and viewer") < step_names.index(
        "Prepare SpecPM.dev static host artifact"
    )
    assert step_names.index("Prepare SpecPM.dev static host artifact") < step_names.index(
        "Upload static host artifact"
    )
    assert step_names.index("Upload static host artifact") < step_names.index("Upload artifact")

    steps_by_name = {step["name"]: step for step in steps if "name" in step}
    assert steps_by_name["Set up Python"]["uses"] == "actions/setup-python@v6"
    assert steps_by_name["Install SpecPM"]["run"] == 'python -m pip install -e ".[dev]"'

    generate = steps_by_name["Generate public index metadata"]
    assert generate["env"]["SPECPM_PUBLIC_INDEX_REGISTRY_URL"] == (
        "https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}"
    )
    assert "python -m specpm.cli public-index generate" in generate["run"]
    assert "--manifest public-index/accepted-packages.yml" in generate["run"]
    assert "--output ./.docc-build" in generate["run"]
    assert '--registry "$SPECPM_PUBLIC_INDEX_REGISTRY_URL"' in generate["run"]
    assert 'SPECPM_VERSION="$(python -c' in generate["run"]
    assert '--specpm-version "$SPECPM_VERSION"' in generate["run"]
    assert '--build-number "${{ github.run_number }}"' in generate["run"]
    assert '--build-revision "${{ github.sha }}"' in generate["run"]

    render = steps_by_name["Render GitHub Pages root redirect and viewer"]
    assert "python scripts/render_pages.py" in render["run"]
    assert "--output ./.docc-build" in render["run"]
    assert '--specpm-version "$SPECPM_VERSION"' in render["run"]
    assert '--build-number "${{ github.run_number }}"' in render["run"]
    assert '--build-revision "${{ github.sha }}"' in render["run"]
    assert "--root-mode docs-redirect" in render["run"]
    assert (
        '--docs-url "https://${{ github.repository_owner }}.github.io/'
        '${{ github.event.repository.name }}/documentation/specpm/"' in render["run"]
    )

    static_render = steps_by_name["Prepare SpecPM.dev static host artifact"]
    assert "rm -rf ./.static-host-build" in static_render["run"]
    assert "cp -R ./.docc-build ./.static-host-build" in static_render["run"]
    assert "python scripts/render_pages.py" in static_render["run"]
    assert "--output ./.static-host-build" in static_render["run"]
    assert "--root-mode" not in static_render["run"]

    upload = steps_by_name["Upload artifact"]
    assert upload["with"]["path"] == "./.docc-build"

    static_upload = steps_by_name["Upload static host artifact"]
    assert static_upload["uses"] == "actions/upload-artifact@v7"
    assert static_upload["with"]["name"] == "specpm-static-site"
    assert static_upload["with"]["path"] == "./.static-host-build"
    assert static_upload["with"]["if-no-files-found"] == "error"
    assert static_upload["with"]["include-hidden-files"] is True

    static_host = loaded["jobs"]["deploy-static-host"]
    assert "github.ref == 'refs/heads/main'" in static_host["if"]
    assert (
        "github.event_name == 'push' || github.event_name == 'workflow_dispatch'"
        in (static_host["if"])
    )
    assert static_host["needs"] == "build"
    assert static_host["timeout-minutes"] == 30
    assert static_host["environment"]["name"] == "FTP"
    assert static_host["environment"]["url"] == "https://SpecPM.dev"
    assert static_host["env"]["FTP_HOST"] == "${{ secrets.FTP_HOST }}"
    assert static_host["env"]["FTP_PORT"] == "${{ secrets.FTP_PORT }}"
    assert static_host["env"]["FTP_USER"] == "${{ secrets.FTP_USER }}"
    assert static_host["env"]["FTP_PASS"] == "${{ secrets.FTP_PASS }}"
    assert static_host["env"]["FTP_REMOTE_ROOT"] == "${{ secrets.FTP_REMOTE_ROOT }}"
    static_steps = {step["name"]: step for step in static_host["steps"] if "name" in step}
    assert static_steps["Download static host artifact"]["uses"] == "actions/download-artifact@v8"
    assert static_steps["Download static host artifact"]["with"]["name"] == "specpm-static-site"
    assert (
        "test -f specpm-static-site/index.html"
        in (static_steps["Validate static host artifact"]["run"])
    )
    assert (
        "test -f specpm-static-site/theme-settings.json"
        in (static_steps["Validate static host artifact"]["run"])
    )
    assert (
        "test -f specpm-static-site/viewer/index.html"
        in (static_steps["Validate static host artifact"]["run"])
    )
    assert (
        "test -f specpm-static-site/v0/status/index.json"
        in (static_steps["Validate static host artifact"]["run"])
    )
    summarize_run = static_steps["Summarize static host artifact"]["run"]
    assert (
        "find specpm-static-site -type f | sort > /tmp/specpm-static-site-files.txt"
        in summarize_run
    )
    assert "wc -l < /tmp/specpm-static-site-files.txt" in summarize_run
    assert "du -sb specpm-static-site" in summarize_run
    assert "du -sh specpm-static-site" in summarize_run
    assert "Largest static host files:" in summarize_run
    validate_deploy_run = static_steps["Validate deploy settings"]["run"]
    assert 'test -n "$FTP_HOST"' in validate_deploy_run
    assert 'test -n "$FTP_USER"' in validate_deploy_run
    assert 'test -n "$FTP_PASS"' in validate_deploy_run
    assert 'test -n "$FTP_REMOTE_ROOT"' in validate_deploy_run
    assert 'if [ "$FTP_REMOTE_ROOT" = "/" ]; then' in validate_deploy_run
    assert (
        "apt-get install -y lftp openssh-client" in (static_steps["Install transfer client"]["run"])
    )
    known_hosts_run = static_steps["Prepare SFTP known hosts"]["run"]
    assert 'DEPLOY_PORT="${FTP_PORT:-22}"' in known_hosts_run
    assert "for attempt in 1 2 3; do" in known_hosts_run
    assert 'ssh-keyscan -T 20 -p "$DEPLOY_PORT" "$FTP_HOST"' in known_hosts_run
    assert "ssh-keyscan attempt $attempt failed; retrying." in known_hosts_run
    assert 'test -s "$HOME/.ssh/known_hosts"' in known_hosts_run
    check_target = static_steps["Check SpecPM.dev SFTP target"]
    assert check_target["timeout-minutes"] == 3
    check_target_run = check_target["run"]
    assert "timeout --kill-after=30s 2m lftp" in check_target_run
    assert "set cmd:fail-exit yes" in check_target_run
    assert "set net:max-retries 1" in check_target_run
    assert "set net:timeout 20" in check_target_run
    assert "set net:reconnect-interval-base 5" in check_target_run
    assert 'cls -1 "$FTP_REMOTE_ROOT"' in check_target_run
    upload_step = static_steps["Upload to SpecPM.dev over SFTP"]
    assert upload_step["timeout-minutes"] == 25
    upload_run = static_steps["Upload to SpecPM.dev over SFTP"]["run"]
    assert 'DEPLOY_PORT="${FTP_PORT:-22}"' in upload_run
    assert "SFTP upload" in upload_run
    assert "set cmd:fail-exit yes" in upload_run
    assert "set cmd:trace yes" in upload_run
    assert "set net:max-retries 1" in upload_run
    assert "set net:timeout 20" in upload_run
    assert "set net:reconnect-interval-base 5" in upload_run
    assert "set xfer:log yes" in upload_run
    assert 'set xfer:log-file "$TRANSFER_LOG"' in upload_run
    assert "set +e" in upload_run
    assert "timeout --kill-after=30s 18m lftp" in upload_run
    assert 'UPLOAD_STATUS="$?"' in upload_run
    assert "set -e" in upload_run
    assert 'lftp -u "$FTP_USER,$FTP_PASS" "sftp://$FTP_HOST:$DEPLOY_PORT"' in upload_run
    assert "SFTP upload exited with status $UPLOAD_STATUS" in upload_run
    assert 'tail -40 "$TRANSFER_LOG"' in upload_run
    assert 'exit "$UPLOAD_STATUS"' in upload_run
    assert "mirror -R --dry-run" not in upload_run
    assert 'mirror -R --verbose=2 --exclude-glob .DS_Store . "$FTP_REMOTE_ROOT"' in upload_run


def test_render_pages_can_keep_github_pages_root_as_docc_redirect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "site"
    docs_url = "https://0al-spec.github.io/SpecPM/documentation/specpm/"
    monkeypatch.chdir(ROOT)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/render_pages.py"),
            "--output",
            str(output),
            "--specpm-version",
            "0.2.0",
            "--build-number",
            "local",
            "--build-revision",
            "1234567890abcdef",
            "--root-mode",
            "docs-redirect",
            "--docs-url",
            docs_url,
        ],
        check=True,
    )

    root = (output / "index.html").read_text(encoding="utf-8")
    assert f'content="0; url={docs_url}"' in root
    assert f'<link rel="canonical" href="{docs_url}" />' in root
    assert "SpecPM - Resolve Needs Into Specifications" not in root
    assert (output / "viewer/index.html").is_file()
    assert (output / "viewer/assets/viewer.js").is_file()
    assert (output / "site-metadata.json").is_file()
    assert json.loads((output / "theme-settings.json").read_text(encoding="utf-8")) == {}


def test_deploy_connection_check_uses_trusted_sftp_dry_run() -> None:
    loaded = load_yaml_file(DEPLOY_CONNECTION_CHECK_WORKFLOW)

    trigger = loaded.get("on") or loaded.get(True)
    paths = set(trigger["pull_request_target"]["paths"])
    assert {
        ".github/workflows/deploy-connection-check.yml",
        ".github/workflows/docs.yml",
    } <= paths

    job = loaded["jobs"]["deploy-connection-check"]
    assert job["if"] == "github.event.pull_request.head.repo.full_name == github.repository"
    assert job["timeout-minutes"] == 10
    assert job["environment"]["name"] == "FTP"
    assert job["env"] == {
        "FTP_HOST": "${{ secrets.FTP_HOST }}",
        "FTP_PORT": "${{ secrets.FTP_PORT }}",
        "FTP_USER": "${{ secrets.FTP_USER }}",
        "FTP_PASS": "${{ secrets.FTP_PASS }}",
        "FTP_REMOTE_ROOT": "${{ secrets.FTP_REMOTE_ROOT }}",
    }

    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    assert steps["Checkout trusted workflow"]["uses"] == "actions/checkout@v6"
    assert steps["Checkout trusted workflow"]["with"]["ref"] == (
        "${{ github.event.pull_request.base.sha }}"
    )
    validate_run = steps["Validate deploy settings"]["run"]
    assert 'test -n "$FTP_HOST"' in validate_run
    assert 'test -n "$FTP_USER"' in validate_run
    assert 'test -n "$FTP_PASS"' in validate_run
    assert 'test -n "$FTP_REMOTE_ROOT"' in validate_run
    assert 'if [ "$FTP_REMOTE_ROOT" = "/" ]; then' in validate_run
    assert "apt-get install -y lftp openssh-client" in (steps["Install transfer client"]["run"])
    known_hosts_run = steps["Prepare SFTP known hosts"]["run"]
    assert 'DEPLOY_PORT="${FTP_PORT:-22}"' in known_hosts_run
    assert 'ssh-keyscan -T 20 -p "$DEPLOY_PORT" "$FTP_HOST"' in known_hosts_run
    assert steps["Check SFTP connection without upload"]["timeout-minutes"] == 3
    check_run = steps["Check SFTP connection without upload"]["run"]
    assert 'DEPLOY_PORT="${FTP_PORT:-22}"' in check_run
    assert "timeout --kill-after=30s 2m lftp" in check_run
    assert 'lftp -u "$FTP_USER,$FTP_PASS" "sftp://$FTP_HOST:$DEPLOY_PORT"' in check_run
    assert "set cmd:fail-exit yes" in check_run
    assert "set net:max-retries 1" in check_run
    assert "set net:timeout 20" in check_run
    assert "set net:reconnect-interval-base 5" in check_run
    assert 'cls -1 "$FTP_REMOTE_ROOT"' in check_run
    assert "mirror -R" not in check_run


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
    assert service["environment"]["SPECPM_VERSION"] == "${SPECPM_VERSION:-}"
    assert service["environment"]["SPECPM_PUBLIC_INDEX_BUILD_NUMBER"] == (
        "${SPECPM_PUBLIC_INDEX_BUILD_NUMBER:-}"
    )
    assert service["environment"]["SPECPM_PUBLIC_INDEX_BUILD_REVISION"] == (
        "${SPECPM_PUBLIC_INDEX_BUILD_REVISION:-}"
    )


def test_deploy_first_workflow_is_documented_and_smoke_testable() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agent_instructions = AGENTS_FILE.read_text(encoding="utf-8")
    deploy_doc = DEPLOY_FIRST_DOC.read_text(encoding="utf-8")
    docc_deployment = DOCC_DEPLOYMENT_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )

    expected_targets = {
        "public-index-reload",
        "public-alpha-smoke",
        "public-alpha-report",
        "public-index-observation-report",
        "pages-observation-report",
        "registry-observation-reports",
        "dev-up",
        "dev-reload",
        "dev-smoke",
        "dev-down",
        "pages-smoke",
        "pages-alpha-smoke",
        "pages-alpha-report",
    }
    for target in expected_targets:
        assert f"{target}:" in makefile

    assert "apt-get install -y --no-install-recommends ca-certificates git" in dockerfile
    assert "PAGES_REGISTRY_URL ?= https://0al-spec.github.io/SpecPM" in makefile
    assert "PUBLIC_ALPHA_RETAINED_SPECPM_VERSION ?= specpm.core@0.1.0" in makefile
    assert "PUBLIC_ALPHA_SMOKE_PACKAGE ?= specnode.core" in makefile
    assert "PUBLIC_ALPHA_SMOKE_VERSION ?= specnode.core@0.1.0" in makefile
    assert "PUBLIC_ALPHA_SMOKE_CAPABILITY ?= specnode.typed_job_protocol" in makefile
    assert "PUBLIC_ALPHA_REPORT_OUTPUT ?= .specpm/public-alpha-observation.json" in makefile
    assert "PAGES_ALPHA_REPORT_OUTPUT ?= .specpm/pages-alpha-observation.json" in makefile
    assert "REGISTRY_OBSERVATION_REPORT_DIR ?= .specpm/registry-observations" in makefile
    assert (
        "PUBLIC_INDEX_OBSERVATION_REPORT_OUTPUT ?= "
        "$(REGISTRY_OBSERVATION_REPORT_DIR)/local-public-index-observation.json"
    ) in makefile
    assert (
        "PAGES_OBSERVATION_REPORT_OUTPUT ?= "
        "$(REGISTRY_OBSERVATION_REPORT_DIR)/pages-public-index-observation.json"
    ) in makefile
    assert "SPECPM_VERSION ?=" in makefile
    assert "PAGES_BUILD_NUMBER ?= local" in makefile
    assert "PAGES_BUILD_REVISION ?=" in makefile
    assert "scripts/render_pages.py" in makefile
    assert "--specpm-version $(SPECPM_VERSION)" in makefile
    assert "--build-number $(PAGES_BUILD_NUMBER)" in makefile
    assert "--build-revision $(PAGES_BUILD_REVISION)" in makefile
    assert "--package specpm.core" in makefile
    assert "--version $(PUBLIC_ALPHA_RETAINED_SPECPM_VERSION)" in makefile
    assert "--version specpm.core@$(SPECPM_VERSION)" in makefile
    assert "--capability specpm.registry.public_alpha_index" in makefile
    assert "--intent intent.registry.intent_lookup" in makefile
    assert "--intent $(PUBLIC_INDEX_SMOKE_INTENT)" in makefile
    assert set(make_target_prerequisites(makefile, "dev-reload")) == {
        "public-index-reload",
        "public-index-smoke",
    }
    assert set(make_target_prerequisites(makefile, "dev-up")) == {
        "public-index-up",
        "public-index-smoke",
    }

    public_index_up_recipe = make_target_recipe(makefile, "public-index-up")
    assert "SPECPM_PUBLIC_INDEX_PORT=$(SPECPM_PUBLIC_INDEX_PORT)" in public_index_up_recipe
    assert "SPECPM_PUBLIC_INDEX_REGISTRY_URL=$(SPECPM_PUBLIC_INDEX_REGISTRY_URL)" in (
        public_index_up_recipe
    )
    assert "SPECPM_PUBLIC_INDEX_MANIFEST=$(PUBLIC_INDEX_MANIFEST)" in public_index_up_recipe
    assert "SPECPM_VERSION=$(SPECPM_VERSION)" in public_index_up_recipe
    assert "SPECPM_PUBLIC_INDEX_BUILD_NUMBER=$(PAGES_BUILD_NUMBER)" in public_index_up_recipe
    assert "SPECPM_PUBLIC_INDEX_BUILD_REVISION=$(PAGES_BUILD_REVISION)" in public_index_up_recipe
    assert "docker compose up" in public_index_up_recipe
    assert "--build" in public_index_up_recipe
    assert "$(PUBLIC_INDEX_COMPOSE_ARGS)" in public_index_up_recipe
    assert "public-index" in public_index_up_recipe

    public_index_reload_recipe = make_target_recipe(makefile, "public-index-reload")
    assert "$(MAKE)" in public_index_reload_recipe
    assert "public-index-up" in public_index_reload_recipe
    assert 'PUBLIC_INDEX_COMPOSE_ARGS="--force-recreate"' in public_index_reload_recipe

    public_alpha_recipe = make_target_recipe(makefile, "public-alpha-smoke")
    assert set(make_target_prerequisites(makefile, "public-alpha-smoke")) == {"public-index-smoke"}
    assert "remote package $(PUBLIC_ALPHA_SMOKE_PACKAGE)" in public_alpha_recipe
    assert "remote version $(PUBLIC_ALPHA_SMOKE_VERSION)" in public_alpha_recipe
    assert "remote search $(PUBLIC_ALPHA_SMOKE_CAPABILITY)" in public_alpha_recipe
    assert "--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL)" in public_alpha_recipe

    public_alpha_report_recipe = make_target_recipe(makefile, "public-alpha-report")
    assert set(make_target_prerequisites(makefile, "public-alpha-report")) == {"public-index-wait"}
    assert "remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS)" in public_alpha_report_recipe
    assert "--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL)" in public_alpha_report_recipe
    assert "> $(PUBLIC_ALPHA_REPORT_OUTPUT)" in public_alpha_report_recipe
    assert "cat $(PUBLIC_ALPHA_REPORT_OUTPUT)" in public_alpha_report_recipe

    public_index_report_recipe = make_target_recipe(makefile, "public-index-observation-report")
    assert set(make_target_prerequisites(makefile, "public-index-observation-report")) == {
        "public-index-wait"
    }
    assert "remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS)" in public_index_report_recipe
    assert "--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL)" in public_index_report_recipe
    assert "> $(PUBLIC_INDEX_OBSERVATION_REPORT_OUTPUT)" in public_index_report_recipe
    assert "cat $(PUBLIC_INDEX_OBSERVATION_REPORT_OUTPUT)" in public_index_report_recipe

    pages_alpha_recipe = make_target_recipe(makefile, "pages-alpha-smoke")
    assert set(make_target_prerequisites(makefile, "pages-alpha-smoke")) == {"pages-smoke"}
    assert "remote package $(PUBLIC_ALPHA_SMOKE_PACKAGE)" in pages_alpha_recipe
    assert "remote version $(PUBLIC_ALPHA_SMOKE_VERSION)" in pages_alpha_recipe
    assert "remote search $(PUBLIC_ALPHA_SMOKE_CAPABILITY)" in pages_alpha_recipe
    assert "--registry $(PAGES_REGISTRY_URL)" in pages_alpha_recipe

    pages_alpha_report_recipe = make_target_recipe(makefile, "pages-alpha-report")
    assert make_target_prerequisites(makefile, "pages-alpha-report") == []
    assert "remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS)" in pages_alpha_report_recipe
    assert "--registry $(PAGES_REGISTRY_URL)" in pages_alpha_report_recipe
    assert "> $(PAGES_ALPHA_REPORT_OUTPUT)" in pages_alpha_report_recipe
    assert "cat $(PAGES_ALPHA_REPORT_OUTPUT)" in pages_alpha_report_recipe

    pages_report_recipe = make_target_recipe(makefile, "pages-observation-report")
    assert make_target_prerequisites(makefile, "pages-observation-report") == []
    assert "remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS)" in pages_report_recipe
    assert "--registry $(PAGES_REGISTRY_URL)" in pages_report_recipe
    assert "> $(PAGES_OBSERVATION_REPORT_OUTPUT)" in pages_report_recipe
    assert "cat $(PAGES_OBSERVATION_REPORT_OUTPUT)" in pages_report_recipe

    assert set(make_target_prerequisites(makefile, "registry-observation-reports")) == {
        "public-index-observation-report",
        "pages-observation-report",
    }

    for text in (readme, agent_instructions, deploy_doc, docc_deployment):
        assert "make dev-reload" in text
        assert "make pages-smoke" in text

    for text in (readme, deploy_doc, docc_deployment):
        assert "make pages-alpha-smoke" in text
        assert "make pages-alpha-report" in text
        assert "make pages-observation-report" in text

    assert "make public-alpha-smoke" in deploy_doc
    assert "make public-alpha-report" in deploy_doc
    assert "make public-index-observation-report" in deploy_doc
    assert "make public-alpha-smoke" in docc_deployment
    assert "make public-alpha-report" in docc_deployment
    assert "make public-index-observation-report" in docc_deployment

    assert "Backup Strategy" in deploy_doc
    assert "Flood and DDoS Boundary" in deploy_doc
    assert "does not introduce a remote mutation API" in deploy_doc
    assert "online intent-to-spec runtime" in deploy_doc
    assert "<doc:Deployment>" in docc_overview


def test_registry_operations_runbook_documents_deploy_backup_and_abuse_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    deploy_doc = DEPLOY_FIRST_DOC.read_text(encoding="utf-8")
    operations_doc = REGISTRY_OPERATIONS_DOC.read_text(encoding="utf-8")
    docc_registry_operations = DOCC_REGISTRY_OPERATIONS_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    required_sections = (
        "Fresh Version Deployment",
        "Rollback",
        "Backup and Restore",
        "Flood, DDoS, and Abuse Controls",
        "Future Online APIs",
        "Operational Boundaries",
    )
    for section in required_sections:
        assert section in operations_doc

    for required_text in (
        "local Docker Compose public index at `http://localhost:8081`",
        "GitHub Pages static public index at `https://0al-spec.github.io/SpecPM`",
        "served under the `/v0` path prefix",
        "GitHub Pages static public index",
        "public-index/accepted-packages.yml",
        "make dev-reload",
        "make pages-smoke",
        "no remote mutation API",
        "no unauthenticated upload endpoint",
        "LLM token and cost budgets",
        "online intent-to-spec runtime",
        "Package content cannot command the host.",
    ):
        assert required_text in operations_doc
    assert "http://localhost:8081/v0" not in operations_doc
    assert "https://0al-spec.github.io/SpecPM/v0" not in operations_doc

    assert "specs/REGISTRY_OPERATIONS.md" in readme
    assert "specs/REGISTRY_OPERATIONS.md" in deploy_doc
    assert "specs/REGISTRY_OPERATIONS.md" in docc_registry_operations
    assert "<doc:RegistryOperations>" in docc_overview

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.deployment.registry_operations_runbook" in manifest_capabilities
    assert "specpm.deployment.registry_operations_runbook" in boundary_capabilities
    assert "specs/REGISTRY_OPERATIONS.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/RegistryOperations.md" in evidence_paths


def test_static_registry_pipeline_doc_explains_build_time_api_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    docc_pipeline = DOCC_STATIC_REGISTRY_PIPELINE_PAGE.read_text(encoding="utf-8")
    docc_deployment = DOCC_DEPLOYMENT_PAGE.read_text(encoding="utf-8")
    docc_registry_operations = DOCC_REGISTRY_OPERATIONS_PAGE.read_text(encoding="utf-8")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for required_text in (
        "build-time API",
        "No request-time server computes registry responses",
        "GitHub Pages only serves the generated artifact",
        "GitHub Issue: Add SpecPackage(s)",
        "GitHub Actions validation",
        "Maintainer review",
        "public-index/accepted-packages.yml",
        "specpm public-index generate",
        "/v0 static JSON registry API",
        "GET /v0/status",
        "GET /v0/packages",
        "GET /v0/packages/{package_id}",
        "GET /v0/packages/{package_id}/versions/{version}",
        "GET /v0/capabilities/{capability_id}/packages",
        "/v0/status/index.json",
        "make dev-reload",
        "Package content cannot command the host.",
        "online intent-to-spec runtime",
    ):
        assert required_text in docc_pipeline

    for excluded_feature_text in (
        "package upload",
        "remote mutation APIs",
        "package content execution",
        "semantic search",
    ):
        assert excluded_feature_text in docc_pipeline

    assert "Static Registry Pipeline" in readme
    assert "<doc:StaticRegistryPipeline>" in docc_overview
    assert "<doc:StaticRegistryPipeline>" in docc_deployment
    assert "<doc:StaticRegistryPipeline>" in docc_registry_operations
    assert "Static Registry Pipeline Documentation" in workplan

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    owned_binding_paths = {
        path
        for binding in boundary["implementationBindings"]
        for path in binding["files"].get("owned", [])
    }
    assert "specpm.registry.static_registry_pipeline_docs" in manifest_capabilities
    assert "specpm.registry.static_registry_pipeline_docs" in boundary_capabilities
    assert "Sources/SpecPM/Documentation.docc/StaticRegistryPipeline.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/StaticRegistryPipeline.md" in owned_binding_paths


def test_current_roadmap_documents_alpha_status_and_next_tracks() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    docc_roadmap = DOCC_ROADMAP_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    workplan = (ROOT / "specs/WORKPLAN.md").read_text(encoding="utf-8")
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    for required_text in (
        "Current Alpha Baseline",
        "Roadmap Principles",
        "Milestone 1: Alpha Stabilization",
        "Milestone 2: Public Index Operator UX",
        "Milestone 3: Downstream Consumer Integration",
        "Milestone 4: Remote Package Acquisition Design",
        "Milestone 5: Trust, Provenance, and Governance",
        "Milestone 6: Enterprise Registry Track",
        "Milestone 7: Intent Resolver Track",
        "Explicit Non-Goals For SpecPM Core",
        "Recent Progress",
        "Next Planned Sequence",
        "Public Index Operator UX baseline is complete",
        "accepted-manifest pull request helper",
        "SpecGraph public registry observation contract",
        "Reusable registry observation reports",
        "GitHub Actions runtime maintenance",
        "GitHub Actions permissions and secret-boundary policy",
        "pull_request_target",
        "remote package acquisition boundary",
        "intent taxonomy governance",
        "Package signing and revocation policy",
        "Provenance receipt schema and audit evidence profile",
        "implementation: public static provenance receipt artifacts",
        "Public index operator flow hardening",
        "label transition policy",
        "terminal label ownership",
        "Downstream Registry Consumer Contract",
        "endpoint classes",
        "failure vocabulary",
        "Producer candidate bundle contract alignment",
        "producer-receipt.json",
        "Package content can describe desired outputs. Package content cannot command the host.",
    ):
        assert required_text in roadmap

    for required_text in (
        "Current Alpha Baseline",
        "Alpha Stabilization",
        "Public Index Operator UX",
        "Downstream Consumer Integration",
        "Remote Package Acquisition Design",
        "Trust, Provenance, and Governance",
        "Enterprise Registry Track",
        "Intent Resolver Track",
        "Next Planned Sequence",
        "accepted-manifest pull request drafts",
        "SpecGraph public registry observation contract",
        "Reusable registry observation reports now write",
        "GitHub Actions runtime maintenance",
        "GitHub Actions permissions and secret-boundary policy",
        "pull_request_target",
        "remote package acquisition boundary",
        "intent taxonomy governance",
        "Package signing and revocation policy",
        "Provenance receipt schema and audit evidence profile",
        "public static provenance receipt JSON artifacts",
        "Public index operator flow hardening",
        "label transition policy",
        "terminal label ownership",
        "Downstream registry consumer contract",
        "endpoint classes",
        "failure vocabulary",
        "Producer candidate bundle contract alignment",
        "producer-receipt.json",
        "Package content can describe desired outputs. Package content cannot command the host.",
    ):
        assert required_text in docc_roadmap

    assert "Active stack:" not in roadmap
    assert "[`ROADMAP.md`](ROADMAP.md)" in readme
    assert "https://0al-spec.github.io/SpecPM/documentation/specpm/roadmap/" in readme
    assert "<doc:Roadmap>" in docc_overview
    assert "Phase 38. Static Registry Pipeline Documentation" in workplan
    assert "Phase 39. Current Roadmap" in workplan
    for phase_heading in (
        "Phase 48. Roadmap and Next Stack Documentation",
        "Phase 49. Accepted Manifest PR Helper",
        "Phase 50. SpecGraph Registry Observation Contract",
        "Phase 51. Reusable Registry Observation Reports",
        "Phase 52. Remote Package Acquisition Boundary",
        "Phase 53. Intent Taxonomy Governance",
        "Phase 54. GitHub Actions Maintenance Policy",
        "Phase 55. GitHub Actions Permissions and Secret Boundary",
        "Phase 56. Package Signing and Revocation Policy",
        "Phase 57. Provenance Receipt Schema and Audit Evidence Profile",
        "Phase 60. Public Index Operator UX Hardening",
        "Phase 61. Downstream Registry Consumer Contract",
        "Phase 63. Producer Candidate Bundle Contract Alignment",
    ):
        assert phase_heading in workplan

    phase_numbers = [
        int(match.group(1)) for match in re.finditer(r"^## Phase (\d+)\.", workplan, re.MULTILINE)
    ]
    assert phase_numbers == sorted(phase_numbers)
    assert len(phase_numbers) == len(set(phase_numbers))

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    owned_binding_paths = {
        path
        for binding in boundary["implementationBindings"]
        for path in binding["files"].get("owned", [])
    }
    assert "specpm.roadmap.current_status" in manifest_capabilities
    assert "specpm.roadmap.current_status" in boundary_capabilities
    assert "ROADMAP.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/Roadmap.md" in evidence_paths
    assert "ROADMAP.md" in owned_binding_paths


def test_public_alpha_registry_seed_is_manifested_and_documented() -> None:
    accepted_manifest = load_yaml_file(PUBLIC_INDEX_ACCEPTED_MANIFEST)
    public_alpha_doc = PUBLIC_ALPHA_DOC.read_text(encoding="utf-8")
    docc_public_alpha = DOCC_PUBLIC_ALPHA_PAGE.read_text(encoding="utf-8")
    docc_overview = (ROOT / "Sources/SpecPM/Documentation.docc/SpecPM.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    package_entries = accepted_manifest["packages"]
    assert {"path": "examples/email_tools"} in package_entries
    assert {"path": "."} in package_entries
    assert {
        "repository": "https://github.com/0al-spec/SpecNode.git",
        "ref": SPECNODE_RELEASE_REF,
        "revision": SPECNODE_RELEASE_REVISION,
        "path": ".",
    } in package_entries

    for text in (public_alpha_doc, docc_public_alpha, readme):
        assert "https://0al-spec.github.io/SpecPM" in text
        assert "specpm.core" in text
        assert "specnode.core" in text

    assert "specnode.typed_job_protocol" in public_alpha_doc
    assert "specpm remote package specnode.core" in public_alpha_doc
    assert "specpm remote version specnode.core@0.1.0" in public_alpha_doc
    assert "specpm remote observe" in public_alpha_doc
    assert "--intent intent.registry.intent_lookup" in public_alpha_doc
    assert "make pages-alpha-smoke" in public_alpha_doc
    assert "make pages-alpha-report" in public_alpha_doc
    assert "make pages-observation-report" in public_alpha_doc
    assert "make pages-alpha-smoke" in docc_public_alpha
    assert "make pages-alpha-report" in docc_public_alpha
    assert "make pages-observation-report" in docc_public_alpha
    assert SPECNODE_RELEASE_REF in public_alpha_doc
    assert SPECNODE_RELEASE_REVISION in public_alpha_doc
    assert "<doc:PublicAlphaRegistry>" in docc_overview

    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    assert "specpm.registry.public_alpha_index" in boundary_capabilities
    assert "specpm.registry.public_alpha_smoke" in boundary_capabilities
    assert "specpm.registry.public_observation_report" in boundary_capabilities
    assert "specs/PUBLIC_ALPHA.md" in evidence_paths
    assert "Sources/SpecPM/Documentation.docc/PublicAlphaRegistry.md" in evidence_paths


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


def sample_valid_submission_report(
    *,
    repository: str = "https://github.com/example/email-tools.git",
    ref: str = "main",
    revision: str = "a" * 40,
    path: str = ".",
    package_id: str = "document_conversion.email_tools",
    version: str = "0.1.0",
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "status": "valid",
        "package_path": path,
        "repository_count": 1,
        "repositories": [
            {
                "url": repository,
                "status": "valid",
                "stage": "validate",
                "package_identity": {
                    "package_id": package_id,
                    "version": version,
                },
                "source": {
                    "repository": repository,
                    "ref": ref,
                    "revision": revision,
                    "path": path,
                },
                "error_count": 0,
                "warning_count": 0,
                "errors": [],
                "warnings": [],
            }
        ],
        "errors": [],
    }


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


def test_submission_manifest_candidate_yaml_contains_valid_sources_only() -> None:
    report = {
        "status": "valid",
        "repositories": [
            {
                "status": "valid",
                "source": {
                    "repository": "https://github.com/example/email-tools.git",
                    "ref": "main",
                    "revision": "a" * 40,
                    "path": ".",
                },
            },
            {
                "status": "invalid",
                "source": {
                    "repository": "https://github.com/example/broken.git",
                    "ref": "main",
                    "revision": "b" * 40,
                    "path": ".",
                },
            },
        ],
    }

    payload = yaml.safe_load(render_accepted_manifest_candidate_yaml(report))

    assert accepted_manifest_candidates(report) == [
        {
            "repository": "https://github.com/example/email-tools.git",
            "ref": "main",
            "revision": "a" * 40,
            "path": ".",
        }
    ]
    assert payload == {
        "schemaVersion": 1,
        "packages": [
            {
                "repository": "https://github.com/example/email-tools.git",
                "ref": "main",
                "revision": "a" * 40,
                "path": ".",
            }
        ],
    }


def test_submission_manifest_candidate_yaml_is_empty_when_report_invalid() -> None:
    payload = yaml.safe_load(
        render_accepted_manifest_candidate_yaml(
            {
                "status": "invalid",
                "repositories": [
                    {
                        "status": "valid",
                        "source": {
                            "repository": "https://github.com/example/email-tools.git",
                            "ref": "main",
                            "revision": "a" * 40,
                            "path": ".",
                        },
                    }
                ],
            }
        )
    )

    assert payload == {"schemaVersion": 1, "packages": []}


def test_submission_cli_writes_manifest_candidate_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    issue_body = tmp_path / "issue.md"
    candidate_output = tmp_path / "candidate.yml"
    issue_body.write_text(sample_submission_issue_body(), encoding="utf-8")

    def fake_validate_submission_body(body: str, *, clone_root: Path | None) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "status": "valid",
            "package_path": ".",
            "repository_count": 1,
            "repositories": [
                {
                    "status": "valid",
                    "source": {
                        "repository": "https://github.com/example/email-tools.git",
                        "ref": "main",
                        "revision": "a" * 40,
                        "path": ".",
                    },
                }
            ],
            "errors": [],
        }

    monkeypatch.setattr(
        index_submission_module,
        "validate_submission_body",
        fake_validate_submission_body,
    )

    exit_code = index_submission_module.main(
        [
            "--issue-body-file",
            str(issue_body),
            "--manifest-candidate-output",
            str(candidate_output),
        ]
    )

    payload = yaml.safe_load(candidate_output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["packages"][0]["revision"] == "a" * 40


def test_prepare_accepted_manifest_pr_applies_candidate_and_writes_pr_body(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - path: examples/email_tools",
                "",
            ]
        ),
        encoding="utf-8",
    )
    report = sample_valid_submission_report()

    update = prepare_accepted_manifest_pr(
        report,
        manifest,
        issue_url="https://github.com/0al-spec/SpecPM/issues/123",
        apply_update=True,
    )
    pr_body = render_accepted_manifest_pr_body(update)
    manifest_payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))

    assert update["status"] == "applied"
    assert update["applied"] is True
    assert update["added_count"] == 1
    assert update["skipped_count"] == 0
    assert manifest_payload["packages"] == [
        {"path": "examples/email_tools"},
        {
            "repository": "https://github.com/example/email-tools.git",
            "ref": "main",
            "revision": "a" * 40,
            "path": ".",
        },
    ]
    assert "https://github.com/0al-spec/SpecPM/issues/123" in pr_body
    assert "`document_conversion.email_tools@0.1.0`" in pr_body
    assert "ref `main` at `" in pr_body
    assert "Pending maintainer/CI validation" in pr_body
    assert "Does not decide package acceptance automatically" in pr_body


def test_prepare_accepted_manifest_pr_rewrites_flow_style_manifest_structurally(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text("schemaVersion: 1\npackages: []\n", encoding="utf-8")

    update = prepare_accepted_manifest_pr(
        sample_valid_submission_report(),
        manifest,
        apply_update=True,
    )
    manifest_payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))

    assert update["status"] == "applied"
    assert manifest_payload == {
        "schemaVersion": 1,
        "packages": [
            {
                "repository": "https://github.com/example/email-tools.git",
                "ref": "main",
                "revision": "a" * 40,
                "path": ".",
            }
        ],
    }


def test_prepare_accepted_manifest_pr_skips_exact_duplicate_source(tmp_path: Path) -> None:
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "\n".join(
            [
                "schemaVersion: 1",
                "packages:",
                "  - repository: https://github.com/example/email-tools.git",
                "    ref: main",
                f"    revision: {'a' * 40}",
                "    path: .",
                "",
            ]
        ),
        encoding="utf-8",
    )
    original_manifest = manifest.read_text(encoding="utf-8")

    update = prepare_accepted_manifest_pr(
        sample_valid_submission_report(),
        manifest,
        apply_update=True,
    )

    assert update["status"] == "unchanged"
    assert update["applied"] is False
    assert update["added_count"] == 0
    assert update["skipped_count"] == 1
    assert update["skipped"][0]["reason"] == "exact_source_already_present"
    assert manifest.read_text(encoding="utf-8") == original_manifest


def test_prepare_accepted_manifest_pr_handles_multiple_valid_sources(tmp_path: Path) -> None:
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "schemaVersion: 1\npackages:\n  - path: examples/email_tools\n", encoding="utf-8"
    )
    report = sample_valid_submission_report()
    second = sample_valid_submission_report(
        repository="https://github.com/example/pdf-tools.git",
        revision="b" * 40,
        package_id="document_conversion.pdf_tools",
        version="0.2.0",
    )["repositories"][0]
    report["repositories"].append(second)
    report["repository_count"] = 2

    update = prepare_accepted_manifest_pr(report, manifest, apply_update=False)

    assert update["status"] == "prepared"
    assert update["applied"] is False
    assert update["candidate_count"] == 2
    assert update["added_count"] == 2
    assert [item["package_ref"] for item in update["added"]] == [
        "document_conversion.email_tools@0.1.0",
        "document_conversion.pdf_tools@0.2.0",
    ]
    assert yaml.safe_load(manifest.read_text(encoding="utf-8"))["packages"] == [
        {"path": "examples/email_tools"}
    ]


def test_prepare_accepted_manifest_pr_rejects_invalid_submission_report(tmp_path: Path) -> None:
    manifest = tmp_path / "accepted-packages.yml"
    manifest.write_text(
        "schemaVersion: 1\npackages:\n  - path: examples/email_tools\n", encoding="utf-8"
    )

    update = prepare_accepted_manifest_pr(
        {
            "schemaVersion": 1,
            "status": "invalid",
            "repositories": [],
            "errors": [
                {
                    "severity": "error",
                    "code": "package_urls_missing",
                    "message": "At least one package URL is required.",
                }
            ],
        },
        manifest,
        apply_update=True,
    )

    assert update["status"] == "invalid"
    assert update["applied"] is False
    assert issue_codes(update["errors"]) == {
        "submission_report_invalid",
        "accepted_manifest_candidates_missing",
    }


def test_prepare_accepted_manifest_pr_cli_writes_report_and_body(tmp_path: Path) -> None:
    submission_report = tmp_path / "submission-report.json"
    manifest = tmp_path / "accepted-packages.yml"
    helper_report = tmp_path / "accepted-manifest-pr-report.json"
    pr_body = tmp_path / "accepted-manifest-pr.md"
    submission_report.write_text(
        json.dumps(sample_valid_submission_report()),
        encoding="utf-8",
    )
    manifest.write_text(
        "schemaVersion: 1\npackages:\n  - path: examples/email_tools\n", encoding="utf-8"
    )

    exit_code = index_submission_module.prepare_accepted_manifest_pr_main(
        [
            "--submission-report",
            str(submission_report),
            "--manifest",
            str(manifest),
            "--issue-url",
            "https://github.com/0al-spec/SpecPM/issues/123",
            "--apply",
            "--json-output",
            str(helper_report),
            "--pr-body-output",
            str(pr_body),
        ]
    )

    payload = json.loads(helper_report.read_text(encoding="utf-8"))
    manifest_payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["status"] == "applied"
    assert payload["added"][0]["source"]["revision"] == "a" * 40
    assert (
        manifest_payload["packages"][1]["repository"]
        == "https://github.com/example/email-tools.git"
    )
    assert "document_conversion.email_tools@0.1.0" in pr_body.read_text(encoding="utf-8")


def test_rfc_example_validates() -> None:
    report = validate_package(ROOT / "examples/email_tools")

    assert report["status"] == "valid"
    assert report["error_count"] == 0
    assert report["capabilities"] == ["document_conversion.email_to_markdown"]


def test_reference_abstract_email_contract_validates() -> None:
    package_root = ROOT / "examples/abstract_email_to_markdown_contract"
    report = validate_package(package_root)

    assert report["status"] == "valid"
    assert report["error_count"] == 0
    assert report["capabilities"] == ["intent.document_conversion.email_to_markdown.contract"]

    manifest = yaml.safe_load((package_root / "specpm.yaml").read_text(encoding="utf-8"))
    spec = yaml.safe_load(
        (package_root / "specs/email-to-markdown-intent.spec.yaml").read_text(encoding="utf-8")
    )

    assert manifest["index"]["provides"]["intents"] == [
        "intent.document_conversion.email_to_markdown"
    ]
    assert "abstract contract" in manifest["keywords"]
    assert "provider neutral" in manifest["keywords"]
    assert spec["implementationBindings"] == []
    assert "abstract contract" in spec["keywords"]
    assert "provider neutral" in spec["keywords"]
    assert any("compose" in item.lower() for item in spec["scope"]["includes"])


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
        "version": "0.2.0",
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
        "specpm.registry.public_alpha_index",
        "specpm.registry.public_alpha_smoke",
        "specpm.registry.public_observation_report",
        "specpm.deployment.deploy_first_workflow",
        "specpm.deployment.registry_operations_runbook",
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


def test_repository_agent_skills_are_installable_and_self_described() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    skills_readme = (ROOT / "skills/README.md").read_text(encoding="utf-8")
    docc_skills = (ROOT / "Sources/SpecPM/Documentation.docc/AgentSkills.md").read_text(
        encoding="utf-8"
    )
    manifest = load_yaml_file(ROOT / "specpm.yaml")
    boundary = load_yaml_file(ROOT / "specs/specpm.spec.yaml")

    manifest_capabilities = set(manifest["index"]["provides"]["capabilities"])
    boundary_capabilities = {
        capability["id"] for capability in boundary["provides"]["capabilities"]
    }
    evidence_paths = {evidence["path"] for evidence in boundary["evidence"]}
    owned_binding_paths = {
        path
        for binding in boundary["implementationBindings"]
        for path in binding["files"].get("owned", [])
    }

    for skill_name, expected in AGENT_SKILLS.items():
        skill_dir = AGENT_SKILL_ROOT / skill_name
        skill_doc = skill_dir / "SKILL.md"
        agent_config = skill_dir / "agents/openai.yaml"
        reference_doc = skill_dir / expected["reference"]
        license_doc = skill_dir / "LICENSE.txt"
        repo_skill_path = f"skills/.experimental/{skill_name}"

        assert skill_doc.is_file()
        assert agent_config.is_file()
        assert reference_doc.is_file()
        assert license_doc.is_file()

        skill_text = skill_doc.read_text(encoding="utf-8")
        assert f"name: {skill_name}" in skill_text
        assert "description:" in skill_text
        assert expected["reference"] in skill_text

        agent = load_yaml_file(agent_config)
        assert f"${skill_name}" in agent["interface"]["default_prompt"]
        assert agent["interface"]["display_name"].startswith("SpecPM")

        assert "MIT License" in license_doc.read_text(encoding="utf-8")
        assert repo_skill_path in readme
        assert repo_skill_path in skills_readme
        assert repo_skill_path in docc_skills
        assert expected["capability"] in manifest_capabilities
        assert expected["capability"] in boundary_capabilities
        assert f"{repo_skill_path}/SKILL.md" in evidence_paths
        assert f"{repo_skill_path}/SKILL.md" in owned_binding_paths


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

    fixture_root = (ROOT / "tests/fixtures/conformance").resolve()
    for case in remote_cases:
        payload_path = (ROOT / case["payload"]).resolve()
        assert payload_path.is_relative_to(fixture_root), case["id"]
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict), case["id"]
        validation_errors = validate_remote_registry_payload(payload)

        expected = case["expected"]
        if expected.get("validation_status") == "invalid":
            assert issue_codes([issue.to_dict() for issue in validation_errors]) == set(
                expected["validation_error_codes"]
            ), case["id"]
            continue

        assert validation_errors == [], case["id"]
        assert_remote_registry_payload_shape(payload)
        assert payload["kind"] == expected["kind"], case["id"]
        assert payload["status"] == expected["status"], case["id"]
        if payload["kind"] == "RemoteRegistryError":
            assert payload["error"]["code"] == expected["error_code"], case["id"]
        if "profile" in expected:
            assert payload["registry"]["profile"] == expected["profile"], case["id"]
        if "package_count" in expected:
            actual = (
                payload["registry"]["package_count"]
                if payload["kind"] in {"RemoteRegistryRoot", "RemoteRegistryStatus"}
                else payload["package_count"]
            )
            assert actual == expected["package_count"], case["id"]
        if "version_count" in expected:
            actual = (
                payload["registry"]["version_count"]
                if payload["kind"] in {"RemoteRegistryRoot", "RemoteRegistryStatus"}
                else payload["version_count"]
            )
            assert actual == expected["version_count"], case["id"]
        if "intent_count" in expected:
            actual = (
                payload["registry"]["intent_count"]
                if payload["kind"] in {"RemoteRegistryRoot", "RemoteRegistryStatus"}
                else payload["intent_count"]
            )
            assert actual == expected["intent_count"], case["id"]
        if "package_id" in expected:
            assert payload["package"]["package_id"] == expected["package_id"], case["id"]
        if expected.get("intent_entry_id"):
            assert payload["intent"]["intent_id"] == expected["intent_entry_id"], case["id"]
        if "version" in expected:
            assert payload["package"]["version"] == expected["version"], case["id"]
        if "yanked" in expected:
            assert payload["package"]["state"]["yanked"] is expected["yanked"], case["id"]
        if "deprecated" in expected:
            assert payload["package"]["state"]["deprecated"] is expected["deprecated"], case["id"]
        if "capability_id" in expected:
            assert payload["query"]["capability_id"] == expected["capability_id"], case["id"]
        if "intent_id" in expected:
            assert payload["query"]["intent_id"] == expected["intent_id"], case["id"]
        if "result_count" in expected:
            assert payload["result_count"] == expected["result_count"], case["id"]


def test_conformance_fixture_manifest_declares_versioned_payload_sets() -> None:
    suite = load_conformance_suite()
    manifest = json.loads(CONFORMANCE_FIXTURE_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["apiVersion"] == "specpm.fixture-manifest/v0"
    assert manifest["schemaVersion"] == 1
    assert manifest["suite"] == suite["suite"]
    assert manifest["registryApiVersion"] == "specpm.registry/v0"
    assert manifest["consumerPinning"] == {
        "required": True,
        "rootOfTrust": "consumer_pinned_specpm_commit",
        "statement": (
            "Downstream consumers must pin the SpecPM repository revision externally; "
            "this manifest describes fixture metadata and is not a lock file."
        ),
    }

    fixture_sets = {fixture_set["id"]: fixture_set for fixture_set in manifest["fixtureSets"]}
    fixture_set_ids = list(fixture_sets)
    assert fixture_set_ids == [
        "remote_registry_static_smoke",
        "remote_registry_lifecycle_examples",
        "remote_registry_error_examples",
        "remote_registry_negative",
        "enterprise_registry_static_smoke",
    ]
    assert len(fixture_set_ids) == len(set(fixture_set_ids))

    declared_paths: set[str] = set()
    fixture_root = (ROOT / "tests/fixtures/conformance").resolve()
    for fixture_set in fixture_sets.values():
        assert fixture_set["description"]
        assert fixture_set["usage"] in {
            "http_static_smoke",
            "payload_validation",
            "negative_validation",
        }
        for fixture in fixture_set["fixtures"]:
            path = fixture["path"]
            assert path not in declared_paths
            declared_paths.add(path)
            assert isinstance(fixture["valid"], bool)

            payload_path = (ROOT / path).resolve()
            assert payload_path.is_relative_to(fixture_root), path
            assert payload_path.is_file(), path

            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            assert payload["apiVersion"] == manifest["registryApiVersion"], path
            assert payload["schemaVersion"] == 1, path
            assert payload["kind"] == fixture["kind"], path

    static_smoke = fixture_sets["remote_registry_static_smoke"]["fixtures"]
    assert [fixture["path"] for fixture in static_smoke] == [
        "tests/fixtures/conformance/remote_registry/registry-status.json",
        "tests/fixtures/conformance/remote_registry/package-index.json",
        "tests/fixtures/conformance/remote_registry/package-metadata.json",
        "tests/fixtures/conformance/remote_registry/package-version.json",
        "tests/fixtures/conformance/remote_registry/capability-search.json",
        "tests/fixtures/conformance/remote_registry/intent-index.json",
        "tests/fixtures/conformance/remote_registry/intent-metadata.json",
        "tests/fixtures/conformance/remote_registry/intent-search.json",
    ]
    assert all(fixture["valid"] is True for fixture in static_smoke)
    assert [fixture["staticPath"] for fixture in static_smoke] == [
        "v0/status/index.json",
        "v0/packages/index.json",
        "v0/packages/document_conversion.email_tools/index.json",
        "v0/packages/document_conversion.email_tools/versions/0.1.0/index.json",
        "v0/capabilities/document_conversion.email_to_markdown/packages/index.json",
        "v0/intents/index.json",
        "v0/intents/intent.document_conversion.email_to_markdown/index.json",
        "v0/intents/intent.document_conversion.email_to_markdown/packages/index.json",
    ]

    for fixture_set_id in (
        "remote_registry_lifecycle_examples",
        "remote_registry_error_examples",
        "remote_registry_negative",
    ):
        for fixture in fixture_sets[fixture_set_id]["fixtures"]:
            assert "staticPath" not in fixture

    negative_fixtures = fixture_sets["remote_registry_negative"]["fixtures"]
    assert [fixture["path"] for fixture in negative_fixtures] == [
        "tests/fixtures/conformance/remote_registry/invalid-package-index-count.json"
    ]
    assert all(fixture["valid"] is False for fixture in negative_fixtures)

    enterprise_smoke = fixture_sets["enterprise_registry_static_smoke"]["fixtures"]
    assert enterprise_smoke == [
        {
            "path": "tests/fixtures/conformance/enterprise_registry/registry-status.json",
            "kind": "RemoteRegistryStatus",
            "staticPath": "v0/status/index.json",
            "valid": True,
        }
    ]

    suite_payload_paths = {
        case["payload"] for case in suite["cases"] if case["kind"] == "remote_registry_payload"
    }
    assert declared_paths == suite_payload_paths


def test_conformance_public_registry_static_index_cases(tmp_path: Path) -> None:
    suite = load_conformance_suite()
    public_cases = [
        case for case in suite["cases"] if case["kind"] == "public_registry_static_index"
    ]
    assert public_cases

    for case in public_cases:
        output = tmp_path / case["id"]
        report = generate_public_index(
            [ROOT / case["package"]],
            output,
            case["registry"],
        )
        expected = case["expected"]
        assert report["status"] == expected["status"], case["id"]
        assert sorted(report["written_files"]) == report["written_files"], case["id"]

        for endpoint in expected["endpoints"]:
            endpoint_path = output / endpoint["path"]
            assert endpoint_path.is_file(), f"{case['id']} missing {endpoint['path']}"
            payload = json.loads(endpoint_path.read_text(encoding="utf-8"))
            assert validate_remote_registry_payload(payload) == [], case["id"]
            assert_remote_registry_payload_shape(payload)
            assert payload["kind"] == endpoint["kind"], case["id"]
            assert payload["status"] == endpoint["status"], case["id"]
            if "package_count" in endpoint:
                actual = (
                    payload["registry"]["package_count"]
                    if payload["kind"] in {"RemoteRegistryRoot", "RemoteRegistryStatus"}
                    else payload["package_count"]
                )
                assert actual == endpoint["package_count"], case["id"]
            if "version_count" in endpoint:
                actual = (
                    payload["registry"]["version_count"]
                    if payload["kind"] in {"RemoteRegistryRoot", "RemoteRegistryStatus"}
                    else payload["version_count"]
                )
                assert actual == endpoint["version_count"], case["id"]
            if "intent_count" in endpoint:
                actual = (
                    payload["registry"]["intent_count"]
                    if payload["kind"] in {"RemoteRegistryRoot", "RemoteRegistryStatus"}
                    else payload["intent_count"]
                )
                assert actual == endpoint["intent_count"], case["id"]
            if "package_id" in endpoint:
                assert payload["package"]["package_id"] == endpoint["package_id"], case["id"]
            if endpoint.get("intent_entry_id"):
                assert payload["intent"]["intent_id"] == endpoint["intent_entry_id"], case["id"]
            if "version" in endpoint:
                assert payload["package"]["version"] == endpoint["version"], case["id"]
            if "capability_id" in endpoint:
                assert payload["query"]["capability_id"] == endpoint["capability_id"], case["id"]
            if "intent_id" in endpoint:
                assert payload["query"]["intent_id"] == endpoint["intent_id"], case["id"]
            if "result_count" in endpoint:
                assert payload["result_count"] == endpoint["result_count"], case["id"]

            html_path = endpoint_path.with_name("index.html")
            assert html_path.is_file(), f"{case['id']} missing {html_path.relative_to(output)}"
            assert json.loads(html_path.read_text(encoding="utf-8")) == payload

        archive = output / expected["archive"]
        version_payload = json.loads(
            (output / expected["version_endpoint"]).read_text(encoding="utf-8")
        )
        assert archive.is_file(), case["id"]
        assert version_payload["package"]["source"]["digest"]["value"] == sha256_path(archive)
        assert version_payload["package"]["source"]["size"] == archive.stat().st_size

        for missing_path in expected.get("absent_paths", []):
            assert not (output / missing_path).exists(), case["id"]


def test_remote_registry_payload_validator_rejects_incomplete_source() -> None:
    payload = load_remote_registry_fixture("capability-search.json")
    del payload["results"][0]["source"]["size"]

    errors = validate_remote_registry_payload(payload)

    assert any(
        issue.code == "remote_registry_field_invalid" and issue.field == "results.0.source.size"
        for issue in errors
    )


def test_remote_registry_payload_validator_rejects_non_string_result_lists() -> None:
    payload = load_remote_registry_fixture("intent-search.json")
    payload["results"][0]["matched_capabilities"] = ["document_conversion.email_to_markdown", 123]
    payload["results"][0]["provided_capabilities"] = [None]
    payload["results"][0]["required_capabilities"] = [""]

    errors = validate_remote_registry_payload(payload)

    assert {issue.field for issue in errors if issue.code == "remote_registry_field_invalid"} >= {
        "results.0.matched_capabilities.1",
        "results.0.provided_capabilities.0",
        "results.0.required_capabilities.0",
    }


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


def test_remote_registry_search_fetches_exact_intent(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    payload = load_remote_registry_fixture("intent-search.json")

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        captured["url"] = request.full_url
        captured["accept"] = request.get_header("Accept")
        captured["timeout"] = timeout
        return FakeRemoteResponse(payload)

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = search_remote_registry_intent(
        "https://registry.example.invalid",
        "intent.document_conversion.email_to_markdown",
        timeout=2.5,
    )

    assert report["status"] == "ok"
    assert report["payload"]["kind"] == "RemoteIntentSearch"
    assert report["payload"]["results"][0]["matched_capabilities"] == [
        "document_conversion.email_to_markdown"
    ]
    assert captured == {
        "url": (
            "https://registry.example.invalid/v0/intents/"
            "intent.document_conversion.email_to_markdown/packages"
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


def test_remote_registry_status_and_index_fetch_expected_endpoints(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payloads = {
        "https://registry.example.invalid/v0/status": (
            load_remote_registry_fixture("registry-status.json")
        ),
        "https://registry.example.invalid/v0/packages": (
            load_remote_registry_fixture("package-index.json")
        ),
        "https://registry.example.invalid/v0/intents": (
            load_remote_registry_fixture("intent-index.json")
        ),
        (
            "https://registry.example.invalid/v0/intents/"
            "intent.document_conversion.email_to_markdown"
        ): load_remote_registry_fixture("intent-metadata.json"),
    }
    seen: list[str] = []

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        seen.append(request.full_url)
        return FakeRemoteResponse(payloads[request.full_url])

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    status = get_remote_registry_status("https://registry.example.invalid")
    package_index = get_remote_package_index("https://registry.example.invalid")
    intent_index = get_remote_intent_index("https://registry.example.invalid")
    intent = get_remote_intent(
        "https://registry.example.invalid",
        "intent.document_conversion.email_to_markdown",
    )

    assert status["status"] == "ok"
    assert status["payload"]["kind"] == "RemoteRegistryStatus"
    assert status["payload"]["registry"]["profile"] == "public_static_index"
    assert package_index["status"] == "ok"
    assert package_index["payload"]["kind"] == "RemotePackageIndex"
    assert package_index["payload"]["package_count"] == 1
    assert intent_index["status"] == "ok"
    assert intent_index["payload"]["kind"] == "RemoteIntentIndex"
    assert intent_index["payload"]["intent_count"] == 1
    assert intent["status"] == "ok"
    assert intent["payload"]["kind"] == "RemoteIntent"
    assert intent["payload"]["intent"]["status"] == "observed"
    assert seen == list(payloads)


def test_remote_registry_observation_report_fetches_expected_alpha_surface(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payloads = {
        "https://registry.example.invalid/v0/status": (
            load_remote_registry_fixture("registry-status.json")
        ),
        "https://registry.example.invalid/v0/packages": (
            load_remote_registry_fixture("package-index.json")
        ),
        "https://registry.example.invalid/v0/packages/document_conversion.email_tools": (
            load_remote_registry_fixture("package-metadata.json")
        ),
        (
            "https://registry.example.invalid/v0/packages/"
            "document_conversion.email_tools/versions/0.1.0"
        ): load_remote_registry_fixture("package-version.json"),
        (
            "https://registry.example.invalid/v0/capabilities/"
            "document_conversion.email_to_markdown/packages"
        ): load_remote_registry_fixture("capability-search.json"),
        (
            "https://registry.example.invalid/v0/intents/"
            "intent.document_conversion.email_to_markdown/packages"
        ): load_remote_registry_fixture("intent-search.json"),
    }
    seen: list[str] = []

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        seen.append(request.full_url)
        assert timeout == 2.5
        return FakeRemoteResponse(payloads[request.full_url])

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = observe_remote_registry(
        "https://registry.example.invalid",
        package_ids=["document_conversion.email_tools"],
        package_refs=["document_conversion.email_tools@0.1.0"],
        capability_ids=["document_conversion.email_to_markdown"],
        intent_ids=["intent.document_conversion.email_to_markdown"],
        timeout=2.5,
    )

    assert report["schemaVersion"] == 1
    assert report["status"] == "ok"
    assert report["operation"] == "observe"
    assert report["summary"] == {
        "registry_status": "ok",
        "package_index_status": "ok",
        "package_count": 1,
        "version_count": 1,
        "capability_count": 1,
        "intent_count": 1,
        "check_count": 9,
        "failed_check_count": 0,
    }
    assert [check["status"] for check in report["checks"]] == ["ok"] * 9
    assert report["target"] == {
        "package_ids": ["document_conversion.email_tools"],
        "package_refs": ["document_conversion.email_tools@0.1.0"],
        "capability_ids": ["document_conversion.email_to_markdown"],
        "intent_ids": ["intent.document_conversion.email_to_markdown"],
    }
    assert report["observations"]["packages"]["document_conversion.email_tools"]["status"] == "ok"
    assert (
        report["observations"]["intents"]["intent.document_conversion.email_to_markdown"]["status"]
        == "ok"
    )
    assert seen == list(payloads)


def test_remote_registry_observation_report_fails_for_missing_capability(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    capability_payload = load_remote_registry_fixture("capability-search.json")
    capability_payload["result_count"] = 0
    capability_payload["results"] = []
    payloads = {
        "https://registry.example.invalid/v0/status": (
            load_remote_registry_fixture("registry-status.json")
        ),
        "https://registry.example.invalid/v0/packages": (
            load_remote_registry_fixture("package-index.json")
        ),
        (
            "https://registry.example.invalid/v0/capabilities/"
            "document_conversion.email_to_markdown/packages"
        ): capability_payload,
    }

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(payloads[request.full_url])

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    report = observe_remote_registry(
        "https://registry.example.invalid",
        capability_ids=["document_conversion.email_to_markdown"],
    )

    assert report["status"] == "invalid"
    assert report["summary"]["failed_check_count"] == 1
    assert issue_codes(report["errors"]) == {"remote_observation_capability_not_visible"}


def test_remote_registry_observation_report_omits_unknown_file_and_uses_verification_message() -> (
    None
):
    report = observe_remote_registry("not-a-url")

    assert report["status"] == "invalid"
    assert report["summary"]["failed_check_count"] == 2
    for error in report["errors"]:
        assert "file" not in error
        assert error["detail"]["endpoint"] is None
        assert "not available" not in error["message"]
        assert "could not be verified" in error["message"]


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
    root_payload = json.loads((output / "v0/index.json").read_text(encoding="utf-8"))
    root_directory_index = json.loads((output / "v0/index.html").read_text(encoding="utf-8"))
    status_payload = json.loads((output / "v0/status/index.json").read_text(encoding="utf-8"))
    package_index_payload = json.loads(
        (output / "v0/packages/index.json").read_text(encoding="utf-8")
    )
    intent_index_payload = json.loads(
        (output / "v0/intents/index.json").read_text(encoding="utf-8")
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
    receipt_path = (
        output
        / "v0/packages/document_conversion.email_tools/versions/0.1.0/"
        / "provenance-receipt/index.json"
    )
    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt_directory_index = json.loads(
        receipt_path.with_name("index.html").read_text(encoding="utf-8")
    )
    capability_payload = json.loads(
        (
            output / "v0/capabilities/document_conversion.email_to_markdown/packages/index.json"
        ).read_text(encoding="utf-8")
    )
    intent_payload = json.loads(
        (
            output / "v0/intents/intent.document_conversion.email_to_markdown/packages/index.json"
        ).read_text(encoding="utf-8")
    )
    intent_entry_payload = json.loads(
        (output / "v0/intents/intent.document_conversion.email_to_markdown/index.json").read_text(
            encoding="utf-8"
        )
    )
    archive = (
        output
        / "v0/packages/document_conversion.email_tools/versions/0.1.0/"
        / "document_conversion.email_tools-0.1.0.specpm.tgz"
    )

    assert archive.is_file()
    assert_remote_registry_payload_shape(root_payload)
    assert root_directory_index == root_payload
    assert_remote_registry_payload_shape(status_payload)
    assert_remote_registry_payload_shape(package_index_payload)
    assert_remote_registry_payload_shape(intent_index_payload)
    assert_remote_registry_payload_shape(package_payload)
    assert package_directory_index == package_payload
    assert_remote_registry_payload_shape(version_payload)
    assert_remote_registry_payload_shape(capability_payload)
    assert_remote_registry_payload_shape(intent_payload)
    assert_remote_registry_payload_shape(intent_entry_payload)
    assert root_payload["registry"] == status_payload["registry"]
    assert root_payload["endpoints"] == {
        "status": "v0/status/index.json",
        "packages": "v0/packages/index.json",
        "intents": "v0/intents/index.json",
    }
    assert status_payload["registry"] == {
        "profile": "public_static_index",
        "api_version": "v0",
        "read_only": True,
        "authority": "metadata_only",
        "package_count": 1,
        "version_count": 1,
        "capability_count": 1,
        "intent_count": 1,
        "provenance_receipt_count": 1,
        "implementation": {
            "name": "SpecPM",
            "version": __version__,
        },
    }
    assert intent_index_payload["catalog"] == {
        "authority": "observed_metadata_only",
        "canonical": False,
        "description": (
            "Observed intent IDs are collected from accepted package metadata; "
            "package declaration does not make an intent ID canonical."
        ),
    }
    assert intent_index_payload["intents"][0]["intent_id"] == (
        "intent.document_conversion.email_to_markdown"
    )
    assert intent_index_payload["intents"][0]["status"] == "observed"
    assert intent_index_payload["intents"][0]["canonical"] is False
    assert intent_index_payload["intents"][0]["package_ids"] == ["document_conversion.email_tools"]
    assert intent_entry_payload["intent"]["intent_id"] == (
        "intent.document_conversion.email_to_markdown"
    )
    assert intent_entry_payload["intent"]["status"] == "observed"
    assert intent_entry_payload["packages"][0]["matched_capabilities"] == [
        "document_conversion.email_to_markdown"
    ]
    assert package_index_payload["packages"][0]["package_id"] == ("document_conversion.email_tools")
    assert package_payload["package"]["latest_version"] == "0.1.0"
    assert capability_payload["results"][0]["matched_capability"] == (
        "document_conversion.email_to_markdown"
    )
    assert intent_payload["results"][0]["matched_intent"] == (
        "intent.document_conversion.email_to_markdown"
    )
    assert intent_payload["results"][0]["matched_capabilities"] == [
        "document_conversion.email_to_markdown"
    ]
    assert version_payload["package"]["source"]["url"] == (
        "https://registry.example.invalid/v0/packages/"
        "document_conversion.email_tools/versions/0.1.0/"
        "document_conversion.email_tools-0.1.0.specpm.tgz"
    )
    assert version_payload["package"]["provenance_receipt"]["url"] == (
        "https://registry.example.invalid/v0/packages/"
        "document_conversion.email_tools/versions/0.1.0/"
        "provenance-receipt/index.json"
    )
    assert version_payload["package"]["provenance_receipt"]["digest"]["value"] == sha256_path(
        receipt_path
    )
    assert version_payload["package"]["source"]["digest"]["value"] == sha256_path(archive)
    assert version_payload["package"]["source"]["size"] == archive.stat().st_size
    assert receipt_directory_index == receipt_payload
    assert receipt_payload["apiVersion"] == "specpm.receipts/v0"
    assert receipt_payload["kind"] == "SpecPMProvenanceReceipt"
    assert receipt_payload["receiptProfile"] == "public_static_index_build_v0"
    assert receipt_payload["receiptId"].startswith("document_conversion.email_tools@0.1.0:sha256:")
    assert receipt_payload["issuedAt"].endswith("Z")
    assert receipt_payload["subject"] == {
        "packageId": "document_conversion.email_tools",
        "version": "0.1.0",
        "registryProfile": "public_static_index",
    }
    assert receipt_payload["source"] == {
        "kind": "local_path",
        "path": "examples/email_tools",
    }
    assert receipt_payload["archive"] == version_payload["package"]["source"]
    assert receipt_payload["review"] == {"kind": "manual", "decision": "accepted"}
    assert receipt_payload["validation"] == {
        "status": "valid",
        "warningCount": 0,
        "errorCount": 0,
        "validatorVersion": __version__,
    }
    assert receipt_payload["trust"]["signatureStatus"] == "not_applicable"
    assert receipt_payload["lifecycle"]["state"] == "visible"
    assert receipt_payload["audit"]["evidence"]
    assert sorted(report["written_files"]) == report["written_files"]


def test_public_index_provenance_receipt_reports_warning_validation_status() -> None:
    package = public_index_receipt_test_package(
        validation={
            "status": "warning_only",
            "warnings": [
                {
                    "code": "example_warning",
                    "message": "Example warning.",
                }
            ],
            "errors": [],
        }
    )

    receipt = public_index_module.public_index_provenance_receipt(package, None)

    assert receipt["validation"]["status"] == "warning"
    assert receipt["validation"]["warningCount"] == 1
    assert receipt["validation"]["errorCount"] == 0


@pytest.mark.parametrize(
    ("state", "expected_state"),
    [
        ({"yanked": True, "deprecated": False}, "yanked"),
        ({"yanked": False, "deprecated": True}, "deprecated"),
        ({"revoked": True, "yanked": True, "deprecated": True}, "revoked"),
    ],
)
def test_public_index_provenance_receipt_summarizes_lifecycle_state(
    state: dict[str, Any],
    expected_state: str,
) -> None:
    package = public_index_receipt_test_package(state=state)

    receipt = public_index_module.public_index_provenance_receipt(package, None)

    assert receipt["lifecycle"]["state"] == expected_state
    assert receipt["lifecycle"]["yanked"] is (state.get("yanked") is True)
    assert receipt["lifecycle"]["deprecated"] is (state.get("deprecated") is True)
    assert receipt["lifecycle"]["revoked"] is (state.get("revoked") is True)


def test_public_index_generate_treats_identical_duplicate_version_as_noop(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    output = tmp_path / "site"
    shutil.copytree(ROOT / "examples/email_tools", first)
    shutil.copytree(ROOT / "examples/email_tools", second)

    report = generate_public_index(
        [first, second],
        output,
        "https://0al-spec.github.io/SpecPM",
    )

    package_payload = json.loads(
        (output / "v0/packages/document_conversion.email_tools/index.json").read_text(
            encoding="utf-8"
        )
    )
    status_payload = json.loads((output / "v0/status/index.json").read_text(encoding="utf-8"))

    assert report["status"] == "ok"
    assert status_payload["registry"]["package_count"] == 1
    assert status_payload["registry"]["version_count"] == 1
    assert package_payload["package"]["latest_version"] == "0.1.0"
    assert [item["version"] for item in package_payload["package"]["versions"]] == ["0.1.0"]
    assert (
        output / "v0/packages/document_conversion.email_tools/versions/0.1.0/index.json"
    ).is_file()


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


def test_public_index_generate_embeds_specpm_build_metadata(tmp_path: Path) -> None:
    output = tmp_path / "site"
    revision = "a" * 40

    report = generate_public_index(
        [ROOT / "examples/email_tools"],
        output,
        "https://registry.example.invalid",
        build_metadata={
            "version": "9.8.7",
            "build_number": "1234",
            "revision": revision,
        },
    )

    assert report["status"] == "ok"
    status_payload = json.loads((output / "v0/status/index.json").read_text(encoding="utf-8"))
    assert status_payload["registry"]["implementation"] == {
        "name": "SpecPM",
        "version": "9.8.7",
        "build": {
            "number": "1234",
            "revision": revision,
            "revision_short": revision[:12],
        },
    }
    assert validate_remote_registry_payload(status_payload) == []


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


def test_public_index_accepted_manifest_resolves_alpha_packages(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    remote_root = tmp_path / "remote-sources"

    def fake_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        if repository_url == "https://github.com/0al-spec/SpecPM.git":
            assert ref == SPECPM_RELEASE_REF
            write_fake_specpm_release_checkout(checkout)
            return {"status": "ok", "revision": SPECPM_RELEASE_REVISION, "errors": []}
        if repository_url == "https://github.com/0al-spec/SpecNode.git":
            assert ref == SPECNODE_RELEASE_REF
            write_fake_specnode_checkout(checkout)
            return {"status": "ok", "revision": SPECNODE_RELEASE_REVISION, "errors": []}
        raise AssertionError(f"Unexpected public index repository: {repository_url}")

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fake_checkout)

    report = load_public_index_manifest(
        PUBLIC_INDEX_ACCEPTED_MANIFEST,
        root=ROOT,
        remote_root=remote_root,
    )

    assert report["status"] == "ok"
    checkout = remote_root / public_index_module.public_index_checkout_dir_name(
        "https://github.com/0al-spec/SpecPM.git",
        SPECPM_RELEASE_REF,
        SPECPM_RELEASE_REVISION,
    )
    specnode_checkout = remote_root / public_index_module.public_index_checkout_dir_name(
        "https://github.com/0al-spec/SpecNode.git",
        SPECNODE_RELEASE_REF,
        SPECNODE_RELEASE_REVISION,
    )
    expected_alpha_package_dirs = [
        str((ROOT / "examples/email_tools").resolve()),
        str((ROOT / "packages/intent.package.public_repository_metadata").resolve()),
        str(checkout),
        str(ROOT.resolve()),
        str(specnode_checkout),
    ]
    expected_alpha_sources = [
        {
            "kind": "local",
            "path": "examples/email_tools",
            "package_dir": str((ROOT / "examples/email_tools").resolve()),
        },
        {
            "kind": "local",
            "path": "packages/intent.package.public_repository_metadata",
            "package_dir": str(
                (ROOT / "packages/intent.package.public_repository_metadata").resolve()
            ),
        },
        {
            "kind": "git",
            "repository": "https://github.com/0al-spec/SpecPM.git",
            "ref": SPECPM_RELEASE_REF,
            "revision": SPECPM_RELEASE_REVISION,
            "path": ".",
            "package_dir": str(checkout),
        },
        {
            "kind": "local",
            "path": ".",
            "package_dir": str(ROOT.resolve()),
        },
        {
            "kind": "git",
            "repository": "https://github.com/0al-spec/SpecNode.git",
            "ref": SPECNODE_RELEASE_REF,
            "revision": SPECNODE_RELEASE_REVISION,
            "path": ".",
            "package_dir": str(specnode_checkout),
        },
    ]
    assert len(expected_alpha_package_dirs) == len(expected_alpha_sources)
    alpha_len = len(expected_alpha_sources)
    assert report["package_dirs"][:alpha_len] == expected_alpha_package_dirs
    assert report["sources"][:alpha_len] == expected_alpha_sources
    generated_root = (ROOT / "public-index/generated").resolve()
    generated_sources = report["sources"][alpha_len:]
    generated_package_dirs = report["package_dirs"][alpha_len:]
    assert len(generated_package_dirs) == len(generated_sources)
    for source, package_dir in zip(generated_sources, generated_package_dirs, strict=True):
        assert source["kind"] == "local"
        source_path = (ROOT / source["path"]).resolve()
        source_path.relative_to(generated_root)
        assert source["package_dir"] == package_dir
        assert package_dir == str(source_path)
    assert report["errors"] == []

    output = tmp_path / "site"
    generation = generate_public_index(
        [Path(path) for path in report["package_dirs"]],
        output,
        "https://registry.example.invalid",
    )
    specpm_payload = json.loads(
        (output / "v0/packages/specpm.core/index.json").read_text(encoding="utf-8")
    )
    assert generation["status"] == "ok"
    assert specpm_payload["package"]["latest_version"] == "0.2.0"
    assert [item["version"] for item in specpm_payload["package"]["versions"]] == [
        "0.1.0",
        "0.2.0",
    ]
    assert (output / "v0/packages/specpm.core/versions/0.1.0/index.json").is_file()
    assert (output / "v0/packages/specpm.core/versions/0.2.0/index.json").is_file()


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
    receipt_payload = json.loads(
        (
            tmp_path
            / "site/v0/packages/document_conversion.email_tools/versions/0.1.0/"
            / "provenance-receipt/index.json"
        ).read_text(encoding="utf-8")
    )
    assert receipt_payload["source"] == {
        "kind": "git",
        "repository": "https://github.com/0al-spec/email-tools.git",
        "ref": "main",
        "revision": revision,
        "path": ".",
    }
    assert receipt_payload["review"]["commit"] == revision


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
            "--issued-at",
            "2026-05-31T00:00:00Z",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["written_count"] == 21
    receipt_payload = json.loads(
        (
            tmp_path
            / "site/v0/packages/document_conversion.email_tools/versions/0.1.0/"
            / "provenance-receipt/index.json"
        ).read_text(encoding="utf-8")
    )
    assert receipt_payload["issuedAt"] == "2026-05-31T00:00:00Z"


def test_cli_public_index_generate_accepts_reviewed_manifest(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    def fake_checkout(repository_url: str, ref: str, checkout: Path) -> dict[str, Any]:
        if repository_url == "https://github.com/0al-spec/SpecPM.git":
            assert ref == SPECPM_RELEASE_REF
            write_fake_specpm_release_checkout(checkout)
            return {"status": "ok", "revision": SPECPM_RELEASE_REVISION, "errors": []}
        if repository_url == "https://github.com/0al-spec/SpecNode.git":
            assert ref == SPECNODE_RELEASE_REF
            write_fake_specnode_checkout(checkout)
            return {"status": "ok", "revision": SPECNODE_RELEASE_REVISION, "errors": []}
        raise AssertionError(f"Unexpected public index repository: {repository_url}")

    monkeypatch.setattr(public_index_module, "checkout_public_index_repository", fake_checkout)

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
    assert (tmp_path / "site/v0/packages/specpm.core/index.json").is_file()
    assert (tmp_path / "site/v0/packages/specpm.core/versions/0.1.0/index.json").is_file()
    assert (tmp_path / "site/v0/packages/specpm.core/versions/0.2.0/index.json").is_file()
    assert (tmp_path / "site/v0/packages/specnode.core/index.json").is_file()


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


def test_cli_remote_search_intent_json(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(load_remote_registry_fixture("intent-search.json"))

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    exit_code = main(
        [
            "remote",
            "search-intent",
            "intent.document_conversion.email_to_markdown",
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["payload"]["kind"] == "RemoteIntentSearch"


def test_cli_remote_status_and_indexes_json(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    payloads = {
        "https://registry.example.invalid/v0/status": (
            load_remote_registry_fixture("registry-status.json")
        ),
        "https://registry.example.invalid/v0/packages": (
            load_remote_registry_fixture("package-index.json")
        ),
        "https://registry.example.invalid/v0/intents": (
            load_remote_registry_fixture("intent-index.json")
        ),
        (
            "https://registry.example.invalid/v0/intents/"
            "intent.document_conversion.email_to_markdown"
        ): load_remote_registry_fixture("intent-metadata.json"),
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
    intents_exit = main(
        [
            "remote",
            "intents",
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ]
    )
    intents_output = json.loads(capsys.readouterr().out)
    intent_exit = main(
        [
            "remote",
            "intent",
            "intent.document_conversion.email_to_markdown",
            "--registry",
            "https://registry.example.invalid",
            "--json",
        ]
    )
    intent_output = json.loads(capsys.readouterr().out)

    assert status_exit == 0
    assert status_output["payload"]["kind"] == "RemoteRegistryStatus"
    assert packages_exit == 0
    assert packages_output["payload"]["kind"] == "RemotePackageIndex"
    assert intents_exit == 0
    assert intents_output["payload"]["kind"] == "RemoteIntentIndex"
    assert intent_exit == 0
    assert intent_output["payload"]["kind"] == "RemoteIntent"


def test_cli_remote_observe_json(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    payloads = {
        "https://registry.example.invalid/v0/status": (
            load_remote_registry_fixture("registry-status.json")
        ),
        "https://registry.example.invalid/v0/packages": (
            load_remote_registry_fixture("package-index.json")
        ),
        "https://registry.example.invalid/v0/packages/document_conversion.email_tools": (
            load_remote_registry_fixture("package-metadata.json")
        ),
        (
            "https://registry.example.invalid/v0/packages/"
            "document_conversion.email_tools/versions/0.1.0"
        ): load_remote_registry_fixture("package-version.json"),
        (
            "https://registry.example.invalid/v0/capabilities/"
            "document_conversion.email_to_markdown/packages"
        ): load_remote_registry_fixture("capability-search.json"),
        (
            "https://registry.example.invalid/v0/intents/"
            "intent.document_conversion.email_to_markdown/packages"
        ): load_remote_registry_fixture("intent-search.json"),
    }

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return FakeRemoteResponse(payloads[request.full_url])

    monkeypatch.setattr(core_module, "urlopen", fake_urlopen)

    exit_code = main(
        [
            "remote",
            "observe",
            "--registry",
            "https://registry.example.invalid",
            "--package",
            "document_conversion.email_tools",
            "--version",
            "document_conversion.email_tools@0.1.0",
            "--capability",
            "document_conversion.email_to_markdown",
            "--intent",
            "intent.document_conversion.email_to_markdown",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["operation"] == "observe"
    assert payload["summary"]["check_count"] == 9
    assert payload["target"]["intent_ids"] == ["intent.document_conversion.email_to_markdown"]


def test_cli_remote_observe_text_normalizes_unknown_counts(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def fake_observe_remote_registry(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "status": "ok",
            "registry": "https://registry.example.invalid",
            "summary": {
                "package_count": None,
                "version_count": None,
            },
            "checks": [],
        }

    monkeypatch.setattr("specpm.cli.observe_remote_registry", fake_observe_remote_registry)

    exit_code = main(
        [
            "remote",
            "observe",
            "--registry",
            "https://registry.example.invalid",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "observed https://registry.example.invalid [unknown packages, unknown versions]" in (
        captured.out
    )
    assert "None packages" not in captured.out
    assert "None versions" not in captured.out


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
    intent_search = run_cli_json(
        [
            "search-intent",
            "intent.document_conversion.email_to_markdown",
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
    assert intent_search["result_count"] == 1
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


def test_validator_rejects_non_canonical_capability_intent_id(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "email-tools")
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["provides"]["capabilities"][0]["intentIds"] = ["identity.enterprise_sso"]
    write_yaml_file(spec_path, spec)

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {
        "intent_id_invalid",
        "manifest_intent_not_declared",
    }
    assert any("'intent.'" in issue["message"] for issue in report["errors"])


def test_manifest_intents_must_be_backed_by_capability_intent_ids(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "email-tools")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["index"]["provides"]["intents"] = [
        "intent.document_conversion.email_to_markdown",
        "intent.identity.enterprise_sso",
    ]
    write_yaml_file(manifest_path, manifest)

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "manifest_intent_not_declared" for issue in report["errors"])


def test_manifest_intents_must_include_declared_capability_intents(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "email-tools")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["index"]["provides"]["intents"] = []
    write_yaml_file(manifest_path, manifest)

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert any(issue["code"] == "manifest_intent_missing" for issue in report["errors"])


def test_manifest_rejects_malformed_intent_entries(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "email-tools")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["index"]["provides"]["intents"] = ["identity.enterprise_sso", 123]
    write_yaml_file(manifest_path, manifest)

    report = validate_package(package)

    assert report["status"] == "invalid"
    assert {issue["code"] for issue in report["errors"]} >= {
        "intent_id_invalid",
        "manifest_intent_entry_invalid",
    }


def test_manifest_intent_shape_error_does_not_emit_consistency_noise(
    tmp_path: Path,
) -> None:
    package = copy_email_package(tmp_path, "email-tools")
    manifest_path = package / "specpm.yaml"
    manifest = load_yaml_file(manifest_path)
    manifest["index"]["provides"]["intents"] = "intent.document_conversion.email_to_markdown"
    write_yaml_file(manifest_path, manifest)

    report = validate_package(package)
    codes = issue_codes(report["errors"])

    assert report["status"] == "invalid"
    assert "manifest_intents_invalid" in codes
    assert "manifest_intent_missing" not in codes
    assert "manifest_intent_not_declared" not in codes


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


def test_validator_warns_on_spec_authoring_quality_gaps(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "authoring-quality")
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    spec = load_yaml_file(spec_path)
    spec["interfaces"]["outbound"].append(
        {
            "id": "review_output",
            "kind": "unknown",
            "summary": "Review output with an intentionally weak kind.",
        }
    )
    spec["effects"]["sideEffects"].append(
        {
            "id": "review_effect",
            "kind": "unknown",
            "summary": "Effect with an intentionally weak kind.",
        }
    )
    spec["evidence"][0]["id"] = "no_network_access_required"
    spec["evidence"][0]["supports"] = [
        "metadata.license",
        "provides.capabilities.document_conversion.email_to_markdown",
    ]
    spec["evidence"].append(
        {
            "id": "review_unknown_kind",
            "kind": "unknown",
            "supports": ["provides.capabilities"],
        }
    )
    write_yaml_file(spec_path, spec)

    report = validate_package(package)

    assert report["status"] == "warning_only"
    warning_codes = issue_codes(report["warnings"])
    assert "duplicate_boundary_document_id" in warning_codes
    assert "evidence_support_target_unknown" in warning_codes
    assert "unspecified_evidence_kind" in warning_codes
    assert "unspecified_effect_kind" in warning_codes
    assert "unspecified_interface_kind" in warning_codes
    assert not any(
        issue["code"] == "evidence_support_target_unknown"
        and issue["message"].endswith("provides.capabilities.document_conversion.email_to_markdown")
        for issue in report["warnings"]
    )


def test_validator_accepts_public_interface_index_evidence_kind(tmp_path: Path) -> None:
    package = copy_email_package(tmp_path, "public-interface-index-evidence")
    spec_path = package / "specs/email-to-markdown.spec.yaml"
    public_interface_index = package / "public-interface-index.json"
    public_interface_index.write_text(
        '{"kind":"PublicInterfaceIndex","schemaVersion":1}\n',
        encoding="utf-8",
    )
    spec = load_yaml_file(spec_path)
    spec["evidence"][0] = {
        "id": "public_interface_index",
        "kind": "public_interface_index",
        "path": "public-interface-index.json",
        "supports": ["provides.capabilities.document_conversion.email_to_markdown"],
    }
    write_yaml_file(spec_path, spec)

    report = validate_package(package)

    assert report["status"] == "valid"
    warning_codes = issue_codes(report["warnings"])
    assert "unknown_evidence_kind" not in warning_codes


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
    assert index_payload["intents"]["intent.document_conversion.email_to_markdown"] == [
        {
            "package_id": "document_conversion.email_tools",
            "version": "0.1.0",
            "capability_ids": ["document_conversion.email_to_markdown"],
        }
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


def test_search_intent_finds_exact_intent_match(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    report = search_intent_index("intent.document_conversion.email_to_markdown", index_path)

    assert report["status"] == "ok"
    assert report["result_count"] == 1
    assert report["results"][0]["package_id"] == "document_conversion.email_tools"
    assert report["results"][0]["matched_intent"] == "intent.document_conversion.email_to_markdown"
    assert report["results"][0]["matched_capabilities"] == ["document_conversion.email_to_markdown"]


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


def test_search_intent_rebuilds_missing_intent_index_from_packages(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload.pop("intents")
    index_path.write_text(json.dumps(index_payload), encoding="utf-8")

    report = search_intent_index("intent.document_conversion.email_to_markdown", index_path)

    assert report["status"] == "ok"
    assert report["result_count"] == 1


def test_search_unknown_capability_returns_empty_result(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    report = search_index("document_conversion.unknown", index_path)

    assert report["status"] == "ok"
    assert report["result_count"] == 0
    assert report["results"] == []


def test_search_intent_rejects_non_canonical_intent_id(tmp_path: Path) -> None:
    report = search_intent_index("document_conversion.email_to_markdown", tmp_path / "index.json")

    assert report["status"] == "invalid"
    assert issue_codes(report["errors"]) == {"intent_id_invalid"}


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


def test_cli_search_intent_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    index_path = tmp_path / "index.json"
    index_package(ROOT / "examples/email_tools", index_path)

    exit_code = main(
        [
            "search-intent",
            "intent.document_conversion.email_to_markdown",
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
