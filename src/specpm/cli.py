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
    yank_index_package,
)
from specpm.public_index import generate_public_index_from_inputs


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    if (
        args.command == "public-index"
        and args.public_index_command == "generate"
        and not args.package_dirs
        and not args.manifest
    ):
        parser.error("public-index generate requires at least one package directory or --manifest")

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

    search_intent = subparsers.add_parser(
        "search-intent", help="Search an index by exact canonical intent id."
    )
    search_intent.add_argument("intent_id")
    search_intent.add_argument("--index", default=".specpm/index.json")
    search_intent.add_argument(
        "--json", action="store_true", help="Emit a stable JSON intent search report."
    )
    search_intent.set_defaults(handler=handle_search_intent)

    add = subparsers.add_parser("add", help="Add a package to local project state.")
    add.add_argument(
        "target", help="Capability id, package_id@version, package directory, or archive."
    )
    add.add_argument("--index", default=".specpm/index.json")
    add.add_argument("--project", default=".")
    add.add_argument("--json", action="store_true", help="Emit a stable JSON add report.")
    add.set_defaults(handler=handle_add)

    yank = subparsers.add_parser("yank", help="Mark an indexed package as yanked.")
    yank.add_argument("package_ref", help="Package reference in package_id@version form.")
    yank.add_argument("--index", default=".specpm/index.json")
    yank.add_argument("--reason", required=True, help="Human-readable yanking reason.")
    yank.add_argument("--json", action="store_true", help="Emit a stable JSON yank report.")
    yank.set_defaults(handler=handle_yank)

    unyank = subparsers.add_parser("unyank", help="Remove the yanked flag from an indexed package.")
    unyank.add_argument("package_ref", help="Package reference in package_id@version form.")
    unyank.add_argument("--index", default=".specpm/index.json")
    unyank.add_argument("--json", action="store_true", help="Emit a stable JSON unyank report.")
    unyank.set_defaults(handler=handle_unyank)

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

    remote = subparsers.add_parser("remote", help="Read remote registry metadata.")
    remote_subparsers = remote.add_subparsers(dest="remote_command", required=True)

    remote_status = remote_subparsers.add_parser(
        "status", help="Fetch remote registry discovery status."
    )
    add_remote_registry_options(remote_status)
    remote_status.set_defaults(handler=handle_remote_status)

    remote_packages = remote_subparsers.add_parser(
        "packages", help="Fetch the remote package index."
    )
    add_remote_registry_options(remote_packages)
    remote_packages.set_defaults(handler=handle_remote_packages)

    remote_package = remote_subparsers.add_parser("package", help="Fetch remote package metadata.")
    remote_package.add_argument("package_id")
    add_remote_registry_options(remote_package)
    remote_package.set_defaults(handler=handle_remote_package)

    remote_version = remote_subparsers.add_parser(
        "version", help="Fetch one remote package version."
    )
    remote_version.add_argument("package_ref", help="Package reference in package_id@version form.")
    add_remote_registry_options(remote_version)
    remote_version.set_defaults(handler=handle_remote_version)

    remote_search = remote_subparsers.add_parser(
        "search", help="Search a remote registry by exact capability id."
    )
    remote_search.add_argument("capability_id")
    add_remote_registry_options(remote_search)
    remote_search.set_defaults(handler=handle_remote_search)

    remote_search_intent = remote_subparsers.add_parser(
        "search-intent", help="Search a remote registry by exact canonical intent id."
    )
    remote_search_intent.add_argument("intent_id")
    add_remote_registry_options(remote_search_intent)
    remote_search_intent.set_defaults(handler=handle_remote_search_intent)

    remote_observe = remote_subparsers.add_parser(
        "observe", help="Build a read-only remote registry observation report."
    )
    remote_observe.add_argument(
        "--package",
        dest="packages",
        action="append",
        default=[],
        help="Expected package id to verify. May be passed more than once.",
    )
    remote_observe.add_argument(
        "--version",
        dest="versions",
        action="append",
        default=[],
        help="Expected package_id@version to verify. May be passed more than once.",
    )
    remote_observe.add_argument(
        "--capability",
        dest="capabilities",
        action="append",
        default=[],
        help="Expected capability id to verify. May be passed more than once.",
    )
    add_remote_registry_options(remote_observe)
    remote_observe.set_defaults(handler=handle_remote_observe)

    public_index = subparsers.add_parser(
        "public-index", help="Generate public static registry metadata."
    )
    public_index_subparsers = public_index.add_subparsers(
        dest="public_index_command", required=True
    )

    public_index_generate = public_index_subparsers.add_parser(
        "generate", help="Generate static /v0 registry metadata from package directories."
    )
    public_index_generate.add_argument("package_dirs", nargs="*")
    public_index_generate.add_argument(
        "--manifest",
        help="Read accepted package sources from a public index manifest.",
    )
    public_index_generate.add_argument("--output", required=True)
    public_index_generate.add_argument("--registry", required=True)
    public_index_generate.add_argument("--json", action="store_true", help="Emit stable JSON.")
    public_index_generate.set_defaults(handler=handle_public_index_generate)

    return parser


def add_remote_registry_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--registry", required=True, help="Remote registry base URL.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Remote registry request timeout in seconds.",
    )
    parser.add_argument("--json", action="store_true", help="Emit stable JSON.")


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


def handle_search_intent(args: argparse.Namespace) -> int:
    report = search_intent_index(args.intent_id, Path(args.index))
    if args.json:
        print_json(report)
    else:
        if report["status"] == "ok":
            if not report["results"]:
                print(f"No packages found for intent: {args.intent_id}")
            for result in report["results"]:
                matched = ", ".join(result.get("matched_capabilities", []))
                print(f"{result['package_id']} {result['version']} [{matched}]")
        else:
            print(f"intent search failed: {args.intent_id}", file=sys.stderr)
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


def handle_yank(args: argparse.Namespace) -> int:
    report = yank_index_package(args.package_ref, Path(args.index), args.reason)
    if args.json:
        print_json(report)
    else:
        print_index_lifecycle(report)
    return 0 if report["status"] in {"yanked", "unchanged"} else 1


def handle_unyank(args: argparse.Namespace) -> int:
    report = unyank_index_package(args.package_ref, Path(args.index))
    if args.json:
        print_json(report)
    else:
        print_index_lifecycle(report)
    return 0 if report["status"] in {"unyanked", "unchanged"} else 1


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


def handle_remote_package(args: argparse.Namespace) -> int:
    report = get_remote_package(args.registry, args.package_id, args.timeout)
    return emit_remote_registry_report(report, args.json)


def handle_remote_status(args: argparse.Namespace) -> int:
    report = get_remote_registry_status(args.registry, args.timeout)
    return emit_remote_registry_report(report, args.json)


def handle_remote_packages(args: argparse.Namespace) -> int:
    report = get_remote_package_index(args.registry, args.timeout)
    return emit_remote_registry_report(report, args.json)


def handle_remote_version(args: argparse.Namespace) -> int:
    report = get_remote_package_version(args.registry, args.package_ref, args.timeout)
    return emit_remote_registry_report(report, args.json)


def handle_remote_search(args: argparse.Namespace) -> int:
    report = search_remote_registry(args.registry, args.capability_id, args.timeout)
    return emit_remote_registry_report(report, args.json)


def handle_remote_search_intent(args: argparse.Namespace) -> int:
    report = search_remote_registry_intent(args.registry, args.intent_id, args.timeout)
    return emit_remote_registry_report(report, args.json)


def handle_remote_observe(args: argparse.Namespace) -> int:
    report = observe_remote_registry(
        args.registry,
        package_ids=args.packages,
        package_refs=args.versions,
        capability_ids=args.capabilities,
        timeout=args.timeout,
    )
    if args.json:
        print_json(report)
    else:
        print_remote_observation(report)
    return 0 if report["status"] == "ok" else 1


def handle_public_index_generate(args: argparse.Namespace) -> int:
    report = generate_public_index_from_inputs(
        [Path(package_dir) for package_dir in args.package_dirs],
        Path(args.output),
        args.registry,
        manifest_path=Path(args.manifest) if args.manifest else None,
    )
    if args.json:
        print_json(report)
    else:
        if report["status"] == "ok":
            print(f"generated public index: {report['output']} [{report['written_count']} files]")
        else:
            print("public index generation failed", file=sys.stderr)
            for issue in report.get("errors", []):
                print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)
    return 0 if report["status"] == "ok" else 1


def emit_remote_registry_report(report: dict[str, Any], json_output: bool) -> int:
    if json_output:
        print_json(report)
    else:
        print_remote_registry(report)
    return 0 if report["status"] == "ok" else 1


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def print_remote_registry(report: dict[str, Any]) -> None:
    if report["status"] != "ok":
        print(f"remote {report['operation']} failed: {report['target']}", file=sys.stderr)
        for issue in report.get("errors", []):
            print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)
        return

    payload = report.get("payload") or {}
    kind = payload.get("kind")
    if kind == "RemoteRegistryStatus":
        registry = payload["registry"]
        print(
            f"{registry['profile']} "
            f"[{registry['package_count']} packages, {registry['version_count']} versions]"
        )
        return
    if kind == "RemotePackageIndex":
        print(f"{payload['package_count']} remote packages [{payload['version_count']} versions]")
        for package in payload["packages"]:
            print(f"{package['package_id']} {package.get('latest_version', 'unknown')}")
        return
    if kind == "RemotePackage":
        package = payload["package"]
        print(f"{package['package_id']} [{len(package['versions'])} versions]")
        return
    if kind == "RemotePackageVersion":
        package = payload["package"]
        state = package["state"]
        flags = []
        if state["yanked"]:
            flags.append("yanked")
        if state["deprecated"]:
            flags.append("deprecated")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        print(f"{package['package_id']} {package['version']}{suffix}")
        return
    if kind == "RemoteCapabilitySearch":
        if not payload["results"]:
            print(f"No remote packages found for capability: {payload['query']['capability_id']}")
            return
        for result in payload["results"]:
            suffix = " [yanked]" if result["yanked"] else ""
            print(
                f"{result['package_id']} {result['version']} "
                f"[{result['matched_capability']}]{suffix}"
            )
        return
    if kind == "RemoteIntentSearch":
        if not payload["results"]:
            print(f"No remote packages found for intent: {payload['query']['intent_id']}")
            return
        for result in payload["results"]:
            suffix = " [yanked]" if result["yanked"] else ""
            matched = ", ".join(result.get("matched_capabilities", []))
            print(f"{result['package_id']} {result['version']} [{matched}]{suffix}")
        return
    print(f"remote {report['operation']}: {kind}")


def print_remote_observation(report: dict[str, Any]) -> None:
    summary = report.get("summary", {})
    if report["status"] == "ok":
        package_count = summary.get("package_count")
        version_count = summary.get("version_count")
        package_count_display = "unknown" if package_count is None else package_count
        version_count_display = "unknown" if version_count is None else version_count
        print(
            f"observed {report['registry']} "
            f"[{package_count_display} packages, "
            f"{version_count_display} versions]"
        )
        for check in report.get("checks", []):
            print(f"ok {check['id']}")
        return

    print(f"remote observation failed: {report['registry']}", file=sys.stderr)
    for check in report.get("checks", []):
        if check.get("status") != "ok":
            print(f"failed {check['id']}", file=sys.stderr)
    for issue in report.get("errors", []):
        print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)


def print_index_lifecycle(report: dict[str, Any]) -> None:
    if report["status"] in {"yanked", "unyanked", "unchanged"}:
        package = report["package"]
        print(
            f"{report['status']}: {package['package_id']} {package['version']} -> {report['index']}"
        )
        return
    print(f"{report['action']} failed: {report['target']}", file=sys.stderr)
    for issue in report.get("errors", []):
        print(f"error {issue['code']}: {issue['message']}", file=sys.stderr)


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
    if package.get("required_capabilities"):
        print("Required capabilities:")
        for capability in package["required_capabilities"]:
            print(f"  - {capability}")
    compatibility = package.get("compatibility")
    if isinstance(compatibility, dict) and compatibility:
        print("Compatibility:")
        for key, value in sorted(compatibility.items()):
            print(f"  - {key}: {value}")
    if report.get("boundary_specs"):
        print("Boundary specs:")
        for spec in report["boundary_specs"]:
            print(f"  - {spec['id']} ({spec['path']})")
            if spec.get("intent_summary"):
                print(f"    Intent: {spec['intent_summary']}")
            if spec.get("bounded_context"):
                print(f"    Bounded context: {spec['bounded_context']}")
            if spec.get("provides"):
                print(f"    Provides: {', '.join(spec['provides'])}")
            if spec.get("requires"):
                print(f"    Requires: {', '.join(spec['requires'])}")
            interface_counts = summarize_interface_counts(spec.get("interfaces"))
            if interface_counts:
                print(f"    Interfaces: {interface_counts}")
            effect_kinds = summarize_effect_kinds(spec.get("effects"))
            if effect_kinds:
                print(f"    Effects: {effect_kinds}")
            confidence = summarize_mapping(spec.get("provenance_confidence"))
            if confidence:
                print(f"    Provenance confidence: {confidence}")
    if report.get("contract_warnings"):
        print("Contract warnings:")
        for issue in report["contract_warnings"]:
            print(f"warning {issue['code']}: {issue['message']}")
    print_validation(report["validation"])


def summarize_interface_counts(interfaces: Any) -> str:
    if not isinstance(interfaces, dict):
        return ""
    counts = []
    for direction in ("inbound", "outbound"):
        items = interfaces.get(direction, [])
        if isinstance(items, list):
            counts.append(f"{direction}={len(items)}")
    return ", ".join(counts)


def summarize_effect_kinds(effects: Any) -> str:
    if not isinstance(effects, dict):
        return ""
    side_effects = effects.get("sideEffects", [])
    if not isinstance(side_effects, list):
        return ""
    kinds = sorted(
        {
            item["kind"]
            for item in side_effects
            if isinstance(item, dict) and isinstance(item.get("kind"), str)
        }
    )
    return ", ".join(kinds)


def summarize_mapping(mapping: Any) -> str:
    if not isinstance(mapping, dict):
        return ""
    parts = [f"{key}={value}" for key, value in sorted(mapping.items())]
    return ", ".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
