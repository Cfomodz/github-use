# repo-scanner

Scan your GitHub repositories for structural and community-health improvements that you might not be aware of yet.

This tool combines **programmatic checks** with **AI-driven analysis** (via DeepSeek) to surface repo-level issues — not code bugs, but the kind of foundational gaps that make a repository harder to use, contribute to, or maintain:

- Missing or inadequate README
- No license file
- No CI/CD workflows
- No test suite
- Missing community health files (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY)
- No Dependabot config
- Missing repo metadata (description, topics, .gitignore)
- And more, including AI-detected issues tailored to your specific repo

## Requirements

- Python 3.10+
- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated
- DeepSeek API key (optional — skip AI with `--no-ai`)

## Installation

```bash
git clone https://github.com/Cfomodz/github-use.git
cd github-use
pip install -e .
```

## Usage

### Scan all your repos

```bash
repo-scanner
```

### Scan a specific user's repos

```bash
repo-scanner some-username
```

### Scan specific repositories

```bash
repo-scanner -r owner/repo-one -r owner/repo-two
```

### Skip AI analysis (no API key needed)

```bash
repo-scanner --no-ai
```

### Save a Markdown report

```bash
repo-scanner -o report.md
```

### Show only warnings and critical findings

```bash
repo-scanner --severity warning
```

### Include forks and archived repos

```bash
repo-scanner --include-forks --include-archived
```

### Run as a module

```bash
python -m repo_scanner --help
```

## Configuration

| Environment Variable | Description |
|---|---|
| `DEEPSEEK_API_KEY` | API key for DeepSeek AI analysis. Get one at https://platform.deepseek.com/ |

The `gh` CLI must be authenticated (`gh auth login`).

## Checks

| Check | What it detects | Severity |
|---|---|---|
| **readme** | Missing README, too short, no logo, no badges, no install/usage sections, no code blocks | Critical / Warning / Info |
| **license** | No LICENSE file, non-standard license | Critical / Info |
| **workflows** | No GitHub Actions, no CI workflow | Critical / Warning |
| **tests** | No test directory or test files | Critical |
| **community** | Missing CONTRIBUTING, CODE_OF_CONDUCT, issue templates, PR template | Warning / Info |
| **security** | No SECURITY.md, no Dependabot config | Warning |
| **metadata** | No description, no topics, no homepage, no .gitignore, no CODEOWNERS | Warning / Info |
| **ai** | Additional context-aware findings from DeepSeek | Varies |

## GitHub Actions

A workflow is included at `.github/workflows/scan.yml` that runs the scanner weekly. To use it:

1. Add a `GH_PAT` secret (personal access token with `repo` scope)
2. Add a `DEEPSEEK_API_KEY` secret (or set `no_ai: true` in the dispatch inputs)
3. The report is uploaded as a workflow artifact

You can also trigger it manually from the Actions tab.

## Example output

```
======================================================================
octocat/hello-world
  My first repository on GitHub!
  Language: unknown | Stars: 2365 | License: none
======================================================================
  [X] No license [license]
      The repository has no LICENSE file and GitHub does not detect a license.
      -> Add a LICENSE file. Without one, the code is under exclusive copyright...
  [!] No GitHub Actions workflows [workflows]
      The .github/workflows/ directory is missing or empty.
      -> Add at least a basic CI workflow that runs on push/PR.
  [i] No project logo or screenshot in README [readme]
      The README contains no images besides badges.
      -> Add a project logo or screenshot near the top of the README...
```
