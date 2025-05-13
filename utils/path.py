from pathlib import Path
from datetime import datetime

def get_result_paths(timestamp: str) -> dict:
    """
    실행 기준 타임스탬프에 따라 결과 저장용 경로를 생성하고 반환합니다.
    반환 구조는 dict로 각 결과 타입별 저장 경로를 포함합니다.
    """
    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M")
    date_key = dt.strftime("%y%m%d_%H%M")
    result_base = Path("results") / date_key

    paths = {
        "base": result_base,
        "context_by_file": result_base / "context" / "by_file",
        "context_summary": result_base / "context" / "sum" / "summary.txt",
        "diff_chunks": result_base / "diff" / "chunk",
        "diff_final": result_base / "diff" / "sum" / "commit.txt",
        "final_commit": result_base / "final" / "commit.txt",
        "final_record": result_base / "final" / "record.txt",
    }

    # 디렉토리 생성
    for key, path in paths.items():
        if key.startswith("context") or key.startswith("diff") or key.startswith("final"):
            path.parent.mkdir(parents=True, exist_ok=True)

    return paths

def get_cost_log_path(timestamp: str) -> Path:
    """
    LLM 호출 로그를 저장할 cost 경로 반환
    ex: cost/250514_1810/llm_20240514_1810.jsonl
    """
    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M")
    base = Path("cost") / dt.strftime("%y%m%d_%H%M")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"llm_{timestamp}.jsonl"
