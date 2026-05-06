"""Checks for presence of a test suite."""

from __future__ import annotations

import re

from repo_scanner.checks import Check, Finding, Severity
from repo_scanner.github import RepoContents, RepoInfo

_TEST_INDICATORS = re.compile(
    r"(^tests?/|^__tests__/|^spec/|^test_|_test\.|\.test\.|\.spec\.|"
    r"pytest|jest|mocha|vitest|unittest|rspec|phpunit|go\.test|cargo\.test)",
    re.IGNORECASE,
)


class TestsCheck:
    name = "tests"

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]:
        findings: list[Finding] = []

        has_tests = any(_TEST_INDICATORS.search(p) for p in contents.tree_listing)

        if not has_tests:
            findings.append(Finding(
                check_name=self.name,
                severity=Severity.CRITICAL,
                title="No test suite detected",
                detail=(
                    "No test directory (tests/, __tests__/, spec/) or test files "
                    "(*_test.*, *.test.*, *.spec.*) were found in the repository."
                ),
                suggestion="Add automated tests. Even a minimal smoke test greatly improves reliability.",
            ))

        return findings


check = TestsCheck()
