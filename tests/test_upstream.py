import pytest

from specpm.core import validate_remote_upstream
from specpm.public_index import remote_package_payload, remote_package_version_payload
from specpm.upstream import manifest_upstream, normalize_upstream


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        {"url": ""},
        {"url": "javascript:alert(1)"},
        {"url": "https://user:secret@example.org/repo"},
        {"url": "https://example.org/repo?token=x"},
        {"url": "https://example.org/repo#fragment"},
        {"url": "https://example.org:bad/repo"},
        {"url": "https://example.org/\nrepo"},
        {"url": "https://example.org/\\repo"},
        {"url": "https://example.org/repo", "revision": None},
        {"url": "https://example.org/repo", "revision": " "},
    ],
)
def test_invalid_upstream(value):
    assert normalize_upstream(value) is None
    errors = []
    validate_remote_upstream({"upstream": value}, errors, "package")
    assert errors[0].field == "package.upstream"


def test_explicit_manifest_selection():
    declaration = {
        "id": "upstream_repository",
        "role": "primary_intent_source",
        "uri": "https://example.org/repo",
        "revision": "v1",
    }
    doc = {"id": "documentation", "role": "documentation", "uri": "https://example.org/docs"}
    assert manifest_upstream({"foreignArtifacts": [doc, declaration]}) == {
        "url": declaration["uri"],
        "revision": "v1",
    }
    for artifacts in (
        [],
        [doc],
        [declaration, declaration],
        [{**declaration, "role": "documentation"}],
        [{**declaration, "uri": "file:///tmp/repo"}],
    ):
        assert manifest_upstream({"foreignArtifacts": artifacts}) is None
    assert manifest_upstream({}) is None
    errors = []
    validate_remote_upstream({}, errors, "package")
    assert not errors
    assert normalize_upstream({"url": declaration["uri"]}) == {"url": declaration["uri"]}


def test_upstream_version_binding():
    old = {
        "package_id": "test.repo",
        "name": "Test",
        "version": "1.0.0",
        "summary": "test",
        "license": "MIT",
        "provided_capabilities": [],
        "required_capabilities": [],
        "compatibility": {},
        "state": {"yanked": False, "deprecated": False},
        "source": {"url": "https://registry.example/archive.tgz"},
        "upstream": {"url": "https://example.org/old", "revision": "old"},
    }
    latest = {
        **old,
        "version": "2.0.0",
        "upstream": {"url": "https://example.org/new", "revision": "new"},
    }
    assert remote_package_payload([old, latest], [])["package"]["upstream"] == latest["upstream"]
    assert remote_package_version_payload(old, [])["package"]["upstream"] == old["upstream"]
    latest.pop("upstream")
    assert "upstream" not in remote_package_payload([old, latest], [])["package"]
