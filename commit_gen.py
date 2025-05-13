import os
import subprocess
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import importlib
from datetime import datetime
from notify import discord, kakao, gmail, slack
from record import notion

# 🔹 .env 로딩
load_dotenv()

CONFIG_PATH = Path(__file__).parent / "git_config.json"
NOTIFY_MODULES = {
    "discord": discord,
    "kakao": kakao,
    "gmail": gmail,
    "slack": slack
}

def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        exit(1)

def get_git_diff():
    raw_diff = subprocess.run("git diff", shell=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    cleaned_lines = [
        line for line in raw_diff.splitlines()
        if not line.startswith("warning: in the working copy")
    ]
    diff = "\n".join(cleaned_lines).strip()
    if not diff:
        exit(0)
    return diff

def split_diff_by_at_blocks(diff_text: str, max_line_threshold: int = 200, block_size: int = 4):
    lines = diff_text.splitlines()
    if len(lines) <= max_line_threshold:
        return [diff_text]
    block_starts = [i for i, line in enumerate(lines) if line.startswith("@@")]
    if not block_starts:
        return ["\n".join(lines[i:i + max_line_threshold]) for i in range(0, len(lines), max_line_threshold)]
    chunks = []
    block_starts.append(len(lines))
    for i in range(0, len(block_starts) - 1, block_size):
        start, end = block_starts[i], block_starts[min(i + block_size, len(block_starts) - 1)]
        chunk = "\n".join(lines[start:end]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks

def load_prompt(config, purpose):
    lang = config["language"][purpose]
    style = config["style"][purpose]
    prompt_path = Path(config["prompt_style_path"]) / lang / f"{style}.txt"
    return prompt_path.read_text(encoding="utf-8")

def call_llm(prompt, llm_config, llm_param):
    providers = llm_config["provider"]
    models = llm_config["model"]

    for provider, model in zip(providers, models):
        try:
            print(f"\n🌐 [LLM 호출] Provider: {provider.upper()} | Model: {model}")
            llm_module = importlib.import_module(f"llm.{model}")
            response = llm_module.call(prompt, llm_param)
            print(f"✅ [LLM 응답 완료] {model}")
            return response
        except Exception as e:
            print(f"⚠️ [LLM 실패] {model}: {type(e).__name__} - {e}")
            continue

    raise RuntimeError("❌ 모든 LLM 호출 실패")

def do_git_commit(commit_msg):
    try:
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def format_commit_output(msg: str, repo_name: str, status: str = "success") -> str:
    prefix = "✅ Git Push 성공" if status == "success" else "❌ Git Push 실패"
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"""{prefix}\n🕒 {time_str}\n📌 레포: {repo_name}\n\n📝 Commit Message\n{'─'*10}\n"""
    return header + msg.strip() + f"\n{'─'*10}"

def send_notification(platforms, msg, status):
    results = {}
    messages = msg if isinstance(msg, list) else [msg]
    for single_msg in messages:
        for pf in platforms:
            module = NOTIFY_MODULES.get(pf)
            if not module:
                continue
            try:
                success = module.send(single_msg, status)
                results[pf] = success
            except Exception:
                results[pf] = False
    return results

def save_log(config, data, status="success"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("success_logs" if status == "success" else "fail_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{timestamp}.jsonl"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

# 🔹 main 실행부
def main():
    config = load_config()
    change = get_git_diff()
    noti_platforms = config.get("noti_pf", [])
    repo_name = Path.cwd().name

    results = {"commit": [], "record": []}

    for purpose in ["commit", "record"]:
        prompt_template = load_prompt(config, purpose)
        diff_chunks = split_diff_by_at_blocks(change)

        for chunk in diff_chunks:
            chunk_prompt = prompt_template.format(change=chunk)
            llm_param = config["llm_param"][purpose]
            time.sleep(10)  # ← 원하는 초 단위 조절 가능
            response = call_llm(chunk_prompt, config["llm"][purpose], llm_param).strip()
            results[purpose].append(response)

    subprocess.run(["git", "add", "."], check=True)
    combined_commit_msg = "\n\n".join(results["commit"])
    commit_status = do_git_commit(combined_commit_msg)

    status_text = "success" if commit_status else "fail"
    formatted_msgs = [format_commit_output(msg, repo_name, status_text) for msg in results["commit"]]

    # 알림을 개별 메시지로 각각 전송
    send_notification(noti_platforms, formatted_msgs, status_text)

    # Notion 기록도 개별 청크로 업로드
    from record.notion import write_record_to_notion
    for record_chunk in results["record"]:
        write_record_to_notion(record_chunk)

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "commit_msgs": results["commit"],
        "record_msgs": results["record"],
        "status": status_text
    }
    save_log(config, log_data, status_text)

if __name__ == "__main__":
    main()
