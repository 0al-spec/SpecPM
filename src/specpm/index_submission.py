from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

from specpm.core import validate_package

SUBMISSION_SCHEMA_VERSION = 1
MAX_SUBMITTED_REPOSITORIES = 10
ISSUE_FORM_EMPTY_VALUES = {"", "_No response_"}


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
    if not args.json_output and not args.markdown_output:
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
                f"Repository URL must be an https URL: {url}",
                field="package_urls",
            )
        )
    if parsed.username or parsed.password:
        errors.append(
            submission_error(
                "repository_url_credentials",
                f"Repository URL must not embed credentials: {url}",
                field="package_urls",
            )
        )
    if parsed.fragment:
        errors.append(
            submission_error(
                "repository_url_fragment",
                f"Repository URL must not include a fragment: {url}",
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
        "--no-tags",
        "--no-recurse-submodules",
        url,
        str(checkout),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
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
    return {"status": "cloned", "errors": []}


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
            for issue in item.get("errors", []):
                lines.append(f"  - `{issue['code']}`: {issue['message']}")
        lines.append("")

    lines.append(
        "SpecPM treats submitted package content as data and does not execute package content "
        "during validation."
    )
    return "\n".join(lines).rstrip() + "\n"


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
