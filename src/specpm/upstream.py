"""Explicit software-origin metadata, independent of spec archive provenance."""

import ipaddress
import re
import unicodedata
from typing import Any
from urllib.parse import urlsplit


def valid_host(host: str) -> bool:
    try:
        if ":" in host:
            return "%" not in host and bool(ipaddress.IPv6Address(host))
        host = host.encode("idna").decode("ascii").rstrip(".")
        if not host or len(host) > 253:
            return False
        if not all(
            re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
            for label in host.split(".")
        ):
            return False
        # Browsers interpret numeric final labels as IPv4, not DNS names.
        if re.fullmatch(r"(?:[0-9]+|0[xX][0-9a-fA-F]+)", host.split(".")[-1]):
            return bool(ipaddress.IPv4Address(host))
        return True
    except (ValueError, UnicodeError):
        return False


def normalize_upstream(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    url = value.get("url")
    if (
        not isinstance(url, str)
        or not url
        or len(url) > 2048
        or any(char.isspace() or unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in url)
        or "\\" in url
    ):
        return None
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or not valid_host(parsed.hostname)
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
            or any(
                char.isspace() or unicodedata.category(char) in {"Cc", "Cf", "Cs"}
                for char in revision
            )
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
