"""
experiment_time.py
====================
논문 1용 — 단계별 응답 시간 10회 측정 스크립트

실행:
    cd backend
    source venv/bin/activate
    python experiment_time.py

출력:
    - 10회 측정 결과 표
    - 평균 / 최소 / 최대 / 표준편차
    - 논문에 바로 복붙 가능한 형태
"""

import sys
import time
import json
import statistics
from pathlib import Path

# 경로 설정
BACKEND_ROOT = Path(__file__).parent
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv
load_dotenv(BACKEND_ROOT / ".env")

# ============================================================
# 모듈 import
# ============================================================
print("=" * 70)
print("📚 모듈 로딩 중...")
print("=" * 70)

t_load_start = time.time()

from services.keyword_extractor import extract_keywords
from services.retriever import Retriever
from services.card_generator import generate_cards, load_countries_metadata
from services.lesson_planner import generate_lesson_plan

# Retriever + metadata 로드 (1회만)
print("  → Retriever 초기화 중 (임베딩 모델 + ChromaDB 로드)...")
retriever = Retriever()

print("  → 국가 메타데이터 로드 중...")
metadata = load_countries_metadata(BACKEND_ROOT / "data" / "all_countries.json")

t_load = time.time() - t_load_start
print(f"  ✅ 모듈 로딩 완료 ({t_load:.1f}초)")
print()

# ============================================================
# 실험 설정
# ============================================================
NUM_TRIALS = 10
TEST_QUERY = "종이컵으로 쌓기 놀이를 하면서 균형을 배우는 활동"
TEST_AGE = 4
TEST_DURATION = 40

# ============================================================
# 실험 실행
# ============================================================
print("=" * 70)
print(f"🧪 실험 시작: {NUM_TRIALS}회 반복 측정")
print(f"   쿼리: \"{TEST_QUERY}\"")
print(f"   연령: 만 {TEST_AGE}세 / 시간: {TEST_DURATION}분")
print("=" * 70)
print()

results = []

for trial in range(1, NUM_TRIALS + 1):
    print(f"--- [{trial}/{NUM_TRIALS}] ---")
    trial_result = {}

    try:
        # Stage A: 키워드 추출
        t0 = time.time()
        kw = extract_keywords(
            text=TEST_QUERY,
            age=TEST_AGE,
            duration=TEST_DURATION,
        )
        trial_result["A"] = time.time() - t0
        print(f"  Stage A (키워드 추출): {trial_result['A']:.2f}초")
        print(f"    → search_query: {kw.get('search_query', '?')[:50]}...")

        # Stage B-D: RAG 검색
        t1 = time.time()
        retrieval = retriever.search(kw["search_query"], top_k_countries=3)
        trial_result["BD"] = time.time() - t1
        countries = [c["country"] for c in retrieval["top_countries"]]
        print(f"  Stage B-D (RAG 검색): {trial_result['BD']:.2f}초")
        print(f"    → Top-3: {countries}")

        # Stage E: 카드 3장 생성
        t2 = time.time()
        cards_result = generate_cards(
            user_query=kw["search_query"],
            age=TEST_AGE,
            duration=TEST_DURATION,
            top_countries=retrieval["top_countries"],
            countries_metadata=metadata,
        )
        trial_result["E"] = time.time() - t2
        card_titles = [c.get("card_title", "?") for c in cards_result.get("cards", [])]
        print(f"  Stage E (카드 생성): {trial_result['E']:.2f}초")
        print(f"    → 카드: {card_titles}")

        # Stage F: 지도안 생성
        selected_card = cards_result["cards"][0]  # 첫 번째 카드 선택
        selected_code = selected_card["country_code"]
        country_data = next(
            (c for c in retrieval["top_countries"] if c["country_code"] == selected_code),
            None,
        )

        t3 = time.time()
        lesson_md = generate_lesson_plan(
            user_query=kw["search_query"],
            age=TEST_AGE,
            duration=TEST_DURATION,
            selected_country_code=selected_code,
            selected_card=selected_card,
            country_chunks=country_data["matched_chunks"] if country_data else [],
            country_metadata=metadata[selected_code],
        )
        trial_result["F"] = time.time() - t3
        print(f"  Stage F (지도안 생성): {trial_result['F']:.2f}초")
        print(f"    → 지도안 길이: {len(lesson_md)}자")

        # 전체 시간
        trial_result["total"] = (
            trial_result["A"] + trial_result["BD"] +
            trial_result["E"] + trial_result["F"]
        )
        print(f"  📊 전체: {trial_result['total']:.2f}초")

        trial_result["success"] = True
        results.append(trial_result)

    except Exception as e:
        print(f"  ❌ 에러 발생: {type(e).__name__}: {e}")
        trial_result["success"] = False
        results.append(trial_result)

    print()

    # 503 에러 방지를 위한 딜레이
    if trial < NUM_TRIALS:
        wait = 3
        print(f"  ⏳ {wait}초 대기 (API 한도 보호)...")
        time.sleep(wait)

# ============================================================
# 결과 분석
# ============================================================
print()
print("=" * 70)
print("📊 실험 결과 요약")
print("=" * 70)

# 성공한 것만 필터
success_results = [r for r in results if r.get("success")]
fail_count = len(results) - len(success_results)

if not success_results:
    print("❌ 성공한 실험이 없습니다.")
    sys.exit(1)

print(f"\n성공: {len(success_results)}회 / 실패: {fail_count}회\n")

# 개별 결과 표
print("┌─────┬──────────┬──────────┬──────────┬──────────┬──────────┐")
print("│ 회차 │ Stage A  │ Stage B-D│ Stage E  │ Stage F  │   전체   │")
print("│     │(키워드)  │(RAG검색) │(카드생성)│(지도안)  │          │")
print("├─────┼──────────┼──────────┼──────────┼──────────┼──────────┤")
for i, r in enumerate(success_results, 1):
    print(f"│  {i:2d} │  {r['A']:6.2f}s │  {r['BD']:6.2f}s │  {r['E']:6.2f}s │  {r['F']:6.2f}s │  {r['total']:6.2f}s │")
print("├─────┼──────────┼──────────┼──────────┼──────────┼──────────┤")

# 통계
stages = ["A", "BD", "E", "F", "total"]
stage_names = ["Stage A", "Stage B-D", "Stage E", "Stage F", "전체"]

stats = {}
for stage in stages:
    values = [r[stage] for r in success_results]
    stats[stage] = {
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
    }

print(f"│ 평균 │  {stats['A']['mean']:6.2f}s │  {stats['BD']['mean']:6.2f}s │  {stats['E']['mean']:6.2f}s │  {stats['F']['mean']:6.2f}s │  {stats['total']['mean']:6.2f}s │")
print(f"│ 최소 │  {stats['A']['min']:6.2f}s │  {stats['BD']['min']:6.2f}s │  {stats['E']['min']:6.2f}s │  {stats['F']['min']:6.2f}s │  {stats['total']['min']:6.2f}s │")
print(f"│ 최대 │  {stats['A']['max']:6.2f}s │  {stats['BD']['max']:6.2f}s │  {stats['E']['max']:6.2f}s │  {stats['F']['max']:6.2f}s │  {stats['total']['max']:6.2f}s │")
print(f"│ 표준 │  {stats['A']['stdev']:6.2f}s │  {stats['BD']['stdev']:6.2f}s │  {stats['E']['stdev']:6.2f}s │  {stats['F']['stdev']:6.2f}s │  {stats['total']['stdev']:6.2f}s │")
print("└─────┴──────────┴──────────┴──────────┴──────────┴──────────┘")

# ============================================================
# 논문용 표 (복사 붙여넣기용)
# ============================================================
print()
print("=" * 70)
print("📝 논문용 표 (복사 붙여넣기용)")
print("=" * 70)
print()
print("표 X. 단계별 평균 응답 시간 (N={}회)".format(len(success_results)))
print()
print(f"  Stage A  (키워드 추출)   : 평균 {stats['A']['mean']:.2f}초 (±{stats['A']['stdev']:.2f})")
print(f"  Stage B-D (RAG 검색)     : 평균 {stats['BD']['mean']:.2f}초 (±{stats['BD']['stdev']:.2f})")
print(f"  Stage E  (카드 생성)     : 평균 {stats['E']['mean']:.2f}초 (±{stats['E']['stdev']:.2f})")
print(f"  Stage F  (지도안 생성)   : 평균 {stats['F']['mean']:.2f}초 (±{stats['F']['stdev']:.2f})")
print(f"  ─────────────────────────────────────────")
print(f"  전체 평균                : {stats['total']['mean']:.2f}초 (±{stats['total']['stdev']:.2f})")
print()

# 비율 분석
total_mean = stats['total']['mean']
print("📊 단계별 시간 비율:")
for stage, name in zip(stages[:-1], stage_names[:-1]):
    pct = stats[stage]['mean'] / total_mean * 100
    print(f"  {name}: {pct:.1f}%")

print()
print("=" * 70)
print("✅ 실험 완료")
print("=" * 70)

# JSON으로도 저장
output_path = BACKEND_ROOT / "experiment_time_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({
        "config": {
            "query": TEST_QUERY,
            "age": TEST_AGE,
            "duration": TEST_DURATION,
            "num_trials": NUM_TRIALS,
        },
        "results": results,
        "stats": stats,
    }, f, ensure_ascii=False, indent=2)

print(f"\n💾 결과 JSON 저장: {output_path}")
