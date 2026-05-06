"""GitHub Actions / CI workflow checks."""

from __future__ import annotations

from repo_scanner.checks import Check, Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo


class WorkflowsCheck:
    name = "workflows"

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]:
        findings: list[Finding] = []

        if not contents.workflow_files:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.CRITICAL,
                title="No GitHub Actions workflows",
                detail="The .github/workflows/ directory is missing or empty.",
                suggestion=(
                    "Add at least a basic CI workflow that runs on push/PR. "
                    "GitHub provides starter workflows for most languages."
                ),
            ))
        else:
            names_lower = [w.lower() for w in contents.workflow_files]
            has_ci = any(
                kw in n for n in names_lower
                for kw in ("ci", "build", "test", "lint", "check")
            )
            if not has_ci:
                findings.append(Finding(
                    check_name=self.name,
                    severity=Severity.WARNING,
                    title="No obvious CI workflow",
                    detail=(
                        f"Found workflow files ({', '.join(contents.workflow_files)}) but none "
                        "appear to be a standard CI/build/test pipeline."
                    ),
                    suggestion="Ensure at least one workflow runs tests or builds on push and pull_request events.",
                ))

        return findings


check = WorkflowsCheck()
