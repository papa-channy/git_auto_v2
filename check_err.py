import os, json, subprocess, requests
from pathlib import Path
from dotenv import load_dotenv

# ────────────────────────────────
# 🔹 .env 로딩 + Fireworks API Key 로드
# ────────────────────────────────
def load_env_and_api_key():
    env_path = Path(__file__).parent.resolve() / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("FIREWORKS_API_KEY", "")
    if not api_key:
        print_status("FIREWORKS_API_KEY", "없음", "fail")
        exit(1)

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }, api_key

# ────────────────────────────────
# 🔹 상태 출력 헬퍼
# ────────────────────────────────
def print_status(label, value, status="ok"):
    symbols = {"ok": "✅", "warn": "⚠️", "fail": "❌"}
    print(f"{symbols[status]} {label}: {value}")

def run(cmd): return subprocess.run(cmd, shell=True, text=True, capture_output=True).stdout.strip()

# ────────────────────────────────
# 🔹 Git 설정 자동 등록
# ────────────────────────────────
def check_git_user_config():
    if not run("git config --global user.name"):
        subprocess.run('git config --global user.name "git-llm-user"', shell=True)
    if not run("git config --global user.email"):
        subprocess.run('git config --global user.email "git@llm.com"', shell=True)
    print_status("Git 사용자 설정", "등록됨")

def enforce_git_core_config():
    subprocess.run("git config --global core.autocrlf input", shell=True)
    subprocess.run("git config --global core.quotepath false", shell=True)
    print_status("core.autocrlf / quotepath", "적용 완료")

# ────────────────────────────────
# 🔹 필수 파일 (.editorconfig, .gitattributes)
# ────────────────────────────────
def ensure_required_files():
    base = Path(__file__).parent.resolve()
    if not (base / ".gitattributes").exists():
        (base / ".gitattributes").write_text("* text=auto\n", encoding="utf-8")
    if not (base / ".editorconfig").exists():
        (base / ".editorconfig").write_text(
            "[*]\nend_of_line = lf\ninsert_final_newline = true\ncharset = utf-8\n", encoding="utf-8"
        )
    print_status("필수 설정 파일", "확인 완료")

# ────────────────────────────────
# 🔹 Git 레포 상태 점검
# ────────────────────────────────
def check_git_repo():
    if subprocess.run("git rev-parse --is-inside-work-tree", shell=True).returncode != 0:
        print_status("Git 레포", ".git 없음", "fail")
        exit(1)
    print_status("Git 레포", "확인됨")

def check_git_remote():
    remote = run("git config --get remote.origin.url")
    if not remote:
        print_status("remote.origin.url", "없음", "fail"); exit(1)
    if subprocess.run(f"git ls-remote {remote}", shell=True, capture_output=True).returncode != 0:
        print_status("원격 저장소 접근", "실패", "fail"); exit(1)
    print_status("원격 저장소", "접근 성공")

# ────────────────────────────────
# 🔹 Git diff 확인 (없으면 예시 삽입)
# ────────────────────────────────
def get_diff_or_example():
    diff = run("git diff --cached")
    if diff: return diff
    print_status("Diff", "없음 → 예시 diff 삽입", "warn")
    return """diff --git a/main.py b/main.py
index 0000000..1111111 100644
--- a/main.py
+++ b/main.py
@@ def hello():
+    print("Hello, Git Automation!")"""

# ────────────────────────────────
# 🔹 Fireworks LLM 호출 (maverick instruct-basic용)
# ────────────────────────────────
def call_fireworks_api(prompt: str, api_key: str) -> str:
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    payload = {
        "model": "accounts/fireworks/models/llama4-maverick-instruct-basic",
        "max_tokens": 1024,
        "top_p": 0.8,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print_status("LLM 호출", f"실패 - {e}", "fail")
        exit(1)

# ────────────────────────────────
# 🔹 설정 파일 로딩 (git_config.json)
# ────────────────────────────────
def load_config():
    config_path = Path(__file__).parent.resolve() / "git_config.json"
    if not config_path.exists():
        print_status("설정 파일", "git_config.json 없음", "fail")
        exit(1)
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except:
        print_status("git_config.json", "JSON 파싱 실패", "fail")
        exit(1)

# ────────────────────────────────
# 🔹 알림 플랫폼 ping 함수 호출
# ────────────────────────────────
def check_notify_platforms(pf_list):
    import notify.discord as discord
    import notify.kakao as kakao
    import notify.gmail as gmail
    import notify.slack as slack

    ping_map = {
        "discord": discord.ping,
        "kakao": kakao.ping,
        "gmail": gmail.ping,
        "slack": slack.ping
    }

    for pf in pf_list:
        if pf not in ping_map:
            print_status(f"{pf} 알림 테스트", "지원되지 않음", "warn")
            continue
        if ping_map[pf]():
            print_status(f"{pf} 알림 테스트", "성공", "ok")
        else:
            print_status(f"{pf} 알림 테스트", "실패", "fail")
            exit(1)

# ────────────────────────────────
# 🔹 Main 실행
# ────────────────────────────────
def main():
    print("\n🔍 check_err: 자동화 사전 점검 시작\n")

    global HEADERS
    HEADERS, api_key = load_env_and_api_key()

    check_git_user_config()
    enforce_git_core_config()
    ensure_required_files()
    check_git_repo()
    check_git_remote()

    config = load_config()
    if "noti_pf" in config:
        check_notify_platforms(config["noti_pf"])

    diff = get_diff_or_example()
    result = call_fireworks_api(diff, api_key)
    print_status("LLM 메시지 생성", f"\n{result}", "ok")

    print("\n🎉 모든 점검 완료. 자동화 준비 OK.\n")

if __name__ == "__main__":
    main()
