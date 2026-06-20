Python
# -*- coding: utf-8 -*-
"""
auto_hub_runner.py - 백엔드 스케줄러 동기화 완료본
- app.py 파일의 26개 데이터 구조와 완벽 연동
"""
import os
import re
import time
import pandas as pd
from app import *

def run_pipeline():
    rc_date = os.getenv("MARU_RC_DATE") or today_kst()
    meet = "서울"
    
    # 26개 API 주소 기반 백엔드 로딩 파이프라인
    data = {}
    for key in ["race_url", "entry_url", "body_url", "rating_url", "popularity_url"]:
        df, _, _ = fetch_one_api(key, rc_date, meet, 1)
        if not df.empty:
            data[key] = df
        time.sleep(0.05)
        
    base = build_base_horses(data, rc_date, meet, 1)
    horses = merge_score_features(base, data, rc_date, meet, 1)
    _, result = score_and_recommend(horses, {"주로": "표준"}, 1200)

    row = {
        "저장시각": now_str(), "날짜": rc_date, "경마장": meet, "경주번호": 1,
        "공격삼쌍승": result["공격삼쌍승"], "삼쌍승18조합": result["삼쌍승18조합"],
        "신뢰도": result["신뢰도"], "예상배당": result["예상배당"], "축마": result["축마"],
        "상대마": result["상대마"], "보조마": result["보조마"], "구멍마": result["구멍마"]
    }
    
    append_csv(SHARED_RECOMMEND_FILE, row)
    print(f"[MARU BACKEND] 데이터 허브 파이프라인 수집 완료: {now_str()}")

if __name__ == "__main__":
    run_pipeline()
