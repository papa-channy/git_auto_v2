import subprocess
from pathlib import Path
from utils.path import get_result_paths

def get_git_diff(log=None) -> str:
    """git diff 결과 추출 (git add 전 기준)"""
    if log: log("🔍 git diff 추출 중...")
    result = subprocess.run(
        ["git", "diff"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    diff_text = result.stdout.strip()
    if not diff_text:
        if log: log("⚠️ git diff 결과 없음")
        raise ValueError("❌ 변경된 내용 없음 (git diff 결과 없음)")
    if log: log("✅ git diff 추출 완료")
    return diff_text


def split_diff_by_function(diff_text: str, timestamp: str, log=None, max_line_threshold: int = 200, block_size: int = 3) -> list[str]:
    """@@ 기준으로 git diff를 함수 단위 청크로 나눔 + 파일로 저장"""
    if log: log("🧩 diff 청크 분할 시작")
    paths = get_result_paths(timestamp)
    chunk_dir = paths["diff_chunks"]
    chunk_dir.mkdir(parents=True, exist_ok=True)

    lines = diff_text.splitlines()
    if len(lines) <= max_line_threshold:
        if log: log("🔹 전체 diff가 짧아 단일 청크 처리")
        chunk_path = chunk_dir / "chunk_1.txt"
        chunk_path.write_text(diff_text.strip(), encoding="utf-8")
        return [diff_text.strip()]

    block_starts = [i for i, line in enumerate(lines) if line.startswith("@@")]
    if not block_starts:
        if log: log("⚠️ @@ 블록 없음 → 고정 길이 분할")
        chunks = ["\n".join(lines[i:i+max_line_threshold]) for i in range(0, len(lines), max_line_threshold)]
    else:
        block_starts.append(len(lines))
        chunks = []
        for i in range(0, len(block_starts) - 1, block_size):
            start, end = block_starts[i], block_starts[min(i + block_size, len(block_starts) - 1)]
            chunk = "\n".join(lines[start:end]).strip()
            if chunk:
                chunks.append(chunk)

    # 저장
    for i, chunk in enumerate(chunks):
        file_path = chunk_dir / f"chunk_{i+1}.txt"
        file_path.write_text(chunk, encoding="utf-8")

    if log: log(f"✅ {len(chunks)}개의 diff 청크 저장 완료")
    return chunks
