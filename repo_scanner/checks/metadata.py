"""Repository metadata and configuration checks."""

from __future__ import annotations

from repo_scanner.checks import Check, Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo

# Languages that conventionally have a .gitignore
_LANGUAGES_NEEDING_GITIGNORE = {
    "python", "javascript", "typescript", "java", "kotlin", "go", "rust",
    "c", "c++", "c#", "ruby", "php", "swift", "dart", "elixir",
}


class MetadataCheck:
    name = "metadata"

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]:
        findings: list[Finding] = []

        # Empty / abandoned repo (no files or only a README)
        non_meta_files = [
            p for p in contents.tree_listing
            if not p.lower().startswith(("readme", "license", ".git"))
        ]
        if not contents.tree_listing:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.CRITICAL,
                title="Repository appears empty",
                detail="No files were found in the repository's default branch.",
                suggestion=(
                    "This repo has no content. Either add code, repurpose it, or consider deleting it "
                    "to reduce clutter."
                ),
            ))
        elif not non_meta_files:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="Repository contains only meta files",
                detail="The repo only has a README, LICENSE, or .git config — no actual project files.",
                suggestion=(
                    "This repo has no substantive content beyond boilerplate. Add project files, "
                    "repurpose it, or consider deleting it."
                ),
            ))

        # No detected programming language
        if not repo.language:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="No programming language detected",
                detail="GitHub does not detect any programming language for this repository.",
                suggestion=(
                    "This usually means the repo is empty, config-only, or docs-only. "
                    "If it should contain code, add source files. Otherwise consider whether "
                    "this repo is still needed."
                ),
            ))

        # Profile README repo (owner/owner)
        if repo.name.lower() == repo.owner.lower():
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="Profile README repository",
                detail=(
                    f"This is the special {repo.owner}/{repo.owner} profile repo. "
                    "Its README appears on your GitHub profile page."
                ),
                suggestion=(
                    "Make sure this README is up-to-date and represents you well — "
                    "it's the first thing visitors see on your profile."
                ),
            ))

        # .github org/user config repo
        if repo.name.lower() == ".github":
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="Organization/user .github config repository",
                detail=(
                    "This is the special .github repo for default community health files, "
                    "issue templates, and funding config."
                ),
                suggestion=(
                    "Ensure this repo contains useful defaults (issue templates, CONTRIBUTING.md, "
                    "FUNDING.yml) that apply across your other repositories."
                ),
            ))

        # Description
        if not repo.description:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="No repository description",
                detail="The GitHub repo description field is empty.",
                suggestion="Add a short description in the repo settings – it appears in search results and repo lists.",
            ))

        # Topics
        if not repo.topics:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No repository topics",
                detail="The repo has no topic tags.",
                suggestion="Add topic tags (e.g., language, framework, domain) to improve discoverability.",
            ))

        # Homepage
        if not repo.homepage and not repo.has_pages:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No homepage URL set",
                detail="The repo has no homepage URL and GitHub Pages is not enabled.",
                suggestion="Set a homepage URL in repo settings (docs site, project website, etc.).",
            ))

        # .gitignore
        lang = (repo.language or "").lower()
        if lang in _LANGUAGES_NEEDING_GITIGNORE and not contents.gitignore_content:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.WARNING,
                title="No .gitignore file",
                detail=f"A {repo.language} project should have a .gitignore to avoid committing build artifacts.",
                suggestion=f"Add a .gitignore appropriate for {repo.language}. See https://github.com/github/gitignore",
            ))

        # CODEOWNERS
        if not contents.has_codeowners:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.INFO,
                title="No CODEOWNERS file",
                detail="No CODEOWNERS file found.",
                suggestion="Add a CODEOWNERS file to automatically request reviews from the right people.",
            ))

        return findings


check = MetadataCheck()
