#!/usr/bin/env bash
# Regenerate all committed, generated content. CI runs this and fails on `git diff`.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=tools/qpm
B=model/tiers/00_score_base/score_base.qpm.yaml
Q=model/tiers/10_qorix/qorix_overlay.qpm.yaml
IDS=model/tiers/00_score_base/score_process_ids.txt

python3 -m qpm render-process --areas process/areas --external-ids "$IDS" --out-dir docs/process_areas

python3 -m qpm compose --tier "$B" --tier "$Q" --out-dir build/qorix
cp build/qorix/tailoring_report.rst docs/tailoring/qorix.rst
toc="qorix"
for t in projects/*/tailoring.qpm.yaml; do
  p=$(basename "$(dirname "$t")"); [[ "$p" == _* ]] && continue
  python3 -m qpm compose --tier "$B" --tier "$Q" --tier "$t" --out-dir "build/$p"
  cp "build/$p/tailoring_report.rst" "docs/tailoring/$p.rst"
  toc="$toc $p"
done
{ echo "Tailoring Reports"; echo "#################"; echo; echo ".. toctree::"; echo "   :maxdepth: 1"; echo
  for p in $toc; do echo "   $p"; done; } > docs/tailoring/index.rst

python3 -m qpm export-upstream --base "$B" --overlay "$Q" \
  --score-yaml model/tiers/00_score_base/score_metamodel.upstream.yaml --out-dir upstream/score_proposal
