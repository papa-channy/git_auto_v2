#!/bin/bash

# 📁 Git 프로젝트인지 확인
if [ ! -d ".git" ] && [ ! -f ".git" ]; then
  exit 1
fi

# 📌 레포 이름 확인
CURRENT_NAME=$(basename "$(pwd)")
ORIGIN_URL=$(git config --get remote.origin.url 2>/dev/null)
if [ -z "$ORIGIN_URL" ]; then
  exit 1
fi
REMOTE_NAME=$(basename -s .git "$ORIGIN_URL")

if [ "$CURRENT_NAME" != "$REMOTE_NAME" ]; then
  exit 1
fi

# 🔁 감시 시작
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN_SCRIPT="$SCRIPT_DIR/commit_gen.py"

if tasklist | grep -q "Code.exe"; then
  PREVIOUS_RUNNING=1
else
  PREVIOUS_RUNNING=0
fi

while true; do
  if tasklist | grep -q "Code.exe"; then
    if [ "$PREVIOUS_RUNNING" -eq 0 ]; then
      PREVIOUS_RUNNING=1
    fi
  else
    if [ "$PREVIOUS_RUNNING" -eq 1 ]; then
      python "$GEN_SCRIPT"
      PREVIOUS_RUNNING=0
      find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} +
    fi
  fi
  sleep 10
done
