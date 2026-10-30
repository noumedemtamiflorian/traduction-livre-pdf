#!/usr/bin/env bash
# Bash Installer for `traduction-livre-pdf` Skill (macOS / Linux)
set -e

SKILL_NAME="traduction-livre-pdf"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Installing Skill '$SKILL_NAME' ==="

echo "[1/2] Installing Python dependencies (pypdf, reportlab, Pillow)..."
python3 -m pip install -r "$SOURCE_DIR/requirements.txt" --quiet

echo "[2/2] Copying skill files to global AI agent directories..."
TARGET_DIRS=(
  "$HOME/.gemini/config/skills/$SKILL_NAME"
  "$HOME/.agents/skills/$SKILL_NAME"
  "$HOME/.claude/skills/$SKILL_NAME"
  "$HOME/.config/opencode/skills/$SKILL_NAME"
)

for DEST in "${TARGET_DIRS[@]}"; do
  mkdir -p "$DEST"
  cp -f "$SOURCE_DIR/SKILL.md" "$DEST/"
  cp -f "$SOURCE_DIR/requirements.txt" "$DEST/"
  cp -rf "$SOURCE_DIR/scripts" "$DEST/"
  cp -rf "$SOURCE_DIR/references" "$DEST/"
  echo "  -> Installed to: $DEST"
done

echo ""
echo "Success! The '$SKILL_NAME' skill is now installed globally."
