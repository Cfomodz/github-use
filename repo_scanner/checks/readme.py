"""Checks for README presence and quality."""

from __future__ import annotations

import re

from repo_scanner.checks import Check, Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo

# Rough heuristic thresholds
_MIN_USEFUL_LENGTH = 200  # characters
_BADGE_PATTERN = re.compile(r"\[!\[.*?\]\(.*?\)\]")
_IMAGE_PATTERN = re.compile(r"!\[.*?\]\(.*?\)")
_HEADING_PATTERN = re.compile(r"^#{1,3}\s+", re.MULTILINE)
_CODE_BLOCK = re.compile(r"```")
_INSTALL_KEYWORDS = re.compile(
    r"(install|setup|getting started|quickstart|requirements|prerequisites)",
    re.IGNORECASE,
)
_USAGE_KEYWORDS = re.compile(r"(usage|example|how to use|demo|tutorial)", re.IGNORECASE)


class ReadmeCheck:
    name = "readme"

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]:
        findings: list[Finding] = []
        readme = contents.readme_content

        if not readme:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.CRITICAL,
                title="No README file",
                detail="The repository has no README.md.",
                suggestion="Add a README.md with a project description, installation instructions, and usage examples.",
            ))
            return findings  # nothing else to check

        if len(readme) < _MIN_USEFUL_LENGTH:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="README is very short",
                detail=f"README is only {len(readme)} characters. It likely lacks essential sections.",
                suggestion="Expand the README with sections for description, installation, usage, and contributing.",
            ))

        # Check for project logo / icon
        images = _IMAGE_PATTERN.findall(readme)
        badges = _BADGE_PATTERN.findall(readme)
        non_badge_images = len(images) - len(badges)
        if non_badge_images < 1:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No project logo or screenshot in README",
                detail="The README contains no images besides badges.",
                suggestion="Add a project logo or screenshot near the top of the README to give the repo a visual identity.",
            ))

        # Check for badges
        if not badges:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No status badges in README",
                detail="Badges (CI status, coverage, version, license) are missing.",
                suggestion="Add badges for build status, test coverage, latest release, and license.",
            ))

        # Check for installation section
        if not _INSTALL_KEYWORDS.search(readme):
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="README missing installation/setup instructions",
                detail="No section mentioning install, setup, or getting started was found.",
                suggestion="Add a section explaining how to install or set up the project.",
            ))

        # Check for usage section
        if not _USAGE_KEYWORDS.search(readme):
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="README missing usage examples",
                detail="No section mentioning usage, examples, or how-to was found.",
                suggestion="Add a usage section with example commands or code snippets.",
            ))

        # Check for code blocks (suggests concrete examples)
        if not _CODE_BLOCK.search(readme):
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="README has no code blocks",
                detail="No fenced code blocks found. Code examples help users get started quickly.",
                suggestion="Include fenced code blocks (```) showing installation commands or API usage.",
            ))

        return findings


check = ReadmeCheck()
