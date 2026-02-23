"""Core scanner orchestrator – runs all checks against a repository."""

from __future__ import annotations

from dataclasses import dataclass, field

from repo_scanner.checks import Finding
from repo_scanner.checks.readme import ReadmeCheck
from repo_scanner.checks.license import LicenseCheck
from repo_scanner.checks.workflows import WorkflowsCheck
from repo_scanner.checks.tests import TestsCheck
from repo_scanner.checks.community import CommunityCheck
from repo_scanner.checks.security import SecurityCheck
from repo_scanner.checks.metadata import MetadataCheck
from repo_scanner.github import RepoContents, RepoInfo

ALL_CHECKS = [
    ReadmeCheck(),
    LicenseCheck(),
    WorkflowsCheck(),
    TestsCheck(),
    CommunityCheck(),
    SecurityCheck(),
    MetadataCheck(),
]


@dataclass
class ScanResult:
    """Result of scanning a single repository."""

    repo: RepoInfo
    findings: list[Finding] = field(default_factory=list)
    ai_findings: list[Finding] = field(default_factory=list)
    error: str | None = None

    @property
    def all_findings(self) -> list[Finding]:
        return self.findings + self.ai_findings


def scan_repo(
    repo: RepoInfo,
    contents: RepoContents,
    use_ai: bool = True,
) -> ScanResult:
    """Run all programmatic checks, then optionally AI analysis."""
    result = ScanResult(repo=repo)

    # Programmatic checks
    for check in ALL_CHECKS:
        try:
            result.findings.extend(check.run(repo, contents))
        except Exception as exc:
            result.findings.append(Finding(
                check_name=check.name,
                severity=__import__("repo_scanner.checks", fromlist=["Severity"]).Severity.INFO,
                title=f"Check '{check.name}' errored",
                detail=str(exc),
                suggestion="This check encountered an unexpected error. Please report it.",
            ))

    # AI analysis
    if use_ai:
        try:
            from repo_scanner.ai import analyze
            result.ai_findings = analyze(repo, contents, result.findings)
        except EnvironmentError as exc:
            result.error = str(exc)
        except Exception as exc:
            result.error = f"AI analysis failed: {exc}"

    return result
