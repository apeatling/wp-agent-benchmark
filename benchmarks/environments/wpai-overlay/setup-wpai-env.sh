#!/usr/bin/env bash
# Installs WPAI Condition B (Skill + Registry) or Condition C (Skill + Registry + Playground CLI + Blueprints)
# into standard AI coding-agent skill discovery directories inside a Harbor container or local sandbox.
#
# Usage:
#   ./setup-wpai-env.sh --condition B|C [--wpai-home /opt/wpai] [--target-home "$HOME"]

set -euo pipefail

CONDITION="C"
WPAI_HOME="${WPAI_HOME:-/opt/wpai}"
TARGET_HOME="${HOME:-/root}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --condition)
      CONDITION="${2^^}"
      shift 2
      ;;
    --wpai-home)
      WPAI_HOME="$2"
      shift 2
      ;;
    --target-home)
      TARGET_HOME="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 --condition B|C [--wpai-home /opt/wpai] [--target-home \$HOME]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "${CONDITION}" != "B" && "${CONDITION}" != "C" ]]; then
  echo "Error: --condition must be B or C (got '${CONDITION}')." >&2
  exit 2
fi

SKILL_SRC="${WPAI_HOME}/skills/wp-platform-selection"
REGISTRY_SRC="${WPAI_HOME}/registry/wp-capabilities.json"

if [[ ! -d "${SKILL_SRC}" ]]; then
  echo "Error: skill directory not found at ${SKILL_SRC}" >&2
  exit 1
fi
if [[ ! -f "${REGISTRY_SRC}" ]]; then
  echo "Error: capability registry not found at ${REGISTRY_SRC}" >&2
  exit 1
fi

# Install skill into standard agent discovery paths across Claude Code, Codex, Cursor, and generic agents.
SKILL_TARGETS=(
  "${TARGET_HOME}/.claude/skills/wp-platform-selection"
  "${TARGET_HOME}/.codex/skills/wp-platform-selection"
  "${TARGET_HOME}/.cursor/skills/wp-platform-selection"
  "${TARGET_HOME}/.agents/skills/wp-platform-selection"
)

for dest in "${SKILL_TARGETS[@]}"; do
  mkdir -p "$(dirname "${dest}")"
  rm -rf "${dest}"
  cp -R "${SKILL_SRC}" "${dest}"
done

# Make capability registry discoverable at a predictable path.
mkdir -p "${TARGET_HOME}/.wpai"
cp "${REGISTRY_SRC}" "${TARGET_HOME}/.wpai/wp-capabilities.json"

if [[ "${CONDITION}" == "B" ]]; then
  # Condition B deliberately excludes Playground runtime & blueprints to isolate Discovery + Registry.
  rm -rf "${WPAI_HOME}/blueprints" "${TARGET_HOME}/.wpai/blueprints" || true
  echo "[wpai] Configured Condition B (Discovery Skill + Capability Registry) for ${TARGET_HOME}."
  exit 0
fi

# Condition C: Also install starter blueprints and pre-warm @wp-playground/cli@3.1.66 if Node/npm is present.
if [[ -d "${WPAI_HOME}/blueprints" ]]; then
  rm -rf "${TARGET_HOME}/.wpai/blueprints"
  cp -R "${WPAI_HOME}/blueprints" "${TARGET_HOME}/.wpai/blueprints"
fi

if command -v npm >/dev/null 2>&1; then
  npm install -g @wp-playground/cli@3.1.66 --no-audit --no-fund
fi

echo "[wpai] Configured Condition C (Discovery Skill + Registry + Playground CLI + Blueprints) for ${TARGET_HOME}."
