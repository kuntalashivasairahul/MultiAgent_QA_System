#!/usr/bin/env bash
# Fetch a pinned corpus; preserve local edits and the previous snapshot.
set -euo pipefail
project_dir="$(cd "$(dirname "$0")" && pwd)"
revision="$(tr -d '[:space:]' < "$project_dir/CORPUS_REVISION")"
corpus_path="$project_dir/corpus"
if [[ ! "$revision" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Invalid CORPUS_REVISION" >&2
    exit 1
fi
if [[ -e "$corpus_path" ]]; then
    if [[ "$(git -C "$corpus_path" rev-parse --show-toplevel 2>/dev/null)" != "$corpus_path" ]]; then
        echo "Existing corpus is not a Git checkout; preserved without changes." >&2
        exit 1
    fi
    if [[ -n "$(git -C "$corpus_path" status --porcelain)" ]]; then
        echo "Corpus has local changes; preserved without changes." >&2
        exit 1
    fi
    if [[ "$(git -C "$corpus_path" rev-parse HEAD)" == "$revision" ]]; then
        echo "Corpus already at pinned revision $revision"
        exit 0
    fi
fi
stage="$(mktemp -d "$project_dir/.corpus-fetch.XXXXXX")"
trap 'rm -rf "$stage"' EXIT
git clone --depth 1 --filter=blob:none --sparse --no-checkout \
    https://github.com/temporalio/documentation.git "$stage/corpus"
git -C "$stage/corpus" fetch --depth 1 origin "$revision"
git -C "$stage/corpus" sparse-checkout set docs
git -C "$stage/corpus" checkout --detach "$revision"
if [[ ! -d "$stage/corpus/docs" ]]; then
    echo "Pinned revision has no docs; previous corpus preserved." >&2
    exit 1
fi
backup=""
if [[ -e "$corpus_path" ]]; then
    backup="$(mktemp -d "$project_dir/.corpus-backup-XXXXXX")"
    mv "$corpus_path" "$backup/corpus"
fi
if ! mv "$stage/corpus" "$corpus_path"; then
    if [[ -n "$backup" ]]; then mv "$backup/corpus" "$corpus_path"; fi
    exit 1
fi
echo "Corpus pinned at $revision"
if [[ -n "$backup" ]]; then echo "Previous corpus preserved in $backup/corpus"; fi
