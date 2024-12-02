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
    # 나라별로 도시 묶기
    country_city_df = df.groupby('나라')['도시명'].apply(list).reset_index()
    country_city_df.rename(columns={'도시명': '도시목록'}, inplace=True)

    # 나라 이름에 "여행" 추가
    country_city_df['나라'] = country_city_df['나라'] + ' 여행'
    return country_city_df

def fetch_monthly_trend_data(country, city_list):
    """네이버 Datalab API에서 월별 트렌드 지수를 가져오는 함수."""
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": naver_client_id,
        "X-Naver-Client-Secret": naver_client_secret,
        "Content-Type": "application/json"
    }
    today = datetime.today()
    start_date = (today.replace(year=today.year - 1)).strftime('%Y-%m-%d')  # 1년 전
    end_date = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')  # 전달 말일

    # 도시 목록을 keywords로 전달 (리스트 형태)
    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "month",
        "keywordGroups": [{"groupName": country, "keywords": city_list}]
    })

    response = requests.post(url, headers=headers, data=body)

    if response.status_code != 200:
        print(f"Error fetching trend data for {country}: {response.status_code} - {response.text}")
        return []

    data = response.json()
    monthly_data = data.get('results', [])

    if monthly_data:
        print(f"Monthly trend data for {country}: {monthly_data[0]['data']}")
    else:
        print(f"No trend data found for {country}")

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
    travel_info_df = create_travel_info()  # 나라와 도시 목록 생성
    filtered_data = []

    for _, row in travel_info_df.iterrows():
        country = row['나라']  # 나라 이름
        city_list = row['도시목록']  # 해당 나라의 도시 목록
        print(f"Analyzing trend for: {country}, {city_list}")

        # 네이버 Datalab API 호출
        monthly_trend_data = fetch_monthly_trend_data(country, city_list)
        if not monthly_trend_data:
            print(f"No trend data for {country}. Skipping...")
            continue

        trend_growth = calculate_average_growth(monthly_trend_data)
        trend_var = calculate_variance_growth(monthly_trend_data)
        trend_cv = calculate_cv_growth(monthly_trend_data)

        monthly_ratios = {entry['period']: entry['ratio'] for entry in monthly_trend_data}

        filtered_data.append({
            'country': country,
            'trend_growth': trend_growth,
            'trend_var': trend_var,
            'trend_cv': trend_cv,
            'monthly_ratios': monthly_ratios
        })

    return filtered_data


def make_final_df():
    rows = []
    data = analyze_articles_with_trends()
    for entry in data:
        country = entry['country']
        trend_growth = entry['trend_growth']
        trend_var = entry['trend_var']
        trend_cv = entry['trend_cv']
        for date, ratio in entry['monthly_ratios'].items():
            rows.append({
                'country': country,
                'trend_growth': trend_growth,
                'trend_var': trend_var,
                'trend_cv': trend_cv,
                'date': date,
                'ratio': ratio
            })

    df = pd.DataFrame(rows)
    # 테이블 1: Countries
    countries_table = df[['country', 'trend_growth', 'trend_var', 'trend_cv']].drop_duplicates()
    countries_table.to_sql('travel_trend_cv', con=engine, if_exists='replace', index=False)  # MySQL에 저장
    print(f"Saved all results to MySQL table 'travel_trend_cv'.")

    # 테이블 2: Trends
    trends_table = df[['country', 'date', 'ratio']]
    trends_table['date'] = pd.to_datetime(trends_table['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    trends_table.to_sql('travel_trend', con=engine, if_exists='replace', index=False)  # MySQL에 저장
    print(f"Saved all results to MySQL table 'travel_trend'.")




# Airflow DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1, 9, 0),  # 12월 1일 9:00으로 설정
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    '08_Travel_naver_search_all',
    default_args=default_args,
    description='Fetch and upload travel data to MySQL',
    schedule_interval='0 9 1 * *',  # 매월 1일 09:00 실행
    catchup=False,
) as dag:

    task = PythonOperator(
        task_id='fetch_and_upload_travel_data',
        python_callable=make_final_df,
        dag=dag,
    )
