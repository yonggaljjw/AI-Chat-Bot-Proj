from django.shortcuts import render
import pandas as pd
from sqlalchemy import create_engine
from chatbot.sql import engine
import json

def get_trend_data():
    # 카테고리 정보 설정
    category_names = {100: "정치", 101: "경제", 102: "사회", 103: "생활/문화", 104: "세계", 105: "IT/과학"}
    optimal_lags = {100: 129, 101: 167, 102: 40, 103: 158, 104: 29, 105: 175}
    
    try:
        # DB 연결 및 데이터 로드
        data = pd.read_sql("SELECT * FROM trend_predictions", engine)
        
        # 각 카테고리별 데이터 처리
        trend_data = {}
        for cat_id, cat_name in category_names.items():
            category_data = data[data['category_id'] == cat_id]
            if not category_data.empty:
                row = category_data.iloc[0]
                trend_data[cat_id] = {
                    'category': cat_name,
                    'predicted_trend': float(f"{row['predicted_trend']:.2f}"),
                    'today_trend': float(f"{row['today_trend']:.2f}"),
                    'lag': optimal_lags[cat_id],
                    'urls': eval(row['urls'])[:5]
                }
        
        return trend_data
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {str(e)}")
        return {}