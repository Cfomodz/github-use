"""Community health file checks (CONTRIBUTING, CODE_OF_CONDUCT, issue/PR templates)."""

from __future__ import annotations

from repo_scanner.checks import Check, Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo


class CommunityCheck:
    name = "community"

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]:
        findings: list[Finding] = []
        all_paths_lower = {p.lower() for p in contents.tree_listing}
        root_lower = {e.lower() for e in contents.root_entries}

        # CONTRIBUTING
        has_contributing = (
            "contributing.md" in root_lower
            or ".github/contributing.md" in all_paths_lower
        )
        if not has_contributing:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="No CONTRIBUTING guide",
                detail="No CONTRIBUTING.md found at the root or in .github/.",
                suggestion="Add a CONTRIBUTING.md to explain how others can contribute.",
            ))

        # CODE_OF_CONDUCT
        has_coc = (
            "code_of_conduct.md" in root_lower
            or ".github/code_of_conduct.md" in all_paths_lower
        )
        if not has_coc:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No Code of Conduct",
                detail="No CODE_OF_CONDUCT.md found.",
                suggestion="Add a CODE_OF_CONDUCT.md (e.g., Contributor Covenant) to set community expectations.",
            ))

        # Issue templates
        if not contents.issue_templates:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No issue templates",
                detail="No GitHub issue templates found in .github/ISSUE_TEMPLATE/.",
                suggestion="Add issue templates for bug reports and feature requests to get structured feedback.",
            ))

        # PR template
        if not contents.pr_template:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No pull request template",
                detail="No PULL_REQUEST_TEMPLATE.md found.",
                suggestion="Add a PR template to standardize pull request descriptions.",
            ))

        return findings


check = CommunityCheck()
