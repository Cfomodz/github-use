"""Security-related repo checks."""

from __future__ import annotations

from repo_scanner.checks import Check, Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo


class SecurityCheck:
    name = "security"

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]:
        findings: list[Finding] = []
        all_paths_lower = {p.lower() for p in contents.tree_listing}
        root_lower = {e.lower() for e in contents.root_entries}

        # SECURITY.md
        has_security = (
            "security.md" in root_lower
            or ".github/security.md" in all_paths_lower
        )
        if not has_security:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="No security policy",
                detail="No SECURITY.md found.",
                suggestion=(
                    "Add a SECURITY.md describing how to responsibly report vulnerabilities. "
                    "GitHub will surface this in the repo's Security tab."
                ),
            ))

        # Dependabot
        if not contents.has_dependabot:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="No Dependabot configuration",
                detail="No .github/dependabot.yml found.",
                suggestion=(
                    "Add a dependabot.yml to automatically receive pull requests "
                    "for outdated or vulnerable dependencies."
                ),
            ))

        return findings


check = SecurityCheck()
