"""Genuine repository code identity for the governed major-phase restart (Decision 147).

**What this module is, in one sentence.** It derives, from the actual Git repository the running
``disclosure_drift`` source is imported from, the identity of the code that is executing -- its
``HEAD`` commit and its committed tree -- and refuses an execution whose working tree is
ambiguous.

**Why it exists.** Accepted **Decision 145** §12 claimed that its execution-identity digest
prevented, *mechanically*, "a process continuing from a revision whose governing semantics
moved". The independent review that Decision 145 itself required found that claim false and
recorded it as **D146-MAJOR-1**: the digest folded ten frozen constants plus
``disclosure_drift.__version__``, which is the literal ``"0.1.0"`` and has been touched by exactly
one commit in the entire history. The review proved it by mutation rather than by argument -- with
an accepted capacity floor relaxed ``60 -> 1`` GiB **and** an admission guard deleted outright, the
digest was bit-identical. The owner sustained the finding and chose the remedy: bind a genuine
code identity rather than narrow the claim. This module is that identity.

**Why it is a module of its own.** :mod:`~disclosure_drift.m3.canary_phases` owns the phase
contract and is deliberately pure -- its ``execution_identity`` is *given* its inputs rather
than reaching for them, and folding a subprocess and a filesystem walk into that module would put
two unrelated kinds of thing behind one import. This asks the host a
question about the *source it is running*, which is neither a phase contract nor a volume nor a
parse, so it is its own subsystem in the same way :mod:`~disclosure_drift.m3.canary_runtime` is.

**What it does not do.** It never checks out, stashes, resets, fetches, pulls, cleans, or repairs
anything. Every Git invocation here is a **read**: ``rev-parse``, ``ls-files``, ``status``. A
repository whose identity moved is a **refusal**, and a refusal is not a resumable pause -- control
returns to the operator, who decides what to do about it. Nothing here authorizes a canary, creates
a world, or mints an instrument.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "GOVERNING_SOURCE_FILENAMES",
    "REPOSITORY_IDENTITY_CONTRACT",
    "RepositoryIdentity",
    "RepositoryIdentityError",
    "repository_identity_at",
    "repository_root_containing",
    "require_clean_running_repository",
    "running_repository_identity",
]


class RepositoryIdentityError(DisclosureDriftError):
    """The executing repository could not be identified, or is not in a state that may execute."""


#: This mechanism's own contract identity, folded into the execution digest and written into every
#: checkpoint, so that a successor built from a different shape refuses rather than comparing two
#: identities that were derived under different rules.
REPOSITORY_IDENTITY_CONTRACT: Final = "m3.3-canary-repository-identity/1"

#: The source files whose tracked membership authenticates the repository this identity describes.
#:
#: **Why membership is checked at all.** ``git`` walks *upward* from whatever directory it is
#: pointed at, so pointing it at an installed copy of this package that happens to sit inside some
#: unrelated repository would yield that repository's identity -- a real identity, of the wrong
#: code. Requiring that the governing modules are **tracked files of the repository that was
#: found** closes that: the identity then provably describes a repository that contains the code
#: about to execute, rather than one that merely encloses it on disk.
#:
#: **Two responsibilities, kept apart.** Membership authenticates the *repository*; the clean-tree
#: contract in :func:`require_clean_running_repository` authenticates the *tree*. This module's own
#: file is deliberately absent from the list -- adding it would authenticate nothing further, since
#: an attacker able to place an unrelated repository can equally place a file inside it, while an
#: uncommitted copy of this module is already refused by the untracked rule.
#:
#: The names are resolved against **this module's own directory** rather than written out as
#: repository-relative paths, so the check cannot rot if the package is ever relocated.
GOVERNING_SOURCE_FILENAMES: Final[tuple[str, ...]] = (
    "canary_phases.py",
    "single_source_canary.py",
)

#: A Git object name, in either of the two hash algorithms a repository may be created with.
_OBJECT_NAME: Final = re.compile(r"\A(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")

#: Every Git call here is a local read of an already-existing repository. Thirty seconds is the
#: bound the neighbouring host queries already use.
_GIT_TIMEOUT_SECONDS: Final = 30

#: How many paths a refusal names before it stops enumerating and reports the count instead.
_NAMED_PATHS_IN_REFUSAL: Final = 10


@dataclass(frozen=True, slots=True)
class RepositoryIdentity:
    """What repository, at what revision, and in what working-tree state, is executing.

    ``head_sha`` is the **history** identity and ``tree_sha`` the **content** identity, and both
    are recorded because they answer different questions. Two commits can carry the same tree --
    an amend that changed only a message, a rebase that moved a parent -- so a tree comparison
    alone would admit a history that moved, and a commit comparison alone would refuse a
    continuation whose code is byte-identical without saying so.

    The two path tuples are the working-tree evidence, kept separate because they describe
    different ambiguities: a tracked file that has been modified means the running implementation
    may differ from ``tree_sha``, and an untracked, non-ignored file means the import graph may
    contain something no commit describes.
    """

    contract: str
    head_sha: str
    tree_sha: str
    dirty_tracked_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]

    @property
    def clean(self) -> bool:
        """Whether the working tree is unambiguous: no tracked change, no untracked file."""
        return not self.dirty_tracked_paths and not self.untracked_paths

    def as_record(self) -> Mapping[str, object]:
        """The identity as a plain mapping, carrying no absolute path."""
        return {
            "contract": self.contract,
            "head_sha": self.head_sha,
            "tree_sha": self.tree_sha,
            "clean": self.clean,
            "dirty_tracked_paths": list(self.dirty_tracked_paths),
            "untracked_paths": list(self.untracked_paths),
        }


def _git(root: Path, arguments: Sequence[str]) -> str:
    """One read-only Git query against ``root``, or a refusal.

    ``-C`` rather than a working directory, so the caller's process-wide state decides nothing;
    the executable is resolved to an absolute path, so ``PATH`` order decides nothing either.

    No path and no Git stderr is carried into the refusal, in keeping with the rest of this
    subsystem: a message that quoted stderr would print absolute paths on the one code path whose
    whole job is to describe the operator's own checkout.

    Raises:
        RepositoryIdentityError: Git is absent, or the query failed for any reason.
    """
    executable = shutil.which("git")
    if executable is None:
        message = (
            "git is not available on this host, so the identity of the repository this code is "
            "executing from cannot be derived. An identity that cannot be derived is refused, "
            "never assumed"
        )
        raise RepositoryIdentityError(message)
    try:
        completed = subprocess.run(  # noqa: S603 - absolute executable, fixed argv, no shell
            [executable, "-C", str(root), *arguments],
            capture_output=True,
            check=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        detail = f"exit {exc.returncode}" if isinstance(exc, subprocess.CalledProcessError) else ""
        message = (
            f"the repository this code is executing from could not be read: "
            f"git {arguments[0]!r} failed ({type(exc).__name__}{f'; {detail}' if detail else ''}). "
            "A repository identity that cannot be derived is refused, never assumed"
        )
        raise RepositoryIdentityError(message) from exc
    return completed.stdout.decode("utf-8", errors="replace")


def _object_name(value: str, *, field: str) -> str:
    """One Git object name, refusing anything that is not one."""
    name = value.strip()
    if not _OBJECT_NAME.fullmatch(name):
        message = (
            f"the repository {field} did not read back as a Git object name; an identity that "
            "cannot be read is refused rather than folded into an execution digest"
        )
        raise RepositoryIdentityError(message)
    return name


def repository_root_containing(path: Path) -> Path:
    """The top level of the Git repository containing ``path``.

    Derived by asking Git from ``path`` itself rather than from the current working directory,
    which this module never reads: a canary phase is launched from wherever the operator happens
    to be standing, and that is not evidence about which code is running.

    Raises:
        RepositoryIdentityError: ``path`` is not inside a Git repository, or Git could not answer.
    """
    start = path if path.is_dir() else path.parent
    toplevel = _git(start, ["rev-parse", "--show-toplevel"]).strip()
    if not toplevel:
        message = (
            "the source this process is running is not inside a Git repository, so no repository "
            "identity exists for it. Execution is refused rather than admitted without one"
        )
        raise RepositoryIdentityError(message)
    return Path(toplevel).resolve()


def repository_identity_at(root: Path) -> RepositoryIdentity:
    """The identity of the repository rooted at ``root``, exactly as Git reports it.

    Four reads, and no write of any kind:

    * ``rev-parse HEAD`` -- the commit this repository is checked out at;
    * ``rev-parse HEAD^{tree}`` -- the content that commit names;
    * ``status --porcelain --untracked-files=no`` -- every tracked path that differs from the
      index or the commit, which is exactly the set that could make the running implementation
      differ from ``tree_sha``;
    * ``ls-files --others --exclude-standard`` -- every untracked path the repository has **not**
      declared ignorable.

    **The untracked rule, stated rather than assumed.** Ignored paths are not evidence of
    ambiguity: ``__pycache__``, a virtual environment and a build directory exist in every working
    checkout the moment the package is imported, and the repository's own tracked ``.gitignore``
    is what declares them irrelevant. An untracked path that is **not** ignored is different in
    kind -- it is a file the repository has never described, it can sit anywhere on the import
    path, and it can therefore change what executes. It is counted as ambiguity and refused.

    Raises:
        RepositoryIdentityError: ``root`` is not a repository top level, or a read failed.
    """
    resolved = root.resolve()
    toplevel = repository_root_containing(resolved)
    if toplevel != resolved:
        message = (
            "a repository identity is derived from a repository top level and never from a "
            "subdirectory of one; the path given is not the top level Git reports"
        )
        raise RepositoryIdentityError(message)
    head = _object_name(_git(resolved, ["rev-parse", "HEAD"]), field="HEAD commit")
    tree = _object_name(_git(resolved, ["rev-parse", "HEAD^{tree}"]), field="HEAD tree")
    dirty = _porcelain_paths(_git(resolved, ["status", "--porcelain=v1", "--untracked-files=no"]))
    untracked = tuple(
        line.strip()
        for line in _git(resolved, ["ls-files", "--others", "--exclude-standard"]).splitlines()
        if line.strip()
    )
    return RepositoryIdentity(
        contract=REPOSITORY_IDENTITY_CONTRACT,
        head_sha=head,
        tree_sha=tree,
        dirty_tracked_paths=dirty,
        untracked_paths=untracked,
    )


def _porcelain_paths(output: str) -> tuple[str, ...]:
    """The path of every tracked entry ``git status --porcelain=v1`` reported.

    Version 1 porcelain is a stable, documented format: two status characters, a space, then the
    path -- and for a rename, ``old -> new``. The **new** path is the one recorded, because it is
    the one that is now on disk.
    """
    paths: list[str] = []
    for line in output.splitlines():
        entry = line[3:].strip() if len(line) > 3 else line.strip()
        if not entry:
            continue
        _, arrow, renamed = entry.partition(" -> ")
        paths.append(renamed.strip() if arrow else entry)
    return tuple(paths)


def running_repository_identity() -> RepositoryIdentity:
    """The identity of the repository **this process's own source** was imported from.

    Derived from this module's own location rather than accepted as an argument -- the rule
    :func:`~disclosure_drift.m3.single_source_canary._package_repository_root` already uses -- so
    that no caller, operator, environment variable or command-line flag can declare a decoy
    revision and have a continuation admitted under it. An operator-supplied SHA would make the
    mechanism a statement of intent; this makes it a measurement.

    The repository Git reports is then **authenticated**: the governing source files must be
    tracked in it. See :data:`GOVERNING_SOURCE_FILENAMES` for why.

    Raises:
        RepositoryIdentityError: the source is not inside a Git repository, that repository does
            not track the governing source files, or a read failed.
    """
    here = Path(__file__).resolve()
    root = repository_root_containing(here)
    _require_tracked_governing_source(root, here.parent)
    return repository_identity_at(root)


def _require_tracked_governing_source(root: Path, package_directory: Path) -> None:
    """Refuse a repository that does not track the modules about to execute.

    Raises:
        RepositoryIdentityError: a governing module is not a tracked file of ``root``.
    """
    try:
        relative = [
            (package_directory / name).relative_to(root).as_posix()
            for name in GOVERNING_SOURCE_FILENAMES
        ]
    except ValueError as exc:
        message = (
            "the source this process is running does not lie inside the Git repository that "
            "encloses it, so no repository identity describes it. Execution is refused"
        )
        raise RepositoryIdentityError(message) from exc
    try:
        _git(root, ["ls-files", "--error-unmatch", "--", *relative])
    except RepositoryIdentityError as exc:
        message = (
            "the Git repository enclosing this source does not track the modules that govern a "
            f"canary phase ({', '.join(relative)}). A repository that merely CONTAINS the running "
            "code on disk is not the repository whose revision governs it, and an identity taken "
            "from one would be a real identity of the wrong code. Execution is refused"
        )
        raise RepositoryIdentityError(message) from exc


def require_clean_running_repository() -> RepositoryIdentity:
    """The running repository's identity, or a refusal if its working tree is ambiguous.

    **The fail-closed half of Decision 147.** A phase records the committed tree it executed
    under so that its successor can prove it is continuing the *same* implementation. That proof
    is worth nothing if the recorded tree does not describe what actually ran, so an execution
    whose working tree carries uncommitted tracked changes -- or untracked, non-ignored files that
    could join the import graph -- is refused **before** any identity is folded into a digest.

    **A refusal here is not a resumable pause.** Nothing is checked out, stashed, reset, fetched,
    cleaned or repaired, and no continuation is offered: control returns to the operator with the
    exact ambiguity named.

    Raises:
        RepositoryIdentityError: the working tree is not clean, or the identity could not be
            derived.
    """
    identity = running_repository_identity()
    if identity.clean:
        return identity
    message = (
        "the repository this canary code is executing from does not have a clean tracked "
        f"working tree, so the committed tree {identity.tree_sha} does not describe what would "
        "actually run. A phase records its repository identity so that its successor can prove "
        "it is continuing the SAME implementation, and that proof is only worth what the "
        "recording is worth. Execution is refused; nothing was checked out, stashed, reset, "
        "cleaned or repaired, and this refusal is NOT a resumable pause. "
        f"{_describe('modified tracked', identity.dirty_tracked_paths)}; "
        f"{_describe('untracked, non-ignored', identity.untracked_paths)}"
    )
    raise RepositoryIdentityError(message)


def _describe(label: str, paths: tuple[str, ...]) -> str:
    """One bounded, repository-relative enumeration for a refusal message."""
    if not paths:
        return f"{label}: none"
    named = ", ".join(paths[:_NAMED_PATHS_IN_REFUSAL])
    if len(paths) > _NAMED_PATHS_IN_REFUSAL:
        return f"{label} ({len(paths)}): {named}, ..."
    return f"{label} ({len(paths)}): {named}"
