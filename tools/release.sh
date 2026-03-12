#!/usr/bin/env bash
# Bump version, re-lock, and commit.
# Usage: tools/release.sh {major|minor|patch}
set -euo pipefail

bump="${1:?usage: $0 major|minor|patch}"

# uv version --bump writes pyproject.toml and re-locks by default.
# --short prints only the new version so we can embed it in the commit.
version="$(uv version --bump "$bump" --short)"

git add pyproject.toml uv.lock
git commit -m "chore: release $version"
