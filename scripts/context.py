import subprocess
from llm_router import call_llm
from utils.path import get_repo_paths
from pathlib import Path

def list_repo_files() -> list[str]:
    result = subprocess.run("git ls-files", shell=True, capture_output=True, text=True)
    return result.stdout.strip().splitlines()

def read_file_content(filepath: str) -> str:
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except:
        return ""

def build_context(log, timestamp: str, llm_file_cfg: dict, llm_repo_cfg: dict):
    log("📦 [Context] 레포 전체 파일 요약 시작")
    paths = get_repo_paths(timestamp)
    file_list = list_repo_files()
    log(f"🔹 총 {len(file_list)}개 파일 확인됨")

    repo_context_chunks = []

    for path in file_list:
        code = read_file_content(path)
        if not code.strip():
            continue

        prompt = f"""다음은 Git 레포의 파일 내용입니다. 이 파일의 **위치, 역할, 주요 로직, 평가**를 요약해주세요.

📁 파일 경로: {path}
📄 내용:
{code}
        """
        try:
            summary = call_llm(prompt, llm_file_cfg)
            repo_context_chunks.append(f"📁 {path}\n{summary.strip()}\n")
        except Exception as e:
            log(f"❌ 파일 요약 실패 - {path} / {e}")

    Path(paths["file"]).write_text("\n\n".join(repo_context_chunks), encoding="utf-8")
    log("🧠 [Context] 전체 레포 요약 시작")

    repo_prompt = f"""아래는 Git 레포의 각 파일에 대한 요약입니다. 이 레포는 어떤 목적과 구조를 가지며, 중요한 구성요소와 기술적 특성이 무엇인지 설명해주세요.

🧩 참고 파일 요약:
{'\n\n'.join(repo_context_chunks)}
    """
    try:
        final_summary = call_llm(repo_prompt, llm_repo_cfg)
        Path(paths["summary"]).write_text(final_summary.strip(), encoding="utf-8")
        log("✅ 전체 레포 요약 완료")
        return final_summary.strip()
    except Exception as e:
        log(f"❌ 전체 레포 요약 실패: {e}")
        return ""
