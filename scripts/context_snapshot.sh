#!/usr/bin/env bash
# Read-only repository context snapshot for Disclosure Drift.
#
# Prints the volatile facts that documentation must never hardcode: baseline
# commit, tree, parent, branch, divergence from the recorded remote ref,
# checkpoint tags, migration head, decision head, the tracked network switches,
# the active stage contract, and the next authorized action. Documentation
# states policy; this script states current state.
#
# It reports state and is not an authority. It carries no frozen contract hash,
# packet digest, receipt version, or input manifest — accepted decisions, the
# accepted contract, and Milestones/STATUS.md carry those.
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

# Read a "KEY: value" marker out of a Markdown ledger, returning the whole
# value. Returns the empty string when the file or the key is absent, which the
# callers below render as an explicit "not found" rather than as a blank value.
#
# A marker value may legitimately continue onto indented lines — the accepted
# stage contracts wrap theirs that way — so the continuation is joined with
# single spaces. The loop deliberately stops at the *first* line that is not a
# continuation, so a marker never absorbs the paragraph, fence, or marker that
# follows it. A continuation line must be indented and non-blank, must not be a
# fence, and must not itself be a `KEY:` marker; anything else ends the value.
# Single-line markers therefore behave exactly as they did before.
marker() {
	local file="$1"
	local key="$2"
	if [ ! -f "$file" ]; then
		printf ''
		return 0
	fi
	awk -v key="$key" '
		found == 0 {
			if ($0 ~ "^[ \t]*" key ":") {
				value = $0
				sub("^[ \t]*" key ":[ \t]*", "", value)
				sub(/[ \t]+$/, "", value)
				found = 1
			}
			next
		}
		{
			if ($0 !~ /^[ \t]+[^ \t]/) exit
			if ($0 ~ /^[ \t]*```/) exit
			if ($0 ~ /^[ \t]*[A-Z][A-Z0-9_]*:/) exit
			line = $0
			sub(/^[ \t]+/, "", line)
			sub(/[ \t]+$/, "", line)
			if (line != "") {
				value = (value == "") ? line : value " " line
			}
		}
		END { if (found) printf "%s", value }
	' "$file"
}

# Read `key: value` from inside one named top-level block of the tracked YAML
# configuration. This reports what the tracked file says; it neither loads nor
# validates configuration — `make validate` does that.
yaml_block_value() {
	local file="$1"
	local block="$2"
	local key="$3"
	if [ ! -f "$file" ]; then
		printf ''
		return 0
	fi
	awk -v block="$block" -v key="$key" '
		$0 ~ "^" block ":[ \t]*$" { inblock = 1; next }
		inblock && /^[^ \t#]/ { exit }
		inblock && $0 ~ "^[ \t]+" key ":" {
			line = $0
			sub("^[ \t]+" key ":[ \t]*", "", line)
			sub(/[ \t]*#.*$/, "", line)
			sub(/[ \t]+$/, "", line)
			printf "%s", line
			exit
		}
	' "$file"
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
CONFIG_FILE="$ROOT/configs/project.yaml"

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
HEAD_TREE="$(git_ro rev-parse --verify --quiet 'HEAD^{tree}' 2>/dev/null || printf '')"

# All parents, not `HEAD^`, so a merge reports both and a root commit reports
# none instead of failing.
HEAD_PARENTS="$(git_ro rev-list --parents -n 1 HEAD 2>/dev/null |
	awk '{ for (i = 2; i <= NF; i++) printf "%s%s", (i > 2 ? " " : ""), $i }' || printf '')"

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
field 'HEAD tree' "${HEAD_TREE:-unknown}"
field 'HEAD parent(s)' "${HEAD_PARENTS:-(none — root commit)}"

if [ -n "$ORIGIN_MAIN" ]; then
	field 'origin/main' "$ORIGIN_MAIN"
	if [ "$ORIGIN_MAIN" = "$HEAD_FULL" ]; then
		field 'HEAD == origin/main' 'yes'
	else
		field 'HEAD == origin/main' 'no — local branch and recorded remote ref differ'
	fi
	# left = commits reachable from origin/main only (behind); right = commits
	# reachable from HEAD only (ahead). Purely local: no remote is contacted, so
	# this is divergence from the *recorded* ref, not from the live remote.
	DIVERGENCE="$(git_ro rev-list --left-right --count refs/remotes/origin/main...HEAD 2>/dev/null || printf '')"
	if [ -n "$DIVERGENCE" ]; then
		field 'ahead / behind' "$(printf '%s' "$DIVERGENCE" | awk '{ printf "ahead %s, behind %s", $2, $1 }')"
	else
		field 'ahead / behind' 'unknown — could not compare with the recorded remote ref'
	fi
else
	field 'origin/main' 'unavailable locally — no refs/remotes/origin/main reference'
	field 'HEAD == origin/main' 'unknown — cannot compare without that reference; this script performs no remote lookup'
	field 'ahead / behind' 'unknown — no recorded remote ref to compare against'
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

section 'Network switches (tracked configs/project.yaml)'
NETWORK_ENABLED="$(yaml_block_value "$CONFIG_FILE" 'network' 'enabled')"
NETWORK_M3_ACQUIRE="$(yaml_block_value "$CONFIG_FILE" 'network' 'm3_acquire_enabled')"
field 'network.enabled' "${NETWORK_ENABLED:-(key not found)}"
field 'network.m3_acquire_enabled' "${NETWORK_M3_ACQUIRE:-(key not found)}"
printf 'Tracked values only. Each is independent, and neither is authorization:\n'
printf 'live operation additionally requires its own accepted owner authorization.\n'

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
field 'Stage boundary' 'make stage-gate'
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
