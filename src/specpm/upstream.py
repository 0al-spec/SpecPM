"""Explicit software-origin metadata, independent of spec archive provenance."""

from typing import Any
from urllib.parse import urlsplit


def normalize_upstream(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    url = value.get("url")
    if (
        not isinstance(url, str)
        or not url
        or len(url) > 2048
        or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url)
        or "\\" in url
    ):
        return None
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            return None
        _ = parsed.port
    except ValueError:
        return None
    result = {"url": url}
    if "revision" in value:
        revision = value["revision"]
        if (
            not isinstance(revision, str)
            or not revision
            or len(revision) > 256
            or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in revision)
        ):
            return None
        result["revision"] = revision
    return result


def manifest_upstream(manifest: dict[str, Any]) -> dict[str, str] | None:
    artifacts = manifest.get("foreignArtifacts")
    if not isinstance(artifacts, list):
        return None
    candidates = [
        item
        for item in artifacts
        if isinstance(item, dict) and item.get("id") == "upstream_repository"
    ]
    # Ambiguous declarations are not resolved by list order or package identity.
    if len(candidates) != 1 or candidates[0].get("role") != "primary_intent_source":
        return None
    artifact = candidates[0]
    value = {"url": artifact.get("uri")}
    if "revision" in artifact:
        value["revision"] = artifact["revision"]
    return normalize_upstream(value)
