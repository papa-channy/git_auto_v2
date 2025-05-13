from pathlib import Path
from datetime import datetime

def get_repo_paths(timestamp: str) -> dict:
    """repo 경로 생성 및 리턴"""
    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
    base = Path("repo") / dt.strftime("%y%m") / dt.strftime("%d_%H%M")
    summary_path = base / "summary.txt"
    file_path = base / "file.txt"
    base.mkdir(parents=True, exist_ok=True)
    return {
        "base": base,
        "summary": summary_path,
        "file": file_path
    }
