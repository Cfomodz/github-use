"""CLI entry point for the repository improvement scanner."""

from __future__ import annotations

import argparse
import sys

from repo_scanner.github import RepoInfo, fetch_repo_contents, list_repos
from repo_scanner.scanner import scan_repo, ScanResult
from repo_scanner.report import print_terminal_report, save_markdown_report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="repo-scanner",
        description="Scan your GitHub repositories for structural and community-health improvements.",
    )
    p.add_argument(
        "user",
        nargs="?",
        default=None,
        help="GitHub username to scan. Defaults to the authenticated user.",
    )
    p.add_argument(
        "--repo", "-r",
        action="append",
        default=[],
        dest="repos",
        help="Scan only specific repo(s) by owner/name. Can be repeated.",
    )
    p.add_argument(
        "--limit", "-l",
        type=int,
        default=100,
        help="Max number of repos to fetch (default: 100).",
    )
    p.add_argument(
        "--include-forks",
        action="store_true",
        help="Include forked repositories.",
    )
    p.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived repositories.",
    )
    p.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip DeepSeek AI analysis (only run programmatic checks).",
    )
    p.add_argument(
        "--output", "-o",
        default="report.md",
        help="Markdown report output path (default: report.md).",
    )
    p.add_argument(
        "--no-report",
        action="store_true",
        help="Skip writing the Markdown report file.",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show repos with no findings too.",
    )
    p.add_argument(
        "--severity",
        choices=["critical", "warning", "info"],
        default="info",
        help="Minimum severity to display (default: info = show all).",
    )
    return p.parse_args(argv)


def _filter_severity(results: list[ScanResult], min_severity: str) -> list[ScanResult]:
    """Remove findings below the minimum severity threshold."""
    from repo_scanner.checks import Severity

    order = {"critical": 0, "warning": 1, "info": 2}
    threshold = order.get(min_severity, 2)

    for result in results:
        result.findings = [
            f for f in result.findings
            if order.get(f.severity.value, 2) <= threshold
        ]
        result.ai_findings = [
            f for f in result.ai_findings
            if order.get(f.severity.value, 2) <= threshold
        ]
    return results


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    # Resolve repos to scan
    if args.repos:
        # Fetch specific repos via gh api
        repos = _fetch_specific_repos(args.repos)
    else:
        print(f"Fetching repositories{' for ' + args.user if args.user else ''}...", file=sys.stderr)
        repos = list_repos(
            user=args.user,
            limit=args.limit,
            include_forks=args.include_forks,
            include_archived=args.include_archived,
        )

    if not repos:
        print("No repositories found.", file=sys.stderr)
        sys.exit(0)

    print(f"Scanning {len(repos)} repositories...\n", file=sys.stderr)

    results: list[ScanResult] = []
    for i, repo in enumerate(repos, 1):
        print(f"[{i}/{len(repos)}] {repo.full_name}...", file=sys.stderr)
        try:
            contents = fetch_repo_contents(repo)
            result = scan_repo(repo, contents, use_ai=not args.no_ai)
            results.append(result)
        except Exception as exc:
            sr = ScanResult(repo=repo, error=str(exc))
            results.append(sr)

    # Filter by severity
    results = _filter_severity(results, args.severity)

    # Output
    print_terminal_report(results, verbose=args.verbose)

    if args.output and not args.no_report:
        save_markdown_report(results, args.output)


def _fetch_specific_repos(repo_names: list[str]) -> list[RepoInfo]:
    """Fetch metadata for specifically named repos."""
    import json
    from repo_scanner.github import _run_gh

    repos: list[RepoInfo] = []
    for name in repo_names:
        raw = _run_gh(
            "api", f"repos/{name}",
            "--jq", ".",
        )
        item = json.loads(raw)
        owner = item.get("owner", {})
        license_info = item.get("license") or {}
        topics = item.get("topics", [])

        # Normalize to lowercase key matching licenseInfo.key from list_repos.
        # The REST API returns spdx_id in uppercase (e.g. "MIT") or "NOASSERTION"
        # for unrecognised licenses; map both empty and "NOASSERTION" to None.
        spdx_id = license_info.get("spdx_id") if isinstance(license_info, dict) else None
        license_key = spdx_id.lower() if spdx_id and spdx_id.upper() != "NOASSERTION" else None

        repos.append(RepoInfo(
            full_name=item.get("full_name", name),
            name=item.get("name", name.split("/")[-1]),
            owner=owner.get("login", ""),
            description=item.get("description") or "",
            default_branch=item.get("default_branch", "main"),
            is_fork=item.get("fork", False),
            is_archived=item.get("archived", False),
            is_private=item.get("private", False),
            has_issues=item.get("has_issues", True),
            has_wiki=item.get("has_wiki", False),
            has_pages=item.get("has_pages", False),
            license_key=license_key,
            topics=topics,
            homepage=item.get("homepage") or "",
            language=item.get("language"),
            stargazers_count=item.get("stargazers_count", 0),
            open_issues_count=item.get("open_issues_count", 0),
        ))
    return repos
