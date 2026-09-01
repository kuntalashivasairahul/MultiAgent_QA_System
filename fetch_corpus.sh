#!/usr/bin/env bash
# Sparse-clone Temporal's docs as the knowledge base corpus.
set -euo pipefail
rm -rf corpus
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/temporalio/documentation.git corpus
git -C corpus sparse-checkout set docs
echo "files: $(find corpus/docs -name '*.md*' | wc -l | tr -d ' ')"
