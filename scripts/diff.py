import subprocess

def get_git_diff(log=None) -> str:
    if log: log("🔍 git diff 추출 중...")
    result = subprocess.run(
        ["git", "diff"], capture_output=True, text=True, encoding="utf-8"
    )
    diff_text = result.stdout.strip()
    if not diff_text:
        if log: log("⚠️ 변경 사항 없음")
        raise ValueError("❌ 변경된 내용 없음 (git diff 결과 없음)")
    if log: log("✅ git diff 추출 완료")
    return diff_text

def split_diff_by_function(diff_text: str, max_line_threshold: int = 200, block_size: int = 4, log=None) -> list[str]:
    if log: log("🧩 diff 청크 분할 중...")
    lines = diff_text.splitlines()
    if len(lines) <= max_line_threshold:
        if log: log(f"🔹 전체 diff가 {max_line_threshold}줄 이내 → 단일 청크 처리")
        return [diff_text]

    block_starts = [i for i, line in enumerate(lines) if line.startswith("@@")]
    if not block_starts:
        if log: log("⚠️ @@ 블록 없음 → 고정 길이 분할")
        return ["\n".join(lines[i:i + max_line_threshold]) for i in range(0, len(lines), max_line_threshold)]

    chunks = []
    block_starts.append(len(lines))
    for i in range(0, len(block_starts) - 1, block_size):
        start, end = block_starts[i], block_starts[min(i + block_size, len(block_starts) - 1)]
        chunk = "\n".join(lines[start:end]).strip()
        if chunk:
            chunks.append(chunk)
    if log: log(f"✅ 총 {len(chunks)}개의 diff 청크 생성 완료")
    return chunks
