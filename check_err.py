import os, json, subprocess, requests, shutil
from pathlib import Path
from dotenv import load_dotenv

# ────────────────────────────────
# 🔹 환경변수 로딩
# ────────────────────────────────
def load_env_and_api_key():
    env_path = Path(__file__).parent.resolve() / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("FIREWORKS_API_KEY", "")
    username = os.getenv("username", "")
    if not api_key or not username:
        print_status(".env 설정", "FIREWORKS_API_KEY 또는 username 누락", "fail")
        exit(1)

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }, api_key, username

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
# 🔹 설정 파일 로딩 (config/*.json)
# ────────────────────────────────
def load_config():
    base_path = Path(__file__).parent.resolve() / "config"
    required_configs = ["llm.json", "style.json", "noti.json", "cost.json"]

    for cfg in required_configs:
        cfg_path = base_path / cfg
        if not cfg_path.exists():
            print_status(f"설정 파일 {cfg}", "없음", "fail")
            exit(1)

    print_status("모든 설정 파일", "확인 완료")
    return json.loads((base_path / "noti.json").read_text(encoding="utf-8"))

# ────────────────────────────────
# 🔹 알림 플랫폼 ping 함수 호출
# ────────────────────────────────
def check_notify_platforms(pf_list):
    import notify.discord as discord
    import notify.kakao as kakao
    import notify.gmail as gmail
    import notify.slack as slack

    ping_map = {"discord": discord.ping, "kakao": kakao.ping, "gmail": gmail.ping, "slack": slack.ping}

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
# 🔹 .bat 자동 생성 + 즉시 실행
# ────────────────────────────────
def auto_create_and_run_bat(username):
    startup_path = Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
    bat_path = startup_path / "set_auto.bat"
    bash_script = f"C:/Users/{username}/Desktop/git_auto/auto_git.sh"

    content = f"""@echo off
start "" "C:\\Program Files\\Git\\bin\\bash.exe" --login -i "{bash_script}"
"""

    bat_path.write_text(content, encoding="utf-8")
    subprocess.Popen([str(bat_path)], shell=True)
    print_status("set_auto.bat 생성 및 즉시 실행", f"{bat_path}", "ok")

# ────────────────────────────────
# 🔹 Main 실행
# ────────────────────────────────
def main():
    print("\n🔍 check_err: 자동화 사전 점검 및 설정 시작\n")

    global HEADERS
    HEADERS, api_key, username = load_env_and_api_key()

    check_git_user_config()
    enforce_git_core_config()
    ensure_required_files()
    check_git_repo()
    check_git_remote()

    config = load_config()
    check_notify_platforms(config.get("noti_pf", []))

    auto_create_and_run_bat(username)

    print("\n🎉 모든 점검 및 설정 완료. 자동화 준비 OK.\n")

if __name__ == "__main__":
    main()
