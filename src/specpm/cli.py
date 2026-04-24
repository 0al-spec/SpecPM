from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from specpm import __version__
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

    index = subparsers.add_parser("index", help="Add a package directory or archive to an index.")
    index.add_argument("package_ref")
    index.add_argument("--index", default=".specpm/index.json")
    index.add_argument("--json", action="store_true", help="Emit a stable JSON index report.")
    index.set_defaults(handler=handle_index)

    search = subparsers.add_parser("search", help="Search an index by exact capability id.")
    search.add_argument("capability_id")
    search.add_argument("--index", default=".specpm/index.json")
    search.add_argument("--json", action="store_true", help="Emit a stable JSON search report.")
    search.set_defaults(handler=handle_search)

    add = subparsers.add_parser("add", help="Add a package to local project state.")
    add.add_argument(
        "target", help="Capability id, package_id@version, package directory, or archive."
    )
    add.add_argument("--index", default=".specpm/index.json")
    add.add_argument("--project", default=".")
    add.add_argument("--json", action="store_true", help="Emit a stable JSON add report.")
    add.set_defaults(handler=handle_add)

    diff = subparsers.add_parser("diff", help="Diff two SpecPackage directories.")
    diff.add_argument("old_package")
    diff.add_argument("new_package")
    diff.add_argument("--json", action="store_true", help="Emit a stable JSON diff report.")
    diff.set_defaults(handler=handle_diff)

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


def handle_index(args: argparse.Namespace) -> int:
    report = index_package(Path(args.package_ref), Path(args.index))
    if args.json:
        print_json(report)
    else:
        if report["status"] in {"indexed", "unchanged"}:
            entry = report["entry"]
            print(
                f"{report['status']}: {entry['package_id']} {entry['version']} -> {report['index']}"
            )
        else:
            print(f"index failed: {args.package_ref}", file=sys.stderr)
            for issue in report.get("errors", []):
                print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)
            if "validation" in report:
                print_validation(report["validation"], stream=sys.stderr)
    return 0 if report["status"] in {"indexed", "unchanged"} else 1


def handle_search(args: argparse.Namespace) -> int:
    report = search_index(args.capability_id, Path(args.index))
    if args.json:
        print_json(report)
    else:
        if report["status"] == "ok":
            if not report["results"]:
                print(f"No packages found for capability: {args.capability_id}")
            for result in report["results"]:
                print(
                    f"{result['package_id']} {result['version']} [{result['matched_capability']}]"
                )
        else:
            print(f"search failed: {args.capability_id}", file=sys.stderr)
            for issue in report.get("errors", []):
                print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)
    return 0 if report["status"] == "ok" else 1


def handle_add(args: argparse.Namespace) -> int:
    report = add_package(args.target, Path(args.index), Path(args.project))
    if args.json:
        print_json(report)
    else:
        if report["status"] in {"added", "unchanged"}:
            package = report["package"]
            print(
                f"{report['status']}: {package['package_id']} {package['version']} "
                f"-> {report['lockfile']}"
            )
        elif report["status"] == "ambiguous":
            print(f"add requires review: {args.target}", file=sys.stderr)
            for candidate in report.get("candidates", []):
                print(
                    f"candidate {candidate['package_id']} {candidate['version']}",
                    file=sys.stderr,
                )
        else:
            print(f"add failed: {args.target}", file=sys.stderr)
            for issue in report.get("errors", []):
                print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)
    return 0 if report["status"] in {"added", "unchanged"} else 1


def handle_diff(args: argparse.Namespace) -> int:
    report = diff_packages(Path(args.old_package), Path(args.new_package))
    if args.json:
        print_json(report)
    else:
        if report["status"] == "ok":
            print(f"{report['classification']}: {args.old_package} -> {args.new_package}")
            changes = report["changes"]
            print(
                "capabilities: "
                f"-{len(changes['capabilities']['removed'])} "
                f"+{len(changes['capabilities']['added'])}"
            )
            print(
                "interfaces: "
                f"-{len(changes['interfaces']['removed'])} "
                f"+{len(changes['interfaces']['added'])} "
                f"~{len(changes['interfaces']['changed'])}"
            )
            print(
                "must constraints: "
                f"-{len(changes['must_constraints']['removed'])} "
                f"+{len(changes['must_constraints']['added'])} "
                f"~{len(changes['must_constraints']['changed'])}"
            )
        else:
            print(f"diff failed: {args.old_package} -> {args.new_package}", file=sys.stderr)
            for issue in report.get("errors", []):
                print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)
    return 0 if report["status"] == "ok" else 1


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
