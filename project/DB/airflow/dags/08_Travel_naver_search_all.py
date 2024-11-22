import os
import urllib.request
import json
import pandas as pd
from datetime import datetime, timedelta
import requests
import numpy as np

from airflow import DAG
from airflow.operators.python import PythonOperator
import pymysql
from sqlalchemy import create_engine

from dotenv import load_dotenv


# 환경 변수 로드
load_dotenv()

# MySQL 연결 정보 설정
username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")

naver_client_id = os.getenv("eunji_naver_api")
naver_client_secret = os.getenv("eunji_naver_api_key")

def create_travel_info():
    df = pd.read_csv("./dags/package/국토연구원 세계도시정보 자료(2019년).csv", encoding="EUC-KR")
    group_names = []
    for _, row in df.iterrows():
        city = row['도시명']
        group_name = f"{city} 여행"
        group_names.append(group_name)
    return group_names

def fetch_monthly_trend_data(word):
    """네이버 Datalab API에서 월별 트렌드 지수를 가져오는 함수."""
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": naver_client_id,
        "X-Naver-Client-Secret": naver_client_secret,
        "Content-Type": "application/json"
    }
    today = datetime.today()
    start_date = (today.replace(year=today.year - 1)).strftime('%Y-%m-%d')  # 1년 전
    end_date = today.strftime('%Y-%m-%d')  # 오늘

    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "month",
        "keywordGroups": [{"groupName": word, "keywords": [word]}]
    })

    response = requests.post(url, headers=headers, data=body)
    
    if response.status_code != 200:
        print(f"Error fetching trend data for {word}: {response.status_code}")
        return []

    data = response.json()
    monthly_data = data.get('results', [])
    
    if monthly_data:
        print(f"Monthly trend data for {word}: {monthly_data[0]['data']}")
    else:
        print(f"No trend data found for {word}")
    
    return monthly_data[0]['data'] if monthly_data else []

def calculate_average_growth(trend_data):
    """트렌드 지수의 평균 증감율을 계산하는 함수."""
    if not trend_data or len(trend_data) < 2:
        return 0  # 데이터가 부족하면 0%로 처리
    
    growth_rates = []
    for i in range(1, len(trend_data)):
        prev_ratio = trend_data[i - 1]['ratio']
        current_ratio = trend_data[i]['ratio']
        growth_rate = ((current_ratio - prev_ratio) / prev_ratio) * 100 if prev_ratio != 0 else 0

        growth_rates.append(growth_rate)
    
    average_growth_rate = sum(growth_rates) / len(growth_rates)
    return average_growth_rate

def calculate_variance_growth(trend_data):
    """트렌드 지수 변화율의 분산을 계산하는 함수."""
    if not trend_data or len(trend_data) < 2:
        return 0  # 데이터가 부족하면 0으로 처리

    growth_rates = []
    for i in range(1, len(trend_data)):
        prev_ratio = trend_data[i - 1]['ratio']
        current_ratio = trend_data[i]['ratio']
        # 변화율 계산 (현재값 / 이전값)
        growth_rate = (current_ratio / prev_ratio) if prev_ratio != 0 else 1
        growth_rates.append(growth_rate)
    
    # 변화율의 분산 계산
    variance_growth_rate = np.var(growth_rates)
    return variance_growth_rate

def calculate_cv_growth(trend_data):
    """트렌드 지수 변화율의 변동계수(CV)를 계산하는 함수."""
    if not trend_data or len(trend_data) < 2:
        return 0  # 데이터 부족 시 0 반환

    growth_rates = []
    for i in range(1, len(trend_data)):
        prev_ratio = trend_data[i - 1]['ratio']
        current_ratio = trend_data[i]['ratio']
        # 변화율 계산 (현재값 / 이전값)
        growth_rate = (current_ratio / prev_ratio) if prev_ratio != 0 else 1
        growth_rates.append(growth_rate)

    # 평균 및 표준편차 계산
    mean_growth = np.mean(growth_rates)
    std_growth = np.std(growth_rates)
    
    # 변동계수 계산
    cv = std_growth / mean_growth if mean_growth != 0 else 0
    return cv

def analyze_articles_with_trends():
    """기사 분석 후 네이버 Datalab API를 사용해 트렌드 증가율을 포함한 데이터를 생성."""
    words = create_travel_info()
    filtered_data = []
    trend_data = {}  # 트렌드 데이터 저장
    for word in words:  # 상위 15개 키워드만 처리
        print(f"Analyzing trend for word: {word}")
        # 네이버 Datalab API로 현재 검색량과 월별 트렌드 지수 가져오기
        monthly_trend_data = fetch_monthly_trend_data(word)
        if not monthly_trend_data:
            trend_growth = 0  # 트렌드 데이터가 없으면 증가율 0%
        else:
            trend_growth = calculate_average_growth(monthly_trend_data)
            trend_var = calculate_variance_growth(monthly_trend_data)
            trend_cv = calculate_cv_growth(monthly_trend_data)
        # 월별 ratio 저장
        monthly_ratios = {entry['period']: entry['ratio'] for entry in monthly_trend_data}
        
        filtered_data.append({
            'word': word,
            'trend_growth': trend_growth,
            'trend_var' : trend_var,
            'trend_cv':trend_cv,
            'monthly_ratios': monthly_ratios,  # 월별 ratio 추가
        })

    return filtered_data

def make_final_df():
    rows = []
    data = analyze_articles_with_trends()
    for entry in data:
        word = entry['word']
        trend_growth = entry['trend_growth']
        trend_var = entry['trend_var']
        trend_cv = entry['trend_cv']
        for date, ratio in entry['monthly_ratios'].items():
            rows.append({'word': word, 'trend_growth': trend_growth,'trend_var':trend_var, 'trend_cv':trend_cv, 'date': date, 'ratio': ratio})

    df = pd.DataFrame(rows)
    # 테이블 1: Words
    words_table = df[['word', 'trend_growth', 'trend_var', 'trend_cv']].drop_duplicates()
    words_table.to_sql('travel_trend_cv', con=engine, if_exists='replace', index=False) # mysql에 저장
    print(f"Saved all results to MySQL table 'travel_trend_cv'.")

    # 테이블 2: Trends
    trends_table = df[['word', 'date', 'ratio']]
    trends_table['date'] = pd.to_datetime(trends_table['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    trends_table.to_sql('travel_trend', con=engine, if_exists='replace', index=False) # mysql에 저장
    print(f"Saved all results to MySQL table 'travel_trend'.")
###



# Airflow DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.now(),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    '08_Travel_naver_search_all',
    default_args=default_args,
    description='Fetch and upload travel data to MySQL',
    schedule_interval=None,
    catchup=False,
) as dag:

    # Airflow Operator로 함수 실행
    task = PythonOperator(
        task_id='fetch_and_upload_travel_data',
        python_callable=make_final_df,
        dag=dag,
    )

    task
