#!/usr/bin/env bash
# Read-only repository context snapshot for Disclosure Drift.
#
# Prints the volatile facts that documentation must never hardcode: baseline
# commit, branch, checkpoint tags, migration head, decision head, the active
# stage contract, and the next authorized action. Documentation states policy;
# this script states current state.
#
# Guarantees relied upon by CLAUDE.md and Milestones/STATUS.md:
#   * no remote access of any kind — remote-tracking refs are read exactly as
#     they already exist on disk and are never updated;
#   * no writes — output goes to stdout only; no file, cache, index, ref, or
#     lock is created or modified (git runs with --no-optional-locks);
#   * no pytest, no SQLite, no project data is opened.
#
# Safe to run from any directory inside the working tree, including one whose
# path contains spaces.

set -euo pipefail

if ! ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
	printf 'context_snapshot: not inside a Git working tree\n' >&2
	exit 1
fi

# Every git call is rooted at the working tree, so invocation from a nested
# directory behaves identically, and takes no optional lock, so a snapshot never
# refreshes the index on disk.
git_ro() {
	git --no-optional-locks -C "$ROOT" "$@"
}

section() {
	printf '\n== %s ==\n' "$1"
}

field() {
	printf '%-24s %s\n' "$1" "$2"
}

# Print stdin as an indented list, or "(none)" when stdin is empty.
print_list() {
	local line
	local seen=0
	while IFS= read -r line; do
		[ -n "$line" ] || continue
		printf '  %s\n' "$line"
		seen=1
	done
	if [ "$seen" -eq 0 ]; then
		printf '  (none)\n'
	fi
}

# Read a "KEY: value" marker line out of a Markdown ledger. Returns the empty
# string when the file or the key is absent.
marker() {
	local file="$1"
	local key="$2"
	if [ ! -f "$file" ]; then
		printf ''
		return 0
	fi
	grep -m1 -E "^[[:space:]]*${key}:" "$file" 2>/dev/null |
		sed -E "s/^[[:space:]]*${key}:[[:space:]]*//" || true
}

# Newest entry matching a glob in a directory, by name order.
newest_named() {
	local dir="$1"
	local pattern="$2"
	local entry
	local newest=""
	if [ ! -d "$dir" ]; then
		printf ''
		return 0
	fi
	while IFS= read -r entry; do
		[ -n "$entry" ] || continue
		newest="$entry"
	done < <(find "$dir" -maxdepth 1 -type f -name "$pattern" -exec basename {} \; | LC_ALL=C sort)
	printf '%s' "$newest"
}

count_named() {
	local dir="$1"
	local pattern="$2"
	local entry
	local total=0
	if [ ! -d "$dir" ]; then
		printf '0'
		return 0
	fi
	while IFS= read -r entry; do
		[ -n "$entry" ] || continue
		total=$((total + 1))
	done < <(find "$dir" -maxdepth 1 -type f -name "$pattern")
	printf '%s' "$total"
}

STATUS_FILE="$ROOT/Milestones/STATUS.md"
MIGRATIONS_DIR="$ROOT/src/disclosure_drift/storage/migrations"
DECISIONS_DIR="$ROOT/Docs/Decisions"

printf '=== Disclosure Drift context snapshot (read-only; no remote access) ===\n'

section 'Repository'
field 'Repository root' "$ROOT"

# `symbolic-ref` resolves to a branch name only when HEAD is attached; on a
# detached HEAD it fails, which is the detection. `rev-parse --abbrev-ref HEAD`
# is deliberately not used here: it prints the literal string 'HEAD' when
# detached, which reads like an ordinary branch named HEAD.
if BRANCH="$(git_ro symbolic-ref --quiet --short HEAD 2>/dev/null)"; then
	:
elif git_ro rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
	BRANCH='DETACHED_HEAD'
else
	BRANCH='unknown'
fi

HEAD_SHORT="$(git_ro rev-parse --short HEAD 2>/dev/null || printf 'unknown')"
HEAD_FULL="$(git_ro rev-parse HEAD 2>/dev/null || printf 'unknown')"

# `--verify --quiet` against the full ref path is required. A bare
# `rev-parse origin/main` echoes its own argument to stdout when the ref does
# not exist, so a `|| printf ''` fallback never fires and the literal text
# 'origin/main' would be captured as though it were a SHA — reported as a false
# divergence. This form prints nothing and exits non-zero when the local
# remote-tracking ref is absent. No remote is contacted either way.
ORIGIN_MAIN="$(git_ro rev-parse --verify --quiet refs/remotes/origin/main 2>/dev/null || printf '')"

field 'Branch' "$BRANCH"
field 'HEAD (short)' "$HEAD_SHORT"
field 'HEAD (full)' "$HEAD_FULL"

if [ -n "$ORIGIN_MAIN" ]; then
	field 'origin/main' "$ORIGIN_MAIN"
	if [ "$ORIGIN_MAIN" = "$HEAD_FULL" ]; then
		field 'HEAD == origin/main' 'yes'
	else
		field 'HEAD == origin/main' 'no — local branch and recorded remote ref differ'
	fi
else
	field 'origin/main' 'unavailable locally — no refs/remotes/origin/main reference'
	field 'HEAD == origin/main' 'unknown — cannot compare without that reference; this script performs no remote lookup'
fi

section 'Working tree'
WORKTREE_STATUS="$(git_ro status --porcelain 2>/dev/null || printf '')"
if [ -z "$WORKTREE_STATUS" ]; then
	field 'State' 'clean'
else
	field 'State' 'dirty — see paths below'
fi

printf '\nStaged paths:\n'
git_ro diff --cached --name-only | print_list

printf '\nUnstaged paths:\n'
git_ro diff --name-only | print_list

printf '\nUntracked paths:\n'
git_ro ls-files --others --exclude-standard | print_list

section 'Checkpoints'
printf 'Tags at HEAD:\n'
git_ro tag --points-at HEAD | print_list

printf '\nM2.3 checkpoint tags:\n'
while IFS= read -r tag; do
	[ -n "$tag" ] || continue
	tag_sha="$(git_ro rev-parse --short "$tag^{commit}" 2>/dev/null || printf 'unknown')"
	printf '%s -> %s\n' "$tag" "$tag_sha"
done < <(git_ro tag --list 'm2.3*' | LC_ALL=C sort) | print_list

section 'Schema and decisions'
LATEST_MIGRATION="$(newest_named "$MIGRATIONS_DIR" '[0-9][0-9][0-9][0-9]_*.sql')"
MIGRATION_COUNT="$(count_named "$MIGRATIONS_DIR" '[0-9][0-9][0-9][0-9]_*.sql')"
LATEST_DECISION="$(newest_named "$DECISIONS_DIR" 'decision_[0-9][0-9][0-9]_*.md')"

field 'Latest migration' "${LATEST_MIGRATION:-(none found)}"
field 'Migration count' "$MIGRATION_COUNT"
field 'Latest decision record' "${LATEST_DECISION:-(none found)}"

section 'Stage state (from Milestones/STATUS.md)'
if [ -f "$STATUS_FILE" ]; then
	CURRENT_STAGE="$(marker "$STATUS_FILE" 'CURRENT_STAGE')"
	ACTIVE_BLOCKER="$(marker "$STATUS_FILE" 'ACTIVE_BLOCKER')"
	NEXT_ACTION="$(marker "$STATUS_FILE" 'NEXT_AUTHORIZED_ACTION')"
	CONTRACT_REL="$(marker "$STATUS_FILE" 'ACTIVE_STAGE_CONTRACT')"
	field 'Current stage' "${CURRENT_STAGE:-(marker CURRENT_STAGE not found)}"
	field 'Active blocker' "${ACTIVE_BLOCKER:-(marker ACTIVE_BLOCKER not found)}"
else
	CURRENT_STAGE=''
	ACTIVE_BLOCKER=''
	NEXT_ACTION=''
	CONTRACT_REL=''
	field 'Status ledger' 'Milestones/STATUS.md not found'
fi

section 'Active stage contract'
if [ -n "${CONTRACT_REL:-}" ] && [ -f "$ROOT/$CONTRACT_REL" ]; then
	CONTRACT_STATUS="$(marker "$ROOT/$CONTRACT_REL" 'STATUS')"
	field 'Contract path' "$CONTRACT_REL"
	field 'Contract status' "${CONTRACT_STATUS:-(marker STATUS not found)}"
elif [ -n "${CONTRACT_REL:-}" ]; then
	field 'Contract path' "$CONTRACT_REL (file not found)"
	field 'Contract status' 'unknown'
else
	field 'Contract path' '(marker ACTIVE_STAGE_CONTRACT not found)'
	field 'Contract status' 'unknown'
fi

section 'Validation commands'
field 'Fast loop' 'make fast'
field 'Full acceptance gate' 'make check'
field 'This snapshot' 'make context'
printf '\nNeither loop is selected by this script. Choose the test set with\n'
printf 'Docs/change_impact_map.md, then run it via: make test PYTEST_ARGS="<paths>"\n'

section 'Next authorized action'
if [ -n "${NEXT_ACTION:-}" ]; then
	printf '%s\n' "$NEXT_ACTION"
else
	printf '(marker NEXT_AUTHORIZED_ACTION not found in Milestones/STATUS.md)\n'
fi

printf '\n=== end of snapshot ===\n'
