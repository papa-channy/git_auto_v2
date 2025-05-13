import subprocess
from pathlib import Path
from llm_router import call_llm
from utils.path import get_result_paths

INCLUDE_EXT = {".py", ".sh"}

def is_valid_source_file(path: Path) -> bool:
    return path.suffix in INCLUDE_EXT and not path.name.startswith(".")

def get_repo_name() -> str:
    result = subprocess.run("git config --get remote.origin.url", shell=True, capture_output=True, text=True)
    url = result.stdout.strip()
    return url.rstrip(".git").split("/")[-1] if url else Path.cwd().name

def get_folder_structure_with_status(valid_files: list[Path]) -> str:
    lines = []
    for path in sorted(valid_files):
        parts = list(path.relative_to(".").parts)
        indent = "│   " * (len(parts) - 1) + "├── "
        status = ""
        try:
            if not path.read_text(encoding="utf-8").strip():
                status = " - Pending composition"
        except:
            status = " - [READ ERROR]"
        lines.append(f"{indent}{path.name}{status}")
    return "\n".join(lines)

def get_readme_content() -> str:
    readme = Path("README.md")
    if readme.exists():
        return readme.read_text(encoding="utf-8").strip()
    return "아직 미작성"

def list_all_repo_files() -> list[Path]:
    return [p for p in Path(".").rglob("*") if p.is_file() and not any(part.startswith(".") for part in p.parts)]

def build_context(log, timestamp: str, llm_file_cfg: dict, llm_repo_cfg: dict):
    log("📦 [Context] 레포 전체 파일 요약 시작")
    paths = get_result_paths(timestamp)
    repo_name = get_repo_name()

    all_files = list_all_repo_files()
    valid_files = [p for p in all_files if is_valid_source_file(p)]
    log(f"🔹 필터링된 유효 파일 수: {len(valid_files)}")

    folder_structure = get_folder_structure_with_status(valid_files)
    readme_text = get_readme_content()

    repo_context_chunks = []
    prompt_vars = {}
    a_index = 1

    for path in valid_files:
        try:
            code = path.read_text(encoding="utf-8").strip()
        except:
            continue

        if not code:
            continue

        prompt = f"""당신은 Git Repo 전체를 분석하여, Commit 메시지 생성 및 기술 문서 작성을 도울 요약 전문가입니다.
이 요약은 코드의 버전 기록, 기술 문서화, 그리고 미래의 작업자나 나 자신을 위한 구조적 설명을 만드는 데 사용될 것입니다.

📌 레포 이름: {repo_name}
📁 폴더 구조:
{folder_structure}

📄 README.md 내용:
{readme_text}

📍 파일 경로: {path}
📄 파일 내용:
{code}

이 파일의 이름, Repo의 폴더 구조, 파일내용을 기반으로
해당 파일의 Repo내 역할, 로직, 로직의 논리를 분석하여 요약해주세요.
"""

        var_name = f"a{a_index}"
        prompt_vars[var_name] = prompt
        a_index += 1

        try:
            summary = call_llm(prompt, llm_file_cfg)
            repo_context_chunks.append(f"📁 {path}\n{summary.strip()}\n")

            save_path = paths["context_by_file"] / f"{path.name}.txt"
            save_path.write_text(summary.strip(), encoding="utf-8")

        except Exception as e:
            log(f"❌ 파일 요약 실패 - {path} / {e}")

    log("🧠 [Context] 전체 레포 요약 생성 중")

    combined = "\n\n".join(repo_context_chunks)

    b = f"""당신은 Git 레포 전체를 해석해, 기술 문서, 커밋 메시지, 집필용 기록 보관에 사용될 "전체 레포 맥락 요약"을 생성하는 요약 전문가입니다.

이 레포는 다음과 같은 구조와 목적을 갖고 있습니다:

📌 레포 이름: {repo_name}
📁 폴더 구조:
{folder_structure}

📄 README.md 내용:
{readme_text}

🧩 각 파일 요약:
{combined}

📝 요청사항:
제공한 내용을 바탕으로 아래 내용을 작성해주세요요
- 이 Repo의 제작 목적
- 이 Repo의 주요 기능
- 전체 구성 구조
- 폴더별 책임
- 주요 파일 및 핵심 로직
- 설계 철학이나 아키텍처 특징
"""
    prompt_vars["b"] = b

    try:
        final_summary = call_llm(b, llm_repo_cfg)
        Path(paths["context_summary"]).write_text(final_summary.strip(), encoding="utf-8")
        log("✅ 전체 레포 요약 완료")
        return final_summary.strip(), prompt_vars

    except Exception as e:
        log(f"❌ 전체 레포 요약 실패: {e}")
        return "", prompt_vars
