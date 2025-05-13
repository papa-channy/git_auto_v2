from llm_router import call_llm

def generate_commit_chunks(diff_chunks: list[str], repo_context: str, llm_cfg: dict, log) -> list[str]:
    """각 diff 청크에 대해 개별 커밋 메시지를 생성"""
    commit_msgs = []

    for i, chunk in enumerate(diff_chunks):
        log(f"🧩 [{i+1}/{len(diff_chunks)}] 커밋 청크 메시지 생성 중...")

        prompt = f"""아래는 Git 레포의 전체 맥락 요약입니다. 이 맥락을 바탕으로, 변경된 diff 내용을 요약하여 내부 프로젝트에 적합한 Git 커밋 메시지를 생성해주세요.

⚙️ 레포 맥락 요약:
{repo_context}

📝 변경된 diff 내용:
{chunk}

🔧 요청사항:
- 한 줄 제목 포함 (요약)
- 변경 이유, 핵심 로직, 고려한 요소 등을 포함한 설명
- 협업 또는 미래의 나를 위한 요약 커밋 메시지

🎯 형식은 다음과 유사하게 작성해주세요:
{{
제목: ...
설명: ...
주의사항 or 메모: ...
}}
"""

        try:
            response = call_llm(prompt, llm_cfg)
            commit_msgs.append(response.strip())
        except Exception as e:
            log(f"❌ chunk {i+1} 메시지 실패: {e}")
            commit_msgs.append(f"[ERROR] 메시지 생성 실패 - chunk {i+1}")

    return commit_msgs


def generate_final_commit(commit_msgs: list[str], repo_context: str, llm_cfg: dict, log) -> str:
    """개별 커밋 메시지들을 기반으로, 전체 PR용 요약 메시지를 생성"""
    prompt = f"""당신은 팀 프로젝트의 PR 메시지를 작성하는 전문가입니다. 아래는 레포의 전체 맥락과, 청크별로 생성된 커밋 메시지들입니다.

🧱 레포 맥락:
{repo_context}

🧩 개별 커밋 메시지들:
{chr(10).join(commit_msgs)}

✍️ 요청사항:
- 팀원들이 빠르게 핵심 내용을 파악할 수 있도록 최종 요약 커밋 메시지를 작성해주세요.
- 구조는 다음과 같이 해주세요:

<type>: <요약 문장>

본문:
- 어떤 변경을 했는지
- 왜 이 변경이 필요한지
- 어떤 영향을 주는지
"""

    log("🧠 최종 커밋 메시지 생성 중...")
    try:
        result = call_llm(prompt, llm_cfg)
        log("✅ 최종 커밋 메시지 생성 완료")
        return result.strip()
    except Exception as e:
        log(f"❌ 최종 커밋 메시지 실패: {e}")
        return "[ERROR] 최종 메시지 실패"
