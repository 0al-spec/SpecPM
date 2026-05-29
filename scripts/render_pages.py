from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LANDING_ROOT = ROOT / "landing_page"
TEMPLATE_TOKENS = {
    "__SPECPM_VERSION__": "version",
    "__SPECPM_BUILD_NUMBER__": "build_number",
    "__SPECPM_BUILD_REVISION__": "revision",
    "__SPECPM_BUILD_REVISION_SHORT__": "revision_short",
}
DEFAULT_DOCS_URL = "https://0al-spec.github.io/SpecPM/documentation/specpm/"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render static SpecPM landing and registry viewer pages."
    )
    parser.add_argument("--output", required=True, help="Generated Pages artifact directory.")
    parser.add_argument("--specpm-version", required=True)
    parser.add_argument("--build-number", default="local")
    parser.add_argument("--build-revision", default="unknown")
    parser.add_argument("--custom-domain", default="")
    parser.add_argument(
        "--root-mode",
        choices=("landing", "docs-redirect"),
        default="landing",
        help="Render the root page as the landing page or as a DocC redirect.",
    )
    parser.add_argument(
        "--docs-url",
        default=DEFAULT_DOCS_URL,
        help="Absolute DocC URL used when --root-mode=docs-redirect.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    metadata = build_metadata(args.specpm_version, args.build_number, args.build_revision)

    output.mkdir(parents=True, exist_ok=True)
    if args.root_mode == "docs-redirect":
        write_docs_redirect(output / "index.html", args.docs_url)
    else:
        render_template(LANDING_ROOT / "index.html", output / "index.html", metadata)
    render_template(LANDING_ROOT / "viewer.html", output / "viewer/index.html", metadata)

    copy_assets(LANDING_ROOT / "assets", output / "assets")
    copy_assets(LANDING_ROOT / "assets", output / "viewer/assets")
    (output / ".nojekyll").touch()
    write_json(output / "site-metadata.json", site_metadata(metadata))

    custom_domain = args.custom_domain.strip()
    if custom_domain:
        (output / "CNAME").write_text(f"{custom_domain}\n", encoding="utf-8")

    return 0


def build_metadata(version: str, build_number: str, revision: str) -> dict[str, str]:
    clean_revision = revision.strip() or "unknown"
    return {
        "version": version.strip() or "0.0.0",
        "build_number": build_number.strip() or "local",
        "revision": clean_revision,
        "revision_short": clean_revision[:12],
    }


def render_template(source: Path, destination: Path, metadata: dict[str, str]) -> None:
    text = source.read_text(encoding="utf-8")
    for token, key in TEMPLATE_TOKENS.items():
        text = text.replace(token, metadata[key])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def copy_assets(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def write_docs_redirect(destination: Path, docs_url: str) -> None:
    clean_url = docs_url.strip() or DEFAULT_DOCS_URL
    escaped_url = html.escape(clean_url, quote=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8" />',
                '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
                f'  <meta http-equiv="refresh" content="0; url={escaped_url}" />',
                f'  <link rel="canonical" href="{escaped_url}" />',
                "  <title>SpecPM Documentation</title>",
                "</head>",
                "<body>",
                f'  <p><a href="{escaped_url}">Open SpecPM documentation</a>.</p>',
                "</body>",
                "</html>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def site_metadata(metadata: dict[str, str]) -> dict[str, Any]:
    return {
        "apiVersion": "specpm.site-build/v0",
        "schemaVersion": 1,
        "implementation": {
            "name": "SpecPM",
            "version": metadata["version"],
            "build": {
                "number": metadata["build_number"],
                "revision": metadata["revision"],
                "revision_short": metadata["revision_short"],
            },
        },
    }


def write_json(destination: Path, payload: dict[str, Any]) -> None:
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
