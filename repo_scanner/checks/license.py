"""License file checks."""

from __future__ import annotations

from repo_scanner.checks import Check, Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo


class LicenseCheck:
    name = "license"

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]:
        findings: list[Finding] = []

        license_files = [
            e for e in contents.root_entries
            if e.upper().startswith("LICENSE") or e.upper().startswith("LICENCE")
        ]

        if not license_files and not repo.license_key:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.CRITICAL,
                title="No license",
                detail="The repository has no LICENSE file and GitHub does not detect a license.",
                suggestion=(
                    "Add a LICENSE file. Without one, the code is under exclusive copyright "
                    "by default and cannot be legally reused. See https://choosealicense.com/"
                ),
            ))
        elif repo.license_key and repo.license_key == "other":
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="Non-standard license",
                detail="GitHub detected a license but could not identify it as a standard SPDX license.",
                suggestion="Consider using a well-known license (MIT, Apache-2.0, GPL-3.0) for clarity.",
            ))

        return findings


check = LicenseCheck()
