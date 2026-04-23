from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from specpm import __version__
from specpm.core import (
    inspect_inbox_bundle,
    inspect_package,
    list_inbox,
    pack_package,
    validate_package,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return args.handler(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specpm", description="Local SpecPackage manager.")
    parser.add_argument("--version", action="version", version=f"specpm {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate", help="Validate a SpecPackage directory.")
    validate.add_argument("package_dir")
    validate.add_argument(
        "--json", action="store_true", help="Emit a stable JSON validation report."
    )
    validate.set_defaults(handler=handle_validate)

    inspect_cmd = subparsers.add_parser("inspect", help="Inspect a SpecPackage directory.")
    inspect_cmd.add_argument("package_dir")
    inspect_cmd.add_argument(
        "--json", action="store_true", help="Emit a stable JSON inspection report."
    )
    inspect_cmd.set_defaults(handler=handle_inspect)

    pack = subparsers.add_parser("pack", help="Create a deterministic SpecPackage archive.")
    pack.add_argument("package_dir")
    pack.add_argument("-o", "--output")
    pack.add_argument("--json", action="store_true", help="Emit a stable JSON pack report.")
    pack.set_defaults(handler=handle_pack)

    inbox = subparsers.add_parser("inbox", help="Inspect SpecGraph export inbox bundles.")
    inbox_subparsers = inbox.add_subparsers(dest="inbox_command", required=True)

    inbox_list = inbox_subparsers.add_parser("list", help="List SpecGraph export bundles.")
    inbox_list.add_argument("--root", default=".specgraph_exports")
    inbox_list.add_argument("--json", action="store_true", help="Emit stable JSON.")
    inbox_list.set_defaults(handler=handle_inbox_list)

    inbox_inspect = inbox_subparsers.add_parser(
        "inspect", help="Inspect one SpecGraph export bundle."
    )
    inbox_inspect.add_argument("package_id")
    inbox_inspect.add_argument("--root", default=".specgraph_exports")
    inbox_inspect.add_argument("--json", action="store_true", help="Emit stable JSON.")
    inbox_inspect.set_defaults(handler=handle_inbox_inspect)

    return parser


def handle_validate(args: argparse.Namespace) -> int:
    report = validate_package(Path(args.package_dir))
    if args.json:
        print_json(report)
    else:
        print_validation(report)
    return 1 if report["status"] == "invalid" else 0


def handle_inspect(args: argparse.Namespace) -> int:
    report = inspect_package(Path(args.package_dir))
    if args.json:
        print_json(report)
    else:
        print_inspection(report)
    return 1 if report["validation"]["status"] == "invalid" else 0


def handle_pack(args: argparse.Namespace) -> int:
    output = Path(args.output) if args.output else None
    report = pack_package(Path(args.package_dir), output)
    if args.json:
        print_json(report)
    else:
        if report["status"] == "packed":
            digest = report["digest"]["value"]
            print(f"packed: {report['archive']}")
            print(f"sha256: {digest}")
            print(f"files: {len(report['included_files'])}")
        else:
            print(f"pack failed: {args.package_dir}", file=sys.stderr)
            for issue in report.get("errors", []):
                print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)
            if "validation" in report:
                print_validation(report["validation"], stream=sys.stderr)
    return 0 if report["status"] == "packed" else 1


def handle_inbox_list(args: argparse.Namespace) -> int:
    report = list_inbox(Path(args.root))
    if args.json:
        print_json(report)
    else:
        if not report["bundles"]:
            print(f"No SpecGraph export bundles found under {report['root']}.")
        for bundle in report["bundles"]:
            identity = bundle.get("package_identity") or {}
            package_id = identity.get("package_id") or bundle["package_id"]
            version = identity.get("version") or "unknown"
            print(f"{package_id} {version} [{bundle['inbox_status']}]")
    return 0


def handle_inbox_inspect(args: argparse.Namespace) -> int:
    report = inspect_inbox_bundle(Path(args.root), args.package_id)
    if args.json:
        print_json(report)
    else:
        if report["found"]:
            print(f"{report['package_id']} [{report['inbox_status']}]")
            print_inspection(report["inspection"])
        else:
            print(f"Bundle not found: {report['package_id']}", file=sys.stderr)
    return 0 if report["found"] else 1


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def print_validation(report: dict[str, Any], stream: TextIO | None = None) -> None:
    stream = stream or sys.stdout
    identity = report.get("package_identity") or {}
    package_id = identity.get("package_id", "unknown")
    print(
        f"{report['status']}: {package_id} "
        f"({report['error_count']} errors, {report['warning_count']} warnings)",
        file=stream,
    )
    for issue in report["errors"]:
        print(f"error {issue['code']}: {issue['message']}", file=stream)
    for issue in report["warnings"]:
        print(f"warning {issue['code']}: {issue['message']}", file=stream)


def print_inspection(report: dict[str, Any]) -> None:
    package = report.get("package") or {}
    identity = package.get("identity") or {}
    print(
        f"Package: {identity.get('package_id', 'unknown')} {identity.get('version', '')}".rstrip()
    )
    if package.get("summary"):
        print(f"Summary: {package['summary']}")
    if package.get("license"):
        print(f"License: {package['license']}")
    if package.get("capabilities"):
        print("Capabilities:")
        for capability in package["capabilities"]:
            print(f"  - {capability}")
    if report.get("boundary_specs"):
        print("Boundary specs:")
        for spec in report["boundary_specs"]:
            print(f"  - {spec['id']} ({spec['path']})")
    print_validation(report["validation"])


if __name__ == "__main__":
    raise SystemExit(main())
