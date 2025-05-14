#!/bin/bash

# 🔧 동적 경로 설정
SCRIPT_DIR="$(dirname "$0")"
PY_PATH="$SCRIPT_DIR/run_all.py"
STORAGE_FILE="$APPDATA/Code/storage.json"

was_alive=true

get_last_vscode_dir() {
    grep -oE '"file://[^"]+"' "$STORAGE_FILE" | head -1 | sed 's|"file://||' | sed 's|"||'
}

echo "✅ auto_git.sh launched at $(date)" >> logs/scr/trigger_debug.log

while true; do
    sleep 10

    if pgrep -f "Code.exe" > /dev/null; then
        was_alive=true
    else
        if [ "$was_alive" = true ]; then
            DIR=$(get_last_vscode_dir)

            if [ -d "$DIR/.git" ]; then
                cd "$DIR" || exit

                ORIGIN=$(git config --get remote.origin.url | sed 's#.*/##' | sed 's/.git$//')
                NAME=$(basename "$DIR")

                if [ "$ORIGIN" = "$NAME" ]; then
                    echo "✅ $DIR: 실행 조건 만족 → run_all.py 실행 at $(date)" >> "$SCRIPT_DIR/logs/scr/trigger_debug.log"
                    python "$PY_PATH"
                else
                    echo "⚠️ $DIR: origin 이름 불일치 → skip" >> "$SCRIPT_DIR/logs/scr/trigger_debug.log"
                fi
            else
                echo "❌ $DIR: .git 폴더 없음 → skip" >> "$SCRIPT_DIR/logs/scr/trigger_debug.log"
            fi

            was_alive=false
        fi
    fi
done
