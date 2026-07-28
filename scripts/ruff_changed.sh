#!/usr/bin/env bash
#
# Run the Ruff lint and format gates over changed Python files only.
#
# This is a development convenience for the edit loop. It is NOT a replacement for the
# repository gates: `ruff check .` and `ruff format --check .` remain the acceptance
# gates, in the Makefile and in CI. A changed-file run cannot see a violation that an
# edit here introduced in a file that was not edited, so it never has the last word.
#
# Usage:
#   scripts/ruff_changed.sh              # changes vs HEAD, plus untracked files
#   scripts/ruff_changed.sh origin/main  # changes vs the merge base with a ref
#
# Paths containing spaces are handled: every git plumbing call is NUL-delimited and the
# file list is carried in a bash array, never in a word-split string.

set -euo pipefail

# Always operate from the repository root so relative paths and the Ruff configuration
# in pyproject.toml resolve identically to the full-repository gates.
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

base_ref="${1-}"

# Prefer the project virtual environment, which is what the Makefile gates use, but let
# an explicit RUFF override win so the script also works inside CI or a global install.
if [[ -n "${RUFF-}" ]]; then
	ruff_bin="$RUFF"
elif [[ -x "$repo_root/.venv/bin/ruff" ]]; then
	ruff_bin="$repo_root/.venv/bin/ruff"
else
	ruff_bin="ruff"
fi

collect() {
	if [[ -n "$base_ref" ]]; then
		# Three-dot: what this branch changed, ignoring what the base moved on to.
		git diff -z --name-only --diff-filter=ACMR "${base_ref}...HEAD" --
		# Uncommitted work on top of that.
		git diff -z --name-only --diff-filter=ACMR HEAD --
	else
		# Staged and unstaged changes against HEAD.
		git diff -z --name-only --diff-filter=ACMR HEAD --
	fi
	# Newly added files git does not track yet; --exclude-standard honours .gitignore,
	# so .venv, caches, and generated data never enter the list.
	git ls-files -z --others --exclude-standard
}

files=()
while IFS= read -r -d '' path; do
	# Only Python sources. Skip paths deleted since git listed them, which happens
	# when a rename or a checkout lands between the two plumbing calls above.
	[[ "$path" == *.py ]] || continue
	[[ -f "$path" ]] || continue
	files+=("$path")
done < <(collect | sort -zu)

if [[ ${#files[@]} -eq 0 ]]; then
	echo "ruff (changed files): no changed Python files; nothing to check."
	exit 0
fi

echo "ruff (changed files): ${#files[@]} file(s)"
printf '  %s\n' "${files[@]}"

# --force-exclude makes Ruff apply the pyproject exclusions to explicitly named paths,
# so a file under an excluded directory is treated exactly as the full-repository run
# treats it. Without it the two gates could disagree on the same file.
status=0
echo "--> ruff check"
"$ruff_bin" check --force-exclude -- "${files[@]}" || status=$?

echo "--> ruff format --check"
"$ruff_bin" format --check --force-exclude -- "${files[@]}" || status=$?

if [[ $status -ne 0 ]]; then
	echo "ruff (changed files): FAILED (exit ${status})" >&2
	exit "$status"
fi

echo "ruff (changed files): both gates passed."
