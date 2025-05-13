def classify_for_notify(
    chunk_msgs: list[str],
    final_msg: str,
    repo_context: str,
    status: str,
    cost_summary_msg: str
) -> list[str]:
    """
    알림 플랫폼 전송용 메시지 5개 반환
    1. 레포 요약
    2. 청크별 커밋 메시지
    3. 최종 메시지
    4. Git 상태
    5. 비용 요약
    """
    messages = []

    messages.append(f"🧠 전체 레포 요약\n{'─'*10}\n{repo_context.strip()}")
    for i, msg in enumerate(chunk_msgs):
        messages.append(f"🔹 Chunk {i+1}\n{msg.strip()}")
    messages.append(f"📦 최종 커밋 메시지\n{'─'*10}\n{final_msg.strip()}")
    messages.append(f"📤 Git Push 상태: {'✅ 성공' if status == 'success' else '❌ 실패'}")
    messages.append(f"💰 LLM 사용 요약\n{'─'*10}\n{cost_summary_msg.strip()}")

    return messages


def classify_for_record(
    repo_context: str,
    chunk_msgs: list[str],
    record_msg: str
) -> list[str]:
    """
    기록용 메시지 3개 반환
    1. 전체 맥락 요약
    2. 청크 전체 요약본
    3. doc_writing 기록 메시지
    """
    return [
        repo_context.strip(),
        "\n".join(chunk.strip() for chunk in chunk_msgs),
        record_msg.strip()
    ]


def classify_for_git(final_msg: str) -> str:
    """
    Git 커밋 메시지 1개 반환
    """
    return final_msg.strip()
