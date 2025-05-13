#!/bin/bash

# 🔧 경로 설정
PY_PATH="$HOME/git_auto/scripts/run_all.py"
LAST_DIR_TRACK="$HOME/.last_vscode_dir.txt"
STORAGE_FILE="$APPDATA/Code/storage.json"

was_alive=true

# 📁 VSCode에서 마지막으로 연 폴더 추출
get_last_vscode_dir() {
    grep -oE '"file://[^"]+"' "$STORAGE_FILE" | head -1 | sed 's|"file://||' | sed 's|"||'
}

while true; do
    sleep 10

    if pgrep -f "Code.exe" > /dev/null; then
        was_alive=true
    else
        if [ "$was_alive" = true ]; then
            echo "🛑 VSCode 종료 감지됨"

            DIR=$(get_last_vscode_dir)

            if [ -d "$DIR/.git" ]; then
                cd "$DIR" || exit

                ORIGIN=$(git config --get remote.origin.url | sed 's#.*/##' | sed 's/.git$//')
                NAME=$(basename "$DIR")

                if [ "$ORIGIN" = "$NAME" ]; then
                    echo "✅ $DIR: 실행 조건 만족 → run_all.py 실행"
                    python "$PY_PATH"
                else
                    echo "⚠️ $DIR: origin 이름 불일치 → skip"
                fi
            else
                echo "❌ $DIR: .git 폴더 없음 → skip"
            fi

            was_alive=false
        fi
    fi
done
