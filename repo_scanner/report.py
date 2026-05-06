"""Report generation – terminal and markdown output."""

from __future__ import annotations

import sys
from pathlib import Path

from repo_scanner.checks import Severity
from repo_scanner.scanner import ScanResult

# ANSI colors for terminal
_COLORS = {
    Severity.CRITICAL: "\033[1;31m",  # bold red
    Severity.WARNING: "\033[1;33m",   # bold yellow
    Severity.INFO: "\033[0;36m",      # cyan
}
_RESET = "\033[0m"
_BOLD = "\033[1m"

_SEVERITY_ICONS = {
    Severity.CRITICAL: "X",
    Severity.WARNING: "!",
    Severity.INFO: "i",
}

_MD_SEVERITY_ICONS = {
    Severity.CRITICAL: ":red_circle:",
    Severity.WARNING: ":yellow_circle:",
    Severity.INFO: ":blue_circle:",
}


def print_terminal_report(results: list[ScanResult], *, verbose: bool = False) -> None:
    """Print a colored summary to the terminal."""
    total_findings = 0
    total_critical = 0
    total_warning = 0
    total_info = 0

    for result in results:
        findings = result.all_findings
        if not findings and not result.error:
            if verbose:
                print(f"\n{_BOLD}{result.repo.full_name}{_RESET} — no issues found")
            continue

        print(f"\n{'=' * 70}")
        print(f"{_BOLD}{result.repo.full_name}{_RESET}")
        if result.repo.description:
            print(f"  {result.repo.description}")
        print(f"  Language: {result.repo.language or 'unknown'} | "
              f"Stars: {result.repo.stargazers_count} | "
              f"License: {result.repo.license_key or 'none'}")
        print(f"{'=' * 70}")

        if result.error:
            print(f"  {_COLORS[Severity.WARNING]}NOTE: {result.error}{_RESET}")

        # Group by severity
        for severity in (Severity.CRITICAL, Severity.WARNING, Severity.INFO):
            group = [f for f in findings if f.severity == severity]
            if not group:
                continue
            color = _COLORS[severity]
            icon = _SEVERITY_ICONS[severity]
            for f in group:
                total_findings += 1
                if severity == Severity.CRITICAL:
                    total_critical += 1
                elif severity == Severity.WARNING:
                    total_warning += 1
                else:
                    total_info += 1

                source = f"[{f.check_name}]" if f.check_name != "ai" else "[ai]"
                print(f"  {color}[{icon}] {f.title}{_RESET} {source}")
                print(f"      {f.detail}")
                if f.suggestion:
                    print(f"      -> {f.suggestion}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"{_BOLD}Summary:{_RESET} scanned {len(results)} repos, "
          f"found {total_findings} findings "
          f"({total_critical} critical, {total_warning} warnings, {total_info} info)")
    print(f"{'=' * 70}")


def generate_markdown_report(results: list[ScanResult]) -> str:
    """Generate a Markdown report string."""
    lines = ["# Repository Improvement Scan Report\n"]

    total_findings = 0
    summary_rows: list[str] = []

    for result in results:
        findings = result.all_findings
        n_crit = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        n_warn = sum(1 for f in findings if f.severity == Severity.WARNING)
        n_info = sum(1 for f in findings if f.severity == Severity.INFO)
        total_findings += len(findings)
        summary_rows.append(
            f"| [{result.repo.full_name}](https://github.com/{result.repo.full_name}) "
            f"| {result.repo.language or '-'} "
            f"| {n_crit} | {n_warn} | {n_info} |"
        )

    # Summary table
    lines.append("## Overview\n")
    lines.append(f"Scanned **{len(results)}** repositories, found **{total_findings}** findings.\n")
    lines.append("| Repository | Language | Critical | Warnings | Info |")
    lines.append("|---|---|---|---|---|")
    lines.extend(summary_rows)
    lines.append("")

    # Per-repo details
    for result in results:
        findings = result.all_findings
        if not findings and not result.error:
            continue

        lines.append(f"---\n## {result.repo.full_name}\n")
        if result.repo.description:
            lines.append(f"> {result.repo.description}\n")
        if result.error:
            lines.append(f"> **Note:** {result.error}\n")

        for severity in (Severity.CRITICAL, Severity.WARNING, Severity.INFO):
            group = [f for f in findings if f.severity == severity]
            if not group:
                continue
            lines.append(f"### {severity.value.capitalize()} ({len(group)})\n")
            for f in group:
                icon = _MD_SEVERITY_ICONS[severity]
                source = f" `{f.check_name}`" if f.check_name else ""
                lines.append(f"- {icon} **{f.title}**{source}")
                lines.append(f"  - {f.detail}")
                if f.suggestion:
                    lines.append(f"  - *Suggestion:* {f.suggestion}")
            lines.append("")

    return "\n".join(lines)


def save_markdown_report(results: list[ScanResult], path: str) -> None:
    """Write the Markdown report to a file."""
    content = generate_markdown_report(results)
    Path(path).write_text(content, encoding="utf-8")
    print(f"Report saved to {path}", file=sys.stderr)
