"""Catalog acceptance contracts for the five skill-authored seed packages."""

import hashlib
import json
import re
import tarfile
from pathlib import Path

import pytest
import yaml

from specpm.core import pack_package, validate_package
from specpm.public_index import generate_public_index

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [
    ("rtk.shell_output_proxy", "0.1.0"),
    ("openai.codex", "0.1.0"),
    ("axios.http_client", "1.19.0"),
    ("bitcoin.core.fullnode", "0.1.0"),
    ("n8n.platform", "0.1.0"),
]


@pytest.mark.parametrize(("package_id", "version"), SEEDS)
def test_seed_package_acceptance_and_portable_evidence(package_id, version, tmp_path):
    relative = f"public-index/curated/{package_id}/{version}"
    root = ROOT / relative
    accepted = yaml.safe_load((ROOT / "public-index/accepted-packages.yml").read_text())
    assert relative in {entry["path"] for entry in accepted["packages"]}
    manifest = yaml.safe_load((root / "specpm.yaml").read_text())
    spec = yaml.safe_load((root / "specs/main.spec.yaml").read_text())
    assert manifest.get("preview_only") is None
    assert "AI-assisted" in manifest["metadata"]["authors"][0]["name"]
    assert spec["metadata"]["status"] == "draft"  # Not runtime certification.
    assert not manifest["index"]["provides"].get("intents")
    assert set(manifest["index"]["provides"]["capabilities"]) == {
        entry["id"] for entry in spec["provides"]["capabilities"]
    }
    validation = validate_package(root)
    assert validation["status"] == "valid", validation
    assert not validation["errors"], validation
    assert not validation["warnings"], validation
    receipt = json.loads((root / "evidence/curation.json").read_text())
    assert re.fullmatch(r"[a-f0-9]{40}", receipt["revision"])
    assert receipt["review"]["runtimeExecuted"] is False
    assert receipt["review"]["upstreamEndorsement"] is False
    assert receipt["producer"]["originalFiles"]["specpm.yaml"]
    upstream = manifest["foreignArtifacts"][0]
    assert (upstream["uri"], upstream["revision"]) == (receipt["repository"], receipt["revision"])
    packed = pack_package(root, tmp_path / "seed.specpm.tgz")
    assert packed["status"] == "packed", packed
    all_files = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    assert set(packed["included_files"]) == all_files
    with tarfile.open(packed["archive"]) as archive:
        for binding in receipt["evidence"]:
            data = archive.extractfile(binding["path"]).read()
            assert hashlib.sha256(data).hexdigest() == binding["artifactSha256"]
            assert re.fullmatch(r"[a-f0-9]{64}", binding["sourceSha256"])
            assert f"/blob/{receipt['revision']}/" in binding["sourceUrl"]
            assert 1 <= binding["sourceLines"][0] <= binding["sourceLines"][1]
            if package_id == "n8n.platform":
                assert binding["mode"] == "reference_only"
                assert b"Upstream bytes are not redistributed" in data
            else:
                assert binding["mode"] == "verbatim"


def test_seed_packages_generate_registry_metadata(tmp_path):
    roots = [ROOT / "public-index/curated" / name / version for name, version in SEEDS]
    report = generate_public_index(roots, tmp_path, "https://registry.example.invalid")
    assert report["status"] == "ok", report
    for name, version in SEEDS:
        version_file = tmp_path / "v0/packages" / name / "versions" / version / "index.json"
        assert version_file.is_file()
        payload = json.loads(version_file.read_text())
        assert payload["package"]["package_id"] == name
        assert payload["package"]["version"] == version


def test_seed_review_corrections():
    base = ROOT / "public-index/curated"
    bitcoin_path = base / "bitcoin.core.fullnode/0.1.0/specs/main.spec.yaml"
    bitcoin = yaml.safe_load(bitcoin_path.read_text())
    assert "p2p_network" not in {i["id"] for i in bitcoin["interfaces"]["outbound"]}
    codex = json.loads((base / "openai.codex/0.1.0/evidence/curation.json").read_text())
    assert "docs/install.md" in {e["sourcePath"] for e in codex["evidence"]}
    for name in ("rtk.shell_output_proxy", "openai.codex", "bitcoin.core.fullnode"):
        receipt = json.loads((base / name / "0.1.0/evidence/curation.json").read_text())
        assert any(e["sourcePath"] in {"LICENSE", "COPYING"} for e in receipt["evidence"])


@pytest.mark.parametrize(
    ("package_id", "version", "effect_id"),
    [
        ("openai.codex", "0.1.0", "network_call"),
        ("axios.http_client", "1.19.0", "external_http"),
        ("n8n.platform", "0.1.0", "network_calls"),
    ],
)
def test_remote_requests_declare_outbound_data_flow(package_id, version, effect_id):
    root = ROOT / "public-index/curated" / package_id / version
    spec = yaml.safe_load((root / "specs/main.spec.yaml").read_text())
    effect = next(item for item in spec["effects"]["sideEffects"] if item["id"] == effect_id)
    # Receiving a response does not make sending request data a read-only effect.
    assert effect["kind"] == "network_write"
    if package_id == "openai.codex":
        for disclosure in ("prompts", "images", "repository context", "configured service"):
            assert disclosure in effect["summary"]
        evidence = next(
            item for item in spec["evidence"] if item["id"] == "typescript_sdk_documentation_1_1"
        )
        assert "effects.sideEffects.network_call" in evidence["supports"]
