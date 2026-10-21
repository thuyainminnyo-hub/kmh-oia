"""Trusted source-revision discovery from the actual Git checkout.

This helper reads Git's HEAD; it does not trust a revision string supplied by a
request caller. It is intended to run in the same checkout/process context as
the controlled pilot. Production should also ensure that the checkout is clean
and that the expected revision is the reviewed build artifact.
"""
from dataclasses import dataclass
import re
import subprocess
from pathlib import Path


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class SourceRevisionCheck:
    actual_revision: str | None
    expected_revision: str | None
    matches: bool
    working_tree_clean: bool
    reason: str


def _git(root: str | Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(Path(root).resolve()), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout.strip()


def discover_git_revision(root: str | Path = ".") -> str:
    """Return the actual full commit SHA from Git HEAD; fail closed otherwise."""
    try:
        revision = _git(root, "rev-parse", "--verify", "HEAD")
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("unable to discover source revision from git checkout") from exc
    if not _SHA_RE.fullmatch(revision):
        raise RuntimeError("git HEAD did not return a full commit SHA")
    return revision


def verify_source_revision(
    expected_revision: str | None,
    root: str | Path = ".",
) -> SourceRevisionCheck:
    """Compare expected SHA to actual HEAD and report tracked/untracked dirtiness."""
    try:
        actual = discover_git_revision(root)
        status = _git(root, "status", "--porcelain", "--untracked-files=normal")
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        return SourceRevisionCheck(
            actual_revision=None,
            expected_revision=expected_revision,
            matches=False,
            working_tree_clean=False,
            reason=str(exc),
        )
    clean = not bool(status)
    valid_expected = isinstance(expected_revision, str) and bool(_SHA_RE.fullmatch(expected_revision))
    matches = valid_expected and expected_revision == actual
    if not valid_expected:
        reason = "expected revision must be a full 40-character lowercase Git SHA"
    elif not matches:
        reason = "expected revision does not match actual Git HEAD"
    elif not clean:
        reason = "working tree contains modified or untracked files"
    else:
        reason = "source revision matches actual Git HEAD and working tree is clean"
    return SourceRevisionCheck(
        actual_revision=actual,
        expected_revision=expected_revision,
        matches=bool(matches),
        working_tree_clean=clean,
        reason=reason,
    )


def require_verified_source_revision(expected_revision: str, root: str | Path = ".") -> str:
    """Return actual revision only when expected SHA matches a clean checkout."""
    check = verify_source_revision(expected_revision, root)
    if not check.matches or not check.working_tree_clean or not check.actual_revision:
        raise RuntimeError(f"source revision verification failed: {check.reason}")
    return check.actual_revision
