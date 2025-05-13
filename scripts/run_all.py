import time
from datetime import datetime
import json
from pathlib import Path
import shutil

from scripts.context import build_context
from scripts.diff import get_git_diff, split_diff_by_function
from scripts.commit import generate_commit_and_record
from scripts.cost_calc import calculate_llm_costs
from scripts.classify import classify_for_notify, classify_for_record, classify_for_git
from scripts.upload import do_git_commit, send_notification, write_records

LOG_DIR = Path("logs/scr")
LOG_DIR.mkdir(parents=True, exist_ok=True)
now_str = datetime.now().strftime("%Y%m%d_%H%M")
LOG_PATH = LOG_DIR / f"{now_str}.log"

def log(msg: str):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M')}] {msg.strip()}\n")

def load_config() -> dict:
    with open("config/llm.json", "r", encoding="utf-8") as f1, \
         open("config/style.json", "r", encoding="utf-8") as f2, \
         open("config/noti.json", "r", encoding="utf-8") as f3, \
         open("config/cost.json", "r", encoding="utf-8") as f4:
        return {
            "llm": json.load(f1),
            "style": json.load(f2)["style"],
            "lang": json.load(f2)["language"],
            "noti": json.load(f3),
            "cost": json.load(f4)
        }
def clear_repo_cache():
    cache_txt = Path("logs/cache.txt")
    if not cache_txt.exists():
        cache_txt.write_text("20", encoding="utf-8")

    try:
        count = int(cache_txt.read_text().strip())
    except:
        count = 20  # 잘못된 값일 경우 초기화

    if count > 1:
        cache_txt.write_text(str(count - 1), encoding="utf-8")
        return  # 아직 정리 주기가 아님

    # ✅ 캐시 정리 시점 도달 → 정리 실행
    paths_to_remove = [
        Path("logs/fail"),
        Path("logs/scr"),
        Path("utils/temp"),
        Path("cache")
    ]

    for path in paths_to_remove:
        if path.exists():
            shutil.rmtree(path)

    for path in Path(".").rglob("*"):
        if path.name == "__pycache__" and path.is_dir():
            shutil.rmtree(path)
        elif path.suffix == ".pyc":
            try:
                path.unlink()
            except:
                pass

    cache_txt.write_text("20", encoding="utf-8")
    print("🧹 캐시 정리 완료 → 주기 초기화됨")



def dynamic_sleep(prompts: dict, base=5, per_1000=2):
    total_chars = sum(len(v["text"]) for v in prompts.values())
    est = base + (total_chars / 1000) * per_1000
    sleep_time = max(round(est), base)
    log(f"⏱ LLM 부하 완화 - {sleep_time}s sleep...")
    time.sleep(sleep_time)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    clear_repo_cache()

    config = load_config()
    log(f"🚀 자동 실행 시작 - {timestamp}")
    config = load_config()
    log(f"🚀 자동 실행 시작 - {timestamp}")

    # 1. context
    context_summary, prompt_vars_ctx = build_context(
        log,
        timestamp,
        config["llm"]["summary"],
        config["llm"]["global_context"]
    )

    # 2. diff
    diff_text = get_git_diff(log)
    diff_chunks = split_diff_by_function(diff_text, timestamp, log)

    # 3. commit + record
    commit_chunks, final_msg, record_msg, prompt_vars_commit = generate_commit_and_record(
        diff_chunks,
        context_summary,
        config["llm"]["commit_chunk"],
        config["llm"]["commit_final"],
        config["llm"]["record"],
        config["style"],
        config["lang"],
        log
    )

    # 4. sleep for LLM 안정화
    all_prompts = {**prompt_vars_ctx, **prompt_vars_commit}
    dynamic_sleep(all_prompts)

    # 5. 비용 계산
    df_cost = calculate_llm_costs(all_prompts, timestamp, log)
    cost_summary = df_cost[["model", "input_tokens", "output_tokens", "krw"]].groupby("model").sum()
    cost_summary_msg = cost_summary.to_string()

    # 6. classify
    git_msg = classify_for_git(final_msg)
    notify_msgs = classify_for_notify(commit_chunks, final_msg, context_summary, "pending", cost_summary_msg)
    record_msgs = classify_for_record(context_summary, commit_chunks, record_msg)

    # 7. Git commit
    commit_status = "success" if do_git_commit(git_msg) else "fail"
    notify_msgs[3] = f"📤 Git Push 상태: {'✅ 성공' if commit_status == 'success' else '❌ 실패'}"

    # 8. upload
    send_notification(config["noti"]["noti_pf"], notify_msgs)
    write_records(config["noti"]["record_pf"], record_msgs)

    log("✅ run_all.py 전체 실행 완료")

if __name__ == "__main__":
    main()
