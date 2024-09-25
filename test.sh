#!/usr/bin/env bash

set -euo pipefail

print_status() {
  echo -en "\n➡️  $1\n\n"
}

if ! command -v uv > /dev/null; then
  echo "Error: 'uv' is not installed or not in the PATH."
  echo "To install it, run:"
  echo "  $ curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

curdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_status "Running \`ruff check\`..."
uv run --frozen -- ruff check

print_status "Running \`ruff format --check\`..."
uv run --frozen -- ruff format --check

print_status "Running \`mypy\`..."
uv run --frozen -- mypy

print_status "Running \`pytest\`..."
uv run --frozen -- pytest  \
    --junitxml=junit.xml \
    --override-ini=junit_family=legacy \
    --cov \
    --cov-append \
    --cov-report xml:coverage.xml \
    --cov-report html

print_status "Running \`pre-commit\`..."
uv run --frozen -- pre-commit run --all-files
