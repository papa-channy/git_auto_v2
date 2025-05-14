from llm_router import call_llm
from pathlib import Path

def read_prompt_file(style: str, lang: str) -> str:
    path = Path("prompt_by_style") / lang / f"{style}.txt"
    return path.read_text(encoding="utf-8").strip()

def generate_commit_and_record(
    diff_chunks: list[str],
    repo_context: str,
    llm_cfg_commit: dict,
    llm_cfg_final: dict,
    llm_cfg_record: dict,
    style_cfg: dict,
    lang_cfg: dict,
    log
):
    log("✏️ [Commit] 청크별 커밋 메시지 생성 시작")

    # 🔧 프롬프트 로딩
    commit_chunk_txt = read_prompt_file(style_cfg["commit_chunk"], lang_cfg["commit"])
    final_commit_txt = read_prompt_file(style_cfg["commit_final"], lang_cfg["commit"])
    record_prompt_txt = read_prompt_file(style_cfg["record"], lang_cfg["record"])

    commit_msgs = []
    prompt_vars = {}
    c_index = 1

    for chunk in diff_chunks:
        prompt = f"""아래는 Git 레포의 전체 맥락 요약과 변경된 diff chunk입니다.
각 변경 내용을 기반으로, 내부 프로젝트에 적합한 커밋 메시지를 요청에 맞게 작성하세요.

[Repo context]
{repo_context}

[변경된 diff 청크]
{chunk}

{commit_chunk_txt}
"""
        var_name = f"c{c_index}"
        prompt_vars[var_name] = {
            "text": prompt,
            "model": llm_cfg_commit["model"][0],
            "purpose": "commit_chunk"
        }
        c_index += 1

        try:
            response = call_llm(prompt, llm_cfg_commit)
            commit_msgs.append(response.strip())
        except Exception as e:
            log(f"❌ 커밋 청크 메시지 생성 실패: {e}")
            commit_msgs.append("[ERROR] 메시지 실패")

    # 최종 커밋 메시지
    d = f"""당신은 팀 프로젝트의 PR 메시지를 작성하는 전문가입니다.
아래는 레포의 전체 맥락과, chunk별로 생성된 커밋 메시지들입니다.

[Repo context]
{repo_context}

[개별 commit 메시지들]
{chr(10).join(commit_msgs)}

{final_commit_txt}
"""
    prompt_vars["d"] = {
        "text": d,
        "model": llm_cfg_final["model"][0],
        "purpose": "commit_final"
    }

    try:
        final_commit = call_llm(d, llm_cfg_final)
    except Exception as e:
        final_commit = "[ERROR] 최종 커밋 메시지 실패"
        log(f"❌ 최종 커밋 메시지 실패: {e}")

    # 기록용 메시지
    combined_diff = "\n\n".join(diff_chunks)
    e = f"""[Repo context]
{repo_context}

[전체 diff]
{combined_diff}

{record_prompt_txt}
"""
    prompt_vars["e"] = {
        "text": e,
        "model": llm_cfg_record["model"][0],
        "purpose": "record"
    }

    try:
        record_msg = call_llm(e, llm_cfg_record)
    except Exception as e:
        record_msg = "[ERROR] 기록 메시지 실패"
        log(f"❌ 기록용 메시지 실패: {e}")

    return commit_msgs, final_commit.strip(), record_msg.strip(), prompt_vars
