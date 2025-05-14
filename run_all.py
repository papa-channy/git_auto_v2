import time, json, sys, shutil
from datetime import datetime
from pathlib import Path

# 🔧 루트 경로 기준 통일
ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
LOG_DIR = ROOT / "logs" / "scr"
CACHE_PATH = ROOT / "logs" / "cache.txt"

# ✅ sys.path에 scripts 모듈 경로 추가
sys.path.append(str(ROOT / "scripts"))

from scripts.context import build_context
from scripts.diff import get_git_diff, split_diff_by_function
from scripts.commit import generate_commit_and_record
from scripts.cost_calc import calculate_llm_costs
from scripts.classify import classify_for_notify, classify_for_record, classify_for_git
from scripts.upload import do_git_commit, send_notification, write_records

# 🔧 로그 디렉토리 생성
LOG_DIR.mkdir(parents=True, exist_ok=True)
now_str = datetime.now().strftime("%Y%m%d_%H%M")
LOG_PATH = LOG_DIR / f"{now_str}.log"

def log(msg: str):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M')}] {msg.strip()}\n")

def load_config() -> dict:
    with open(CONFIG_DIR / "llm.json", "r", encoding="utf-8") as f1, \
         open(CONFIG_DIR / "style.json", "r", encoding="utf-8") as f2, \
         open(CONFIG_DIR / "noti.json", "r", encoding="utf-8") as f3, \
         open(CONFIG_DIR / "cost.json", "r", encoding="utf-8") as f4:

        style_cfg = json.load(f2)
        return {
            "llm": json.load(f1)["llm"],
            "style": style_cfg["style"],
            "lang": style_cfg["language"],
            "noti": json.load(f3),
            "cost": json.load(f4)
        }

def clear_repo_cache():
    if not CACHE_PATH.exists():
        CACHE_PATH.write_text("20", encoding="utf-8")

    try:
        count = int(CACHE_PATH.read_text().strip())
    except:
        count = 20

    if count > 1:
        CACHE_PATH.write_text(str(count - 1), encoding="utf-8")
        return

    # 캐시 정리 경로들
    paths_to_remove = [
        ROOT / "logs" / "fail",
        ROOT / "logs" / "scr",
        ROOT / "utils" / "temp",
        ROOT / "cache"
    ]

    for path in paths_to_remove:
        if path.exists():
            shutil.rmtree(path)

    for path in ROOT.rglob("*"):
        if path.name == "__pycache__" and path.is_dir():
            shutil.rmtree(path)
        elif path.suffix == ".pyc":
            try:
                path.unlink()
            except:
                pass

    CACHE_PATH.write_text("20", encoding="utf-8")
    print("🧹 캐시 정리 완료 → 주기 초기화됨")

def dynamic_sleep(prompts: dict, base=7, per_1000=2):
    total_chars = 0
    for v in prompts.values():
        if isinstance(v, dict) and "text" in v:
            total_chars += len(v["text"])
    est = base + (total_chars / 1000) * per_1000
    sleep_time = max(round(est), base)
    log(f"⏱ LLM 부하 완화 - {sleep_time}s sleep...")
    time.sleep(sleep_time)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    clear_repo_cache()

    config = load_config()
    style_cfg = config["style"]
    lang_cfg = config["lang"]
    log(f"🚀 자동 실행 시작 - {timestamp}")

    # 1️⃣ 전체 레포 컨텍스트 요약
    context_summary, prompt_vars_ctx = build_context(
        log,
        timestamp,
        config["llm"]["summary"],
        config["llm"]["global_context"]
    )

    # 2️⃣ Git diff 및 청크 분리
    diff_text = get_git_diff(log)
    diff_chunks = split_diff_by_function(diff_text, timestamp, log)

    # 3️⃣ Commit 메시지 생성 + 기록용 메시지 생성
    commit_chunks, final_msg, record_msg, prompt_vars_commit = generate_commit_and_record(
        diff_chunks,
        context_summary,
        config["llm"]["commit_chunk"],
        config["llm"]["commit_final"],
        config["llm"]["record"],
        style_cfg,
        lang_cfg,
        log
    )

    # 4️⃣ LLM 호출 안정화를 위한 딥 슬립
    all_prompts = {**prompt_vars_ctx, **prompt_vars_commit}
    dynamic_sleep(all_prompts)

    # 5️⃣ 비용 계산 및 요약 메시지
    df_cost = calculate_llm_costs(all_prompts, timestamp, log)
    cost_summary = df_cost[["model", "input_tokens", "output_tokens", "krw"]].groupby("model").sum()
    cost_summary_msg = cost_summary.to_string()

    # 6️⃣ 목적별 메시지 분기
    git_msg = classify_for_git(final_msg)
    notify_msgs = classify_for_notify(commit_chunks, final_msg, context_summary, "pending", cost_summary_msg)
    record_msgs = classify_for_record(context_summary, commit_chunks, record_msg)

    # 7️⃣ Git 커밋 실행
    commit_status = "success" if do_git_commit(git_msg) else "fail"
    notify_msgs[3] = f"📤 Git Push 상태: {'✅ 성공' if commit_status == 'success' else '❌ 실패'}"

    # 8️⃣ 알림 전송 + 기록 업로드
    send_notification(config["noti"]["noti_pf"], notify_msgs)
    write_records(config["noti"]["record_pf"], record_msgs)

    log("✅ run_all.py 전체 실행 완료")


if __name__ == "__main__":
    main()
