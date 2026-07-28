# Audit: Cfomodz/github-use

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Home of `repo-scanner`, a CLI that scans GitHub repos for structural/community-health
gaps (README, license, CI, tests, etc.) using `gh` + optional DeepSeek AI analysis.
Also now hosts this audit log.

## Findings

### 1. `--include-forks` flag is broken — warning

`repo_scanner/github.py:80` always passes `--source` to `gh repo list`, which
excludes forks server-side. The `include_forks` parameter only controls a
client-side filter that never sees any forks, so `repo-scanner --include-forks`
silently behaves the same as without the flag. Fix: only append `--source` when
`include_forks` is False.

### 2. The scanner fails its own critical checks — warning

The repo has **no LICENSE file** and **no tests**, both of which `repo-scanner`
itself reports as *critical* findings on other repos. There is also no CI that
runs lint/tests on push/PR (the only workflow is the weekly scan). Eating your
own dog food would make the tool more credible.

### 3. Scheduled scans cannot skip AI — info

`.github/workflows/scan.yml` only reads the `no_ai` input from
`workflow_dispatch`; on the weekly `schedule` trigger inputs are empty, so AI is
always attempted. If the `DEEPSEEK_API_KEY` secret is absent every repo entry
carries an error string in the report. Consider defaulting to `--no-ai` when the
secret is empty.

### 4. Dependency list duplicated — info

`requirements.txt` duplicates the single dependency already declared in
`pyproject.toml` (`httpx>=0.27,<1`). Two sources of truth will drift; drop
`requirements.txt` or generate it.

## TODOs

- [ ] Fix `--include-forks` by making `--source` conditional in `list_repos()`
- [ ] Add a LICENSE file
- [ ] Add a minimal pytest suite for the pure-function checks + a CI workflow (lint + tests)
- [ ] Make scheduled scan runs fall back to `--no-ai` when `DEEPSEEK_API_KEY` is unset
- [ ] Remove `requirements.txt` (or auto-generate it from `pyproject.toml`)
