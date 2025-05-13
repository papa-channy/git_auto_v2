# scripts/run_all.py

from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs/scr")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 타임스탬프 기반 로그 파일 생성
now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = LOG_DIR / f"{now_str}.log"

def log(msg: str):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg.strip() + "\n")
