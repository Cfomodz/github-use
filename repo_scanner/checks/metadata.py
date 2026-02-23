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
