"""DeepSeek API integration for AI-driven repository analysis."""

from __future__ import annotations

import json
import os

import httpx

from repo_scanner.checks import Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo

_DEEPSEEK_BASE = "https://api.deepseek.com"
_MODEL = "deepseek-chat"
_TIMEOUT = 120  # seconds


def _get_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "DEEPSEEK_API_KEY environment variable is not set. "
            "Get an API key at https://platform.deepseek.com/"
        )
    return key


def _build_prompt(repo: RepoInfo, contents: RepoContents, programmatic_findings: list[Finding]) -> str:
    """Build the analysis prompt with repo context."""
    finding_summary = "\n".join(
        f"  - [{f.severity.value.upper()}] {f.title}: {f.detail}"
        for f in programmatic_findings
    ) or "  (none)"

    tree_sample = "\n".join(contents.tree_listing[:150])
    readme_snippet = contents.readme_content[:2000] if contents.readme_content else "(no README)"

    return f"""You are a senior open-source maintainer reviewing a GitHub repository for
structural, community-health, and best-practice improvements. Focus ONLY on
repository-level concerns — NOT code quality or bugs inside source files.

## Repository
- Name: {repo.full_name}
- Language: {repo.language or "unknown"}
- Description: {repo.description or "(none)"}
- Stars: {repo.stargazers_count}
- License: {repo.license_key or "none detected"}
- Topics: {', '.join(repo.topics) if repo.topics else "(none)"}
- Homepage: {repo.homepage or "(none)"}
- Is fork: {repo.is_fork}
- Is private: {repo.is_private}

## File tree (first 150 entries)
{tree_sample}

## README (first 2000 chars)
{readme_snippet}

## Already-detected issues (from programmatic checks)
{finding_summary}

---

Based on the above, identify **additional** repository-level improvements that the
programmatic checks MISSED. Think about things like:
- Project organization or directory structure anti-patterns
- Missing or misplaced config files for the detected language/framework
- Documentation gaps (changelogs, API docs, architecture docs)
- Release management (no tags, no GitHub Releases)
- Branch protection or repo settings suggestions
- Packaging / distribution issues (missing setup.cfg, package.json, Cargo.toml, etc.)
- Accessibility or internationalization considerations for docs
- Anything else a seasoned maintainer would notice

Return your findings as a JSON array of objects, each with:
  "title": short title,
  "detail": 1-2 sentence explanation,
  "suggestion": actionable recommendation,
  "severity": one of "critical", "warning", "info"

Return ONLY the JSON array, no markdown fences, no commentary. If you have no
additional findings beyond what was already detected, return an empty array: []"""


def analyze(
    repo: RepoInfo,
    contents: RepoContents,
    programmatic_findings: list[Finding],
) -> list[Finding]:
    """Send repo context to DeepSeek and parse AI-generated findings."""
    api_key = _get_api_key()
    prompt = _build_prompt(repo, contents, programmatic_findings)

    payload = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": "You are a GitHub repository health auditor. Respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(
            f"{_DEEPSEEK_BASE}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if the model added them despite instructions
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[: content.rfind("```")]
    content = content.strip()

    try:
        items = json.loads(content)
    except json.JSONDecodeError:
        return [Finding(
            check_name="ai",
            severity=Severity.INFO,
            title="AI analysis returned unparseable response",
            detail=f"Raw response (truncated): {content[:300]}",
            suggestion="Re-run with --no-ai to skip AI analysis, or check DeepSeek API status.",
        )]

    findings: list[Finding] = []
    for item in items:
        sev_str = item.get("severity", "info").lower()
        try:
            sev = Severity(sev_str)
        except ValueError:
            sev = Severity.INFO
        findings.append(Finding(
            check_name="ai",
            severity=sev,
            title=item.get("title", "AI finding"),
            detail=item.get("detail", ""),
            suggestion=item.get("suggestion", ""),
        ))

    return findings
