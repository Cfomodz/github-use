"""GitHub CLI (gh) integration for fetching repos and repo contents."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class RepoInfo:
    """Metadata about a single GitHub repository."""

    full_name: str  # owner/repo
    name: str
    owner: str
    description: str
    default_branch: str
    is_fork: bool
    is_archived: bool
    is_private: bool
    has_issues: bool
    has_wiki: bool
    has_pages: bool
    license_key: str | None
    topics: list[str]
    homepage: str
    language: str | None
    stargazers_count: int
    open_issues_count: int


@dataclass
class RepoContents:
    """Cached view of files/directories at the repo root + key paths."""

    root_entries: list[str] = field(default_factory=list)
    readme_content: str = ""
    has_github_dir: bool = False
    workflow_files: list[str] = field(default_factory=list)
    issue_templates: list[str] = field(default_factory=list)
    pr_template: bool = False
    has_dependabot: bool = False
    has_codeowners: bool = False
    gitignore_content: str = ""
    tree_listing: list[str] = field(default_factory=list)


def _run_gh(*args: str, ignore_errors: bool = False) -> str:
    """Run a gh CLI command and return stdout."""
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "GitHub CLI (gh) not found. Install it from https://cli.github.com/ "
            "and run 'gh auth login' to authenticate."
        )
    if result.returncode != 0 and not ignore_errors:
        raise RuntimeError(
            f"gh {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def list_repos(
    user: str | None = None,
    limit: int = 200,
    include_forks: bool = False,
    include_archived: bool = False,
) -> list[RepoInfo]:
    """List repositories for a user (or the authenticated user)."""
    cmd = ["repo", "list"]
    if user:
        cmd.append(user)
    cmd += ["--source", "--limit", str(limit), "--json",
            "nameWithOwner,name,owner,description,defaultBranchRef,"
            "isFork,isArchived,isPrivate,hasIssuesEnabled,hasWikiEnabled,"
            "hasPages,licenseInfo,repositoryTopics,homepageUrl,primaryLanguage,"
            "stargazerCount,issues"]

    raw = _run_gh(*cmd)
    repos: list[RepoInfo] = []
    for item in json.loads(raw):
        is_fork = item.get("isFork", False)
        is_archived = item.get("isArchived", False)
        if not include_forks and is_fork:
            continue
        if not include_archived and is_archived:
            continue

        license_info = item.get("licenseInfo") or {}
        primary_lang = item.get("primaryLanguage") or {}
        owner_info = item.get("owner") or {}
        branch_ref = item.get("defaultBranchRef") or {}
        topics_raw = item.get("repositoryTopics") or []
        if isinstance(topics_raw, list) and topics_raw and isinstance(topics_raw[0], dict):
            topics = [t.get("name", "") for t in topics_raw]
        else:
            topics = list(topics_raw)

        # `issues` from `gh repo list --json issues` is a connection object: {totalCount: N}
        issues_raw = item.get("issues") or {}
        open_count = issues_raw.get("totalCount", 0) if isinstance(issues_raw, dict) else 0

        repos.append(RepoInfo(
            full_name=item.get("nameWithOwner", ""),
            name=item.get("name", ""),
            owner=owner_info.get("login", "") if isinstance(owner_info, dict) else str(owner_info),
            description=item.get("description") or "",
            default_branch=branch_ref.get("name", "main") if isinstance(branch_ref, dict) else "main",
            is_fork=is_fork,
            is_archived=is_archived,
            is_private=item.get("isPrivate", False),
            has_issues=item.get("hasIssuesEnabled", True),
            has_wiki=item.get("hasWikiEnabled", False),
            has_pages=item.get("hasPages", False),
            license_key=license_info.get("key") if isinstance(license_info, dict) else None,
            topics=topics,
            homepage=item.get("homepageUrl") or "",
            language=primary_lang.get("name") if isinstance(primary_lang, dict) else None,
            stargazers_count=item.get("stargazerCount", 0),
            open_issues_count=open_count,
        ))
    return repos


def fetch_repo_contents(repo: RepoInfo) -> RepoContents:
    """Fetch the file tree and key file contents for a repo via gh api."""
    contents = RepoContents()

    # Get the recursive tree (lightweight – just paths).
    # ?recursive=1 ensures nested paths (workflows, tests, etc.) are included.
    # Note: GitHub truncates very large trees; if .truncated is true some paths may be missing.
    try:
        tree_raw = _run_gh(
            "api", f"repos/{repo.full_name}/git/trees/{repo.default_branch}?recursive=1",
            "--jq", ".tree[].path",
            ignore_errors=True,
        )
        contents.tree_listing = tree_raw.splitlines() if tree_raw else []
    except Exception:
        contents.tree_listing = []

    # Fallback: also grab root listing for a simpler view
    try:
        root_raw = _run_gh(
            "api", f"repos/{repo.full_name}/contents/",
            "--jq", ".[].name",
            ignore_errors=True,
        )
        contents.root_entries = root_raw.splitlines() if root_raw else []
    except Exception:
        contents.root_entries = []

    # README
    contents.readme_content = _fetch_file(repo, "README.md")
    if not contents.readme_content:
        contents.readme_content = _fetch_file(repo, "readme.md")
    if not contents.readme_content:
        contents.readme_content = _fetch_file(repo, "README")

    # .github directory
    contents.has_github_dir = any(
        e.startswith(".github") for e in contents.tree_listing
    )

    # Workflows
    contents.workflow_files = [
        p for p in contents.tree_listing
        if p.startswith(".github/workflows/") and (p.endswith(".yml") or p.endswith(".yaml"))
    ]

    # Issue templates
    contents.issue_templates = [
        p for p in contents.tree_listing
        if p.startswith(".github/ISSUE_TEMPLATE") or p == ".github/issue_template.md"
    ]

    # PR template
    contents.pr_template = any(
        p.lower().startswith(".github/pull_request_template")
        or p.lower() == "pull_request_template.md"
        for p in contents.tree_listing
    )

    # Dependabot
    contents.has_dependabot = ".github/dependabot.yml" in contents.tree_listing or \
                              ".github/dependabot.yaml" in contents.tree_listing

    # CODEOWNERS
    contents.has_codeowners = any(
        p.endswith("CODEOWNERS") for p in contents.tree_listing
    )

    # .gitignore
    contents.gitignore_content = _fetch_file(repo, ".gitignore")

    return contents


def _fetch_file(repo: RepoInfo, path: str) -> str:
    """Download a single file's content from a repo."""
    try:
        raw = _run_gh(
            "api", f"repos/{repo.full_name}/contents/{path}",
            "--jq", ".content",
            ignore_errors=True,
        )
        if not raw:
            return ""
        import base64
        return base64.b64decode(raw).decode("utf-8", errors="replace")
    except Exception:
        return ""
