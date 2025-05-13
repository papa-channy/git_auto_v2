import os
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 🔹 .env 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

API_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"

# 🔐 .env 값
ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("KAKAO_REFRESH_TOKEN")
CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")

# 🔧 공통 헤더 함수 (동적 업데이트 지원)
def build_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

# 🔧 토큰 갱신
def refresh_access_token() -> str:
    if not CLIENT_ID or not REFRESH_TOKEN:
        return None

    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": REFRESH_TOKEN
    }

    try:
        resp = requests.post(TOKEN_URL, data=data, timeout=5)
        resp.raise_for_status()
        new_token = resp.json().get("access_token")
        if new_token:
            _update_env_token(new_token)
            return new_token
    except Exception as e:
        print(f"[KAKAO] ❌ 토큰 갱신 실패: {e}")
    return None

# 🔧 .env 파일 업데이트
def _update_env_token(new_token):
    lines = []
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("KAKAO_ACCESS_TOKEN="):
                lines.append(f"KAKAO_ACCESS_TOKEN={new_token}\n")
            else:
                lines.append(line)

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    os.environ["KAKAO_ACCESS_TOKEN"] = new_token  # 세션 반영도 함께

# 🔧 JSON 문자열로 변환
def json_string(obj):
    return json.dumps(obj, ensure_ascii=False)

# 🔔 알림 전송 (내부 재시도 포함)
def _send_msg(token: str, msg: str) -> bool:
    headers = build_headers(token)
    template = {
        "object_type": "text",
        "text": msg,
        "link": {
            "web_url": "https://github.com",
            "mobile_web_url": "https://github.com"
        }
    }
    try:
        data = { "template_object": json_string(template) }
        resp = requests.post(API_URL, headers=headers, data=data, timeout=5)
        if resp.status_code == 401:
            print("[KAKAO] ❗ 토큰 만료로 인해 401 반환됨")
            return False
        return resp.status_code == 200 and resp.json().get("result_code") == 0
    except Exception as e:
        print(f"[KAKAO] ❌ 전송 실패: {e}")
        return False

# ✅ 최종 공개 함수
def send(commit_msg: str, status: str = "success") -> bool:
    global ACCESS_TOKEN
    if not ACCESS_TOKEN:
        print("[KAKAO] ❌ ACCESS_TOKEN 없음")
        return False

    prefix = "✅ Git Push 성공" if status == "success" else "❌ Git Push 실패"
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    full_msg = f"{prefix}\n🕒 {time_str}\n\n📝 Commit Message:\n{commit_msg}"

    # 1차 시도
    success = _send_msg(ACCESS_TOKEN, full_msg)
    if success:
        print("[KAKAO] ✅ 메시지 전송 성공")
        return True

    # 실패 시 토큰 갱신 & 재시도
    new_token = refresh_access_token()
    if not new_token:
        return False
    return _send_msg(new_token, full_msg)

# ping 함수 (테스트용)
def ping() -> bool:
    test_msg = "✅ [Ping 테스트] 카카오 알림 연결 성공"
    return _send_msg(ACCESS_TOKEN, test_msg)
