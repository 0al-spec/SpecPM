from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import yaml

from specpm.core import validate_package

SUBMISSION_SCHEMA_VERSION = 1
ACCEPTED_MANIFEST_CANDIDATE_SCHEMA_VERSION = 1
ACCEPTED_MANIFEST_PR_SCHEMA_VERSION = 1
MAX_SUBMITTED_REPOSITORIES = 10
ISSUE_FORM_EMPTY_VALUES = {"", "_No response_"}
ACCEPTED_MANIFEST_SOURCE_FIELDS = ("repository", "ref", "revision", "path")


@dataclass(frozen=True)
class SubmissionIssue:
    package_urls: list[str]
    package_path: str
    notes: str
    errors: list[dict[str, str]]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    body = read_issue_body(args)
    clone_root = Path(args.clone_root) if args.clone_root else None
    report = validate_submission_body(body, clone_root=clone_root)

    if args.json_output:
        write_text_file(Path(args.json_output), json.dumps(report, indent=2, sort_keys=True))
    if args.markdown_output:
        write_text_file(Path(args.markdown_output), render_submission_report_markdown(report))
    if args.manifest_candidate_output:
        write_text_file(
            Path(args.manifest_candidate_output),
            render_accepted_manifest_candidate_yaml(report),
        )
    if not args.json_output and not args.markdown_output and not args.manifest_candidate_output:
        print(json.dumps(report, indent=2, sort_keys=True))

    return 0 if report["status"] == "valid" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate-index-submission",
        description="Validate a public SpecPM Index submission issue.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--issue-body-file", help="Path to a GitHub Issue body markdown file.")
    source.add_argument("--event-path", help="Path to a GitHub event JSON payload.")
    parser.add_argument("--clone-root", default="", help="Optional directory for temporary clones.")
    parser.add_argument("--json-output", help="Write machine-readable validation report.")
    parser.add_argument("--markdown-output", help="Write GitHub issue comment markdown report.")
    parser.add_argument(
        "--manifest-candidate-output",
        help="Write accepted-packages.yml candidate entries for valid repositories.",
    )
    return parser


def read_issue_body(args: argparse.Namespace) -> str:
    if args.issue_body_file:
        return Path(args.issue_body_file).read_text(encoding="utf-8")
    event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
    issue = event.get("issue")
    if not isinstance(issue, dict) or not isinstance(issue.get("body"), str):
        raise SystemExit("GitHub event payload does not contain issue.body.")
    return issue["body"]


def validate_submission_body(body: str, *, clone_root: Path | None = None) -> dict[str, Any]:
    issue = parse_submission_issue_body(body)
    report: dict[str, Any] = {
        "schemaVersion": SUBMISSION_SCHEMA_VERSION,
        "status": "invalid" if issue.errors else "valid",
        "package_path": issue.package_path,
        "repository_count": len(issue.package_urls),
        "repositories": [],
        "errors": issue.errors,
    }
    if issue.errors:
        return report

    clone_root = clone_root if clone_root and str(clone_root) else None
    with temporary_clone_root(clone_root) as root:
        for url in issue.package_urls:
            result = validate_submitted_repository(url, issue.package_path, root)
            report["repositories"].append(result)

    if any(item["status"] != "valid" for item in report["repositories"]):
        report["status"] = "invalid"
    return report


@contextmanager
def temporary_clone_root(path: Path | None) -> Iterator[Path]:
    if path is not None:
        path.mkdir(parents=True, exist_ok=True)
        yield path
        return
    with tempfile.TemporaryDirectory(prefix="specpm-submission-") as temp_dir:
        yield Path(temp_dir)


def parse_submission_issue_body(body: str) -> SubmissionIssue:
    sections = parse_issue_form_sections(body)
    urls_text = sections.get("new specpackage repositories", "").strip()
    package_path = normalize_optional_issue_value(sections.get("package path", "")) or "."
    notes = normalize_optional_issue_value(sections.get("notes", ""))

    errors: list[dict[str, str]] = []
    package_urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
    if not package_urls:
        errors.append(
            submission_error("package_urls_missing", "At least one package URL is required.")
        )
    if len(package_urls) > MAX_SUBMITTED_REPOSITORIES:
        errors.append(
            submission_error(
                "package_urls_too_many",
                f"At most {MAX_SUBMITTED_REPOSITORIES} package URLs can be submitted at once.",
            )
        )

    valid_urls: list[str] = []
    for url in package_urls:
        url_errors = validate_public_git_url(url)
        if url_errors:
            errors.extend(url_errors)
        else:
            valid_urls.append(url)

    path_errors = validate_package_path(package_path)
    errors.extend(path_errors)

    return SubmissionIssue(valid_urls, package_path, notes, errors)


def parse_issue_form_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        if line.startswith("### "):
            current = line.removeprefix("### ").strip().lower()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}


def normalize_optional_issue_value(value: str) -> str:
    stripped = value.strip()
    return "" if stripped in ISSUE_FORM_EMPTY_VALUES else stripped


def validate_public_git_url(url: str) -> list[dict[str, str]]:
    parsed = urlparse(url)
    errors: list[dict[str, str]] = []
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(
            submission_error(
                "repository_url_invalid",
                "Repository URL must be an https URL with a hostname.",
                field="package_urls",
            )
        )
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        errors.append(
            submission_error(
                "repository_url_path_invalid",
                "Repository URL must include an owner and repository path.",
                field="package_urls",
            )
        )
    if parsed.username or parsed.password:
        errors.append(
            submission_error(
                "repository_url_credentials",
                "Repository URL must not embed credentials.",
                field="package_urls",
            )
        )
    if parsed.params or parsed.query:
        errors.append(
            submission_error(
                "repository_url_query",
                "Repository URL must not include query parameters.",
                field="package_urls",
            )
        )
    if parsed.fragment:
        errors.append(
            submission_error(
                "repository_url_fragment",
                "Repository URL must not include a fragment.",
                field="package_urls",
            )
        )
    return errors


def validate_package_path(package_path: str) -> list[dict[str, str]]:
    if not package_path:
        return [submission_error("package_path_missing", "Package path must not be empty.")]
    if "\\" in package_path:
        return [
            submission_error(
                "package_path_invalid",
                "Package path must use POSIX separators.",
                field="package_path",
            )
        ]
    parsed = PurePosixPath(package_path)
    if parsed.is_absolute() or ".." in parsed.parts:
        return [
            submission_error(
                "package_path_escape",
                "Package path must be relative and must not contain '..'.",
                field="package_path",
            )
        ]
    return []


def validate_submitted_repository(url: str, package_path: str, clone_root: Path) -> dict[str, Any]:
    checkout = clone_root / clone_dir_name(url)
    if checkout.exists():
        shutil.rmtree(checkout)
    clone = clone_repository(url, checkout)
    if clone["status"] != "cloned":
        return {
            "url": url,
            "status": "invalid",
            "stage": "clone",
            "package_path": package_path,
            "errors": clone["errors"],
        }

    package_dir = (checkout / package_path).resolve()
    checkout_root = checkout.resolve()
    if not package_dir.is_relative_to(checkout_root):
        return {
            "url": url,
            "status": "invalid",
            "stage": "package_path",
            "package_path": package_path,
            "errors": [
                submission_error(
                    "package_path_escape",
                    "Package path resolves outside the cloned repository.",
                    field="package_path",
                )
            ],
        }

    validation = validate_package(package_dir)
    return {
        "url": url,
        "status": "valid" if validation["status"] in {"valid", "warning_only"} else "invalid",
        "stage": "validate",
        "package_path": package_path,
        "source": {
            "repository": url,
            "ref": clone.get("ref"),
            "revision": clone.get("revision"),
            "path": package_path,
        },
        "validation_status": validation["status"],
        "package_identity": validation["package_identity"],
        "error_count": validation["error_count"],
        "warning_count": validation["warning_count"],
        "errors": validation["errors"],
        "warnings": validation["warnings"],
    }


def clone_repository(url: str, checkout: Path) -> dict[str, Any]:
    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--filter",
        "blob:none",
        "--no-tags",
        "--no-recurse-submodules",
        "--single-branch",
        url,
        str(checkout),
    ]
    env = os.environ.copy()
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "invalid",
            "errors": [
                submission_error(
                    "repository_clone_failed",
                    f"Repository could not be cloned: {exc}",
                    field="package_urls",
                )
            ],
        }
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "git clone failed"
        return {
            "status": "invalid",
            "errors": [
                submission_error(
                    "repository_clone_failed",
                    message,
                    field="package_urls",
                )
            ],
        }
    revision = read_clone_metadata(["git", "-C", str(checkout), "rev-parse", "HEAD"])
    ref = read_clone_metadata(["git", "-C", str(checkout), "branch", "--show-current"])
    return {
        "status": "cloned",
        "ref": ref.strip() or None,
        "revision": revision.strip().lower(),
        "errors": [],
    }


def read_clone_metadata(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout


def clone_dir_name(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    name = Path(urlparse(url).path).name.removesuffix(".git") or "repository"
    sanitized = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in name)
    return f"{sanitized}-{digest}"


def render_submission_report_markdown(report: dict[str, Any]) -> str:
    status_icon = "PASS" if report["status"] == "valid" else "FAIL"
    lines = [
        "## SpecPM Index Submission Check",
        "",
        f"Status: `{report['status']}` ({status_icon})",
        f"Package path: `{report['package_path']}`",
        f"Repositories: `{report['repository_count']}`",
        "",
    ]
    if report["errors"]:
        lines.append("### Submission Errors")
        for issue in report["errors"]:
            lines.append(f"- `{issue['code']}`: {issue['message']}")
        lines.append("")

    if report["repositories"]:
        lines.append("### Repository Results")
        for item in report["repositories"]:
            identity = item.get("package_identity") or {}
            package_id = identity.get("package_id", "unknown")
            version = identity.get("version", "unknown")
            lines.append(
                f"- `{item['status']}` `{item['url']}` "
                f"stage=`{item['stage']}` package=`{package_id}@{version}`"
            )
            source = item.get("source") or {}
            if item["status"] == "valid" and source.get("ref") and source.get("revision"):
                lines.extend(
                    [
                        "  - Accepted manifest candidate:",
                        "    ```yaml",
                        f"    - repository: {source['repository']}",
                        f"      ref: {source['ref']}",
                        f"      revision: {source['revision']}",
                        f"      path: {source['path']}",
                        "    ```",
                    ]
                )
            for issue in item.get("errors", []):
                lines.append(f"  - `{issue['code']}`: {issue['message']}")
        lines.append("")

    lines.append(
        "SpecPM treats submitted package content as data and does not execute package content "
        "during validation."
    )
    return "\n".join(lines).rstrip() + "\n"


def accepted_manifest_candidates(report: dict[str, Any]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if report.get("status") != "valid":
        return candidates
    for item in report.get("repositories", []):
        if not isinstance(item, dict) or item.get("status") != "valid":
            continue
        source = item.get("source")
        if not isinstance(source, dict):
            continue
        candidate = {
            "repository": source.get("repository"),
            "ref": source.get("ref"),
            "revision": source.get("revision"),
            "path": source.get("path"),
        }
        if all(isinstance(value, str) and value for value in candidate.values()):
            candidates.append(candidate)
    return candidates


def render_accepted_manifest_candidate_yaml(report: dict[str, Any]) -> str:
    document = {
        "schemaVersion": ACCEPTED_MANIFEST_CANDIDATE_SCHEMA_VERSION,
        "packages": accepted_manifest_candidates(report),
    }
    return yaml.safe_dump(document, sort_keys=False)


def prepare_accepted_manifest_pr_main(argv: list[str] | None = None) -> int:
    parser = build_accepted_manifest_pr_parser()
    args = parser.parse_args(argv)
    submission_report = json.loads(Path(args.submission_report).read_text(encoding="utf-8"))
    report = prepare_accepted_manifest_pr(
        submission_report,
        Path(args.manifest),
        issue_url=args.issue_url,
        apply_update=args.apply,
    )

    if args.json_output:
        write_text_file(Path(args.json_output), json.dumps(report, indent=2, sort_keys=True))
    if args.pr_body_output:
        write_text_file(Path(args.pr_body_output), render_accepted_manifest_pr_body(report))
    if not args.json_output and not args.pr_body_output:
        print(json.dumps(report, indent=2, sort_keys=True))

    return 0 if report["status"] in {"prepared", "applied", "unchanged"} else 1


def build_accepted_manifest_pr_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prepare-accepted-manifest-pr",
        description="Prepare a reviewed accepted-packages.yml change from a validation report.",
    )
    parser.add_argument(
        "--submission-report",
        required=True,
        help="Path to a valid submission-report.json produced by validate_index_submission.py.",
    )
    parser.add_argument(
        "--manifest",
        default="public-index/accepted-packages.yml",
        help="Accepted public index manifest to update or inspect.",
    )
    parser.add_argument(
        "--issue-url",
        default="",
        help="Optional package-submission issue URL to include in generated PR context.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Append new candidate entries to the accepted manifest.",
    )
    parser.add_argument("--json-output", help="Write machine-readable helper report.")
    parser.add_argument("--pr-body-output", help="Write draft pull request body markdown.")
    return parser


def prepare_accepted_manifest_pr(
    submission_report: dict[str, Any],
    manifest_path: Path,
    *,
    issue_url: str = "",
    apply_update: bool = False,
) -> dict[str, Any]:
    candidates = accepted_manifest_candidate_packages(submission_report)
    manifest = read_accepted_manifest_for_update(manifest_path)
    errors = list(manifest["errors"])

    if submission_report.get("status") != "valid":
        errors.append(
            submission_error(
                "submission_report_invalid",
                "Accepted manifest PR helper requires a valid submission report.",
            )
        )
    if not candidates:
        errors.append(
            submission_error(
                "accepted_manifest_candidates_missing",
                "Submission report does not contain accepted manifest candidates.",
            )
        )

    if errors:
        return accepted_manifest_pr_report(
            "invalid",
            manifest_path,
            issue_url,
            candidates,
            [],
            [],
            errors,
            applied=False,
        )

    known_sources = list(manifest["sources"])
    added: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for candidate in candidates:
        source = candidate["source"]
        if any(same_accepted_manifest_source(source, existing) for existing in known_sources):
            skipped.append(
                {
                    "reason": "exact_source_already_present",
                    "package": candidate,
                }
            )
            continue
        added.append(candidate)
        known_sources.append(source)

    applied = False
    if apply_update and added:
        append_accepted_manifest_sources(manifest_path, [item["source"] for item in added])
        applied = True

    status = "applied" if applied else "prepared"
    if not added:
        status = "unchanged"

    return accepted_manifest_pr_report(
        status,
        manifest_path,
        issue_url,
        candidates,
        added,
        skipped,
        [],
        applied=applied,
    )


def accepted_manifest_candidate_packages(report: dict[str, Any]) -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    if report.get("status") != "valid":
        return packages
    for item in report.get("repositories", []):
        if not isinstance(item, dict) or item.get("status") != "valid":
            continue
        source = normalized_accepted_manifest_source(item.get("source"))
        if source is None:
            continue
        identity = (
            item.get("package_identity") if isinstance(item.get("package_identity"), dict) else {}
        )
        package_id = (
            identity.get("package_id") if isinstance(identity.get("package_id"), str) else ""
        )
        version = identity.get("version") if isinstance(identity.get("version"), str) else ""
        packages.append(
            {
                "package_id": package_id,
                "version": version,
                "package_ref": f"{package_id}@{version}" if package_id and version else "unknown",
                "source": source,
            }
        )
    return packages


def read_accepted_manifest_for_update(manifest_path: Path) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not manifest_path.is_file():
        return {
            "sources": [],
            "errors": [
                submission_error("accepted_manifest_missing", "Accepted manifest file is missing.")
            ],
        }
    try:
        loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return {
            "sources": [],
            "errors": [
                submission_error(
                    "accepted_manifest_yaml_invalid",
                    f"Accepted manifest YAML could not be parsed: {exc}",
                )
            ],
        }
    if not isinstance(loaded, dict):
        errors.append(
            submission_error(
                "accepted_manifest_invalid",
                "Accepted manifest must be a mapping.",
            )
        )
        return {"sources": [], "errors": errors}
    if loaded.get("schemaVersion") != 1:
        errors.append(
            submission_error(
                "accepted_manifest_schema_version_invalid",
                "Accepted manifest schemaVersion must be 1.",
                field="schemaVersion",
            )
        )
    packages = loaded.get("packages")
    if not isinstance(packages, list):
        errors.append(
            submission_error(
                "accepted_manifest_packages_invalid",
                "Accepted manifest packages must be a list.",
                field="packages",
            )
        )
        return {"sources": [], "errors": errors}
    sources = [
        source
        for item in packages
        if (source := normalized_accepted_manifest_source(item)) is not None
    ]
    return {"sources": sources, "errors": errors}


def normalized_accepted_manifest_source(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    source = {field: value.get(field) for field in ACCEPTED_MANIFEST_SOURCE_FIELDS}
    if all(isinstance(item, str) and item for item in source.values()):
        return {field: str(source[field]) for field in ACCEPTED_MANIFEST_SOURCE_FIELDS}
    return None


def same_accepted_manifest_source(left: dict[str, str], right: dict[str, str]) -> bool:
    return all(left[field] == right[field] for field in ACCEPTED_MANIFEST_SOURCE_FIELDS)


def append_accepted_manifest_sources(manifest_path: Path, sources: list[dict[str, str]]) -> None:
    if not sources:
        return
    loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not isinstance(loaded.get("packages"), list):
        raise ValueError("accepted manifest must be a mapping with a packages list")
    loaded["packages"].extend(sources)
    manifest_path.write_text(yaml.safe_dump(loaded, sort_keys=False), encoding="utf-8")


def accepted_manifest_pr_report(
    status: str,
    manifest_path: Path,
    issue_url: str,
    candidates: list[dict[str, Any]],
    added: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    errors: list[dict[str, str]],
    *,
    applied: bool,
) -> dict[str, Any]:
    return {
        "schemaVersion": ACCEPTED_MANIFEST_PR_SCHEMA_VERSION,
        "status": status,
        "applied": applied,
        "manifest": str(manifest_path),
        "issue_url": issue_url,
        "candidate_count": len(candidates),
        "added_count": len(added),
        "skipped_count": len(skipped),
        "candidates": candidates,
        "added": added,
        "skipped": skipped,
        "errors": errors,
    }


def render_accepted_manifest_pr_body(report: dict[str, Any]) -> str:
    issue_url = report.get("issue_url") or "not provided"
    package_lines = []
    for item in report.get("added", []):
        source = item["source"]
        package_lines.append(
            "- "
            f"`{item.get('package_ref', 'unknown')}` from `{source['repository']}` "
            f"ref `{source['ref']}` at `{source['revision']}` path `{source['path']}`"
        )
    if not package_lines:
        package_lines.append("- No new accepted manifest entries were added.")

    lines = [
        "## Motivation",
        "",
        "Accept a validated public SpecPackage submission into the generated public index.",
        "",
        f"Submission issue: {issue_url}",
        f"Helper report status: `{report['status']}`",
        "",
        "## Goals",
        "",
        "- Add reviewed, pinned package source records to `public-index/accepted-packages.yml`.",
        "- Keep public index acceptance auditable through issues, pull requests, and CI.",
        "- Preserve the static read-only registry boundary.",
        "",
        "## Changes",
        "",
        *package_lines,
        "",
        "## Validation",
        "",
        "- Pending maintainer/CI validation: "
        "rerun package-submission validation for the issue body.",
        "- Pending maintainer/CI validation: "
        "run public index generation against the updated manifest.",
        "- Pending maintainer/CI validation: run local Docker smoke if registry output changes.",
        "",
        "## Boundaries and Non-Goals",
        "",
        "- Does not decide package acceptance automatically.",
        "- Does not add `specpm publish`, upload endpoints, remote mutation APIs, "
        "package install, archive acquisition, package execution, or namespace ownership grants.",
        "",
        "## Notes",
        "",
        "- Generated by `scripts/prepare_accepted_manifest_pr.py`; maintainers should edit "
        "this draft with the exact validation commands they ran before merge.",
    ]
    return "\n".join(lines) + "\n"


def submission_error(code: str, message: str, *, field: str | None = None) -> dict[str, str]:
    issue = {
        "severity": "error",
        "code": code,
        "message": message,
    }
    if field is not None:
        issue["field"] = field
    return issue


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
