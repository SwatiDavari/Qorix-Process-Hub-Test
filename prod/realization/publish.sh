#!/usr/bin/env bash
# Publish the current working-tree changes to main, always in the same sequence:
#   1 on main -> 2 sync -> 3 check + regenerate -> 4 stage + review -> 5 commit -> 6 push -> 7 watch CI
# Usage:  bash prod/realization/publish.sh [-y] [--dry-run] [--skip-regen] ["commit message"]
#   -y            do not ask for confirmation
#   --dry-run     run steps 1-4 as a preview; change nothing in git, commit and push nothing
#   --skip-regen  skip the local check/regenerate step (CI still runs the same checks and fails on drift)
# Needs only git (+ python3 with PyYAML/jsonschema for step 3, optional) and gh (optional, step 7). No pip install.
set -euo pipefail
cd "$(dirname "$0")/../.."          # repository root

YES=0; DRY=0; SKIP=0; MSG=""
for a in "$@"; do
  case "$a" in -y) YES=1;; --dry-run) DRY=1;; --skip-regen) SKIP=1;; *) MSG="$a";; esac
done
say()  { printf '\n== %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
run()  { if [ "$DRY" = 1 ]; then echo "[dry-run] $*"; else "$@"; fi; }
EXCL=(':(exclude)build' ':(exclude)_build' ':(exclude,glob)bazel-*' ':(exclude,glob)**/__pycache__' ':(exclude).pytest_cache')   # never publish local artefacts

say "1/7 Branch: must be main"
cur=$(git branch --show-current)
if [ "$cur" != "main" ]; then echo "on '$cur', switching to main"; run git checkout main; fi

say "2/7 Sync with origin/main"
run git pull --rebase --autostash origin main

say "3/7 Check and regenerate"
if [ "$SKIP" = 1 ]; then
  echo "skipped (--skip-regen)"
elif python3 -c "import yaml" 2>/dev/null; then
  export PYTHONPATH=prod/realization/qpm
  python3 -m qpm check-process --assemblies prod/assemblies --standards needs/standards.yaml
  if python3 -c "import jsonschema; jsonschema.Draft202012Validator" 2>/dev/null; then
    bash prod/realization/regen.sh
  else
    warn "jsonschema >= 4 not available: regenerating assembly pages only, dist pages not refreshed"
    python3 -m qpm render-process --assemblies prod/assemblies --standards needs/standards.yaml --out-dir prod
  fi
else
  warn "PyYAML not available: skipping local check and regenerate. CI will fail on drift if generated pages are stale."
fi

say "4/7 Stage and review"
git add -A -- . "${EXCL[@]}"
if git diff --cached --quiet; then echo "Nothing to publish."; exit 0; fi
git status --short | head -40
echo "$(git diff --cached --name-only | wc -l) file(s) staged"
if [ "$DRY" = 1 ]; then git reset -q; echo "[dry-run] stopped before commit; staging undone"; exit 0; fi
if [ "$YES" != 1 ]; then read -r -p "Commit and push these to main? [y/N] " ok; [ "$ok" = "y" ] || { git reset -q; echo "Aborted; staging undone."; exit 1; }; fi

say "5/7 Commit"
[ -n "$MSG" ] || MSG="Update process hub $(date +%F): $(git diff --cached --name-only | wc -l) files"
git commit -m "$MSG"

say "6/7 Push to main"
git push origin main || { echo "push rejected, rebasing once and retrying"; git pull --rebase origin main; git push origin main; }

say "7/7 CI"
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  sleep 8
  id=$(gh run list --branch main --limit 1 --json databaseId -q '.[0].databaseId')
  gh run watch "$id" --exit-status && echo "CI green" || { echo "CI failed: gh run view $id --log-failed"; exit 1; }
else
  repo=$(git remote get-url origin | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')
  echo "gh not available or not logged in. Watch CI at: https://github.com/$repo/actions"
fi
