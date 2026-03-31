#!/usr/bin/env bash
set -euo pipefail

DOCKERFILE_PATH="${1:-Dockerfile}"

if [[ ! -f "$DOCKERFILE_PATH" ]]; then
  echo "ERROR: Dockerfile not found at '$DOCKERFILE_PATH'" >&2
  exit 1
fi

warn_count=0
info_count=0

warn() {
  warn_count=$((warn_count + 1))
  printf '[WARN] %s\n' "$1"
}

info() {
  info_count=$((info_count + 1))
  printf '[INFO] %s\n' "$1"
}

has_line() {
  local pattern="$1"
  grep -Eiq "$pattern" "$DOCKERFILE_PATH"
}

printf 'Auditing %s\n' "$DOCKERFILE_PATH"

# Base image checks
if has_line '^\s*FROM\s+[^[:space:]]+:latest'; then
  warn "Avoid ':latest' tags in FROM. Use explicit versions."
fi

if grep -Eq '^\s*FROM\s+[^[:space:]]+$' "$DOCKERFILE_PATH"; then
  warn "Some FROM lines have no explicit tag. Consider pinning a version."
fi

# Privilege checks
if ! has_line '^\s*USER\s+'; then
  warn "No USER instruction found. Run as non-root when possible."
elif has_line '^\s*USER\s+root\s*$'; then
  warn "USER is root. Prefer a non-root runtime user."
else
  info "Non-root USER detected."
fi

# Reliability checks
if ! has_line '^\s*HEALTHCHECK\s+'; then
  warn "No HEALTHCHECK found. Add one for long-lived services if applicable."
fi

# Docker hygiene checks
if has_line '^\s*ADD\s+'; then
  warn "ADD detected. Prefer COPY unless ADD-specific behavior is required."
fi

if has_line 'apt-get\s+update' && ! has_line 'rm\s+-rf\s+/var/lib/apt/lists'; then
  warn "apt metadata cleanup missing. Remove /var/lib/apt/lists to reduce layer size."
fi

if has_line 'pip\s+install' && ! has_line 'pip\s+install\s+--no-cache-dir'; then
  warn "pip install without --no-cache-dir may increase image size."
fi

# Build/cache checks
if has_line '^\s*COPY\s+\.\s+'; then
  info "COPY . detected. Ensure dependency installation happens before copying volatile source."
fi

from_count=$(grep -Eic '^\s*FROM\s+' "$DOCKERFILE_PATH" || true)
if (( from_count == 1 )); then
  info "Single-stage build detected. Multi-stage may reduce runtime image size."
fi

# .dockerignore check
dockerfile_dir=$(cd "$(dirname "$DOCKERFILE_PATH")" && pwd)
if [[ ! -f "$dockerfile_dir/.dockerignore" ]]; then
  warn ".dockerignore not found next to Dockerfile. Consider adding one to reduce build context."
else
  info ".dockerignore found."
fi

printf '\nSummary: %d warning(s), %d info message(s)\n' "$warn_count" "$info_count"

if (( warn_count == 0 )); then
  echo "Result: no major issues detected by heuristic audit."
fi
