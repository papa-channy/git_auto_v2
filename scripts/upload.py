import subprocess
from notify import discord, gmail, kakao, slack
from record import notion, google_drive

# ─────────────────────────────
# 🔼 Git commit & push
# ─────────────────────────────
def do_git_commit(commit_msg: str) -> bool:
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# ─────────────────────────────
# 📤 알림 플랫폼 전송
# ─────────────────────────────
def send_notification(platforms: list[str], messages: list[str]):
    for platform in platforms:
        for msg in messages:
            try:
                if platform == "discord":
                    discord.send(msg)
                elif platform == "gmail":
                    gmail.send(msg)
                elif platform == "kakao":
                    kakao.send(msg)
                elif platform == "slack":
                    slack.send(msg)
            except Exception as e:
                print(f"[ERROR] {platform} 알림 실패: {e}")

# ─────────────────────────────
# 📝 기록 플랫폼 전송
# ─────────────────────────────
def write_records(platforms: list[str], messages: list[str]):
    for platform in platforms:
        try:
            if platform == "notion":
                notion.send(messages)
            elif platform == "google_drive":
                google_drive.send(messages)
            elif platform == "slack":
                slack.send("\n\n".join(messages))  # 기록용은 묶어서 전송
        except Exception as e:
            print(f"[ERROR] {platform} 기록 실패: {e}")
