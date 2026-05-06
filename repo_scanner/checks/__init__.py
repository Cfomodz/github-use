"""Built-in repo health checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from repo_scanner.github import RepoContents, RepoInfo


class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Finding:
    """A single improvement finding."""

    check_name: str
    severity: Severity
    title: str
    detail: str
    suggestion: str


class Check(Protocol):
    """Interface every check module must satisfy."""

    name: str

    def run(self, repo: RepoInfo, contents: RepoContents) -> list[Finding]: ...
