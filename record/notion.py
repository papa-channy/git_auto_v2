import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import random

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

NOTION_URL_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

# 🎨 파스텔톤 배경 중 랜덤 선택
COLOR_OPTIONS = [
    "gray_background", "brown_background", "orange_background",
    "yellow_background", "green_background", "blue_background",
    "purple_background", "pink_background"
]

def get_repo_name():
    import subprocess
    url = subprocess.run("git config --get remote.origin.url", shell=True, capture_output=True, text=True).stdout.strip()
    return url.rstrip(".git").split("/")[-1] if url else "unknown_repo"

def find_or_create_toggle_block(parent_id, title_text):
    """상위 토글 블록이 존재하는지 확인하고 없으면 생성"""
    search_url = f"{NOTION_URL_BASE}/blocks/{parent_id}/children?page_size=100"
    resp = requests.get(search_url, headers=HEADERS)
    resp.raise_for_status()

    children = resp.json().get("results", [])
    for block in children:
        if block["type"] == "toggle" and \
           block["toggle"]["rich_text"][0]["text"]["content"] == title_text:
            return block["id"]

    # 없으면 생성
    payload = {
        "children": [
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": { "content": title_text }
                        }
                    ],
                    "children": []
                }
            }
        ]
    }
    create_url = f"{NOTION_URL_BASE}/blocks/{parent_id}/children"
    resp = requests.patch(create_url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["results"][0]["id"]

def write_record_to_notion(record_msg: str, index: int = None):
    now = datetime.now()
    now_str = now.strftime("%y/%m/%d %p %I시 %M분").replace("AM", "오전").replace("PM", "오후")

    repo_name = get_repo_name()
    top_toggle_title = f"[{repo_name}]"

    # ✅ 순번 포함된 하위 토글 제목
    if index is not None:
        sub_toggle_title = f"{now_str} {repo_name} 변경사항 ({index + 1})"
    else:
        sub_toggle_title = f"{now_str} {repo_name} 변경사항"

    # 1️⃣ 상위 토글 찾거나 생성
    parent_id = NOTION_PAGE_ID
    top_toggle_id = find_or_create_toggle_block(parent_id, top_toggle_title)

    sub_payload = {
        "children": [
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": { "content": sub_toggle_title }
                        }
                    ],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": { "content": record_msg }
                                    }
                                ],
                                "color": random.choice(COLOR_OPTIONS)
                            }
                        }
                    ]
                }
            }
        ]
    }

    create_url = f"{NOTION_URL_BASE}/blocks/{top_toggle_id}/children"
    try:
        resp = requests.patch(create_url, headers=HEADERS, json=sub_payload)
        resp.raise_for_status()
        return True
    except Exception as e:
        return False
