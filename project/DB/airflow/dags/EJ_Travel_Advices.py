from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pymysql

# Load environment variables
load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")

def fetch_data():
    # 페이지 URL
    url = "https://www.0404.go.kr/dev/country.mofa?idx=&hash=&chkvalue=no1&stext=&group_idx="

    # 페이지 요청
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # 데이터 수집
    data = []
    countries = soup.select("ul.country_list > li")

    for country in countries:
        country_name = country.select_one("a").text.strip()
        img_tags = country.select("img")
        travel_advice = [img["alt"].strip() for img in img_tags if img.get("alt")]  # alt 속성이 있는 경우에만 추가
        travel_advice = ", ".join(travel_advice) if travel_advice else "정보 없음"  # alt 속성이 없으면 "정보 없음"
        data.append([country_name, travel_advice])

    # 데이터프레임 생성
    df = pd.DataFrame(data, columns=["Country", "Travel_Advice"])
    return df

def upload_data():
    df = fetch_data()
    df.to_sql('travel_advices', con=engine, if_exists='replace', index=False)
    print(f"{len(df)}개의 데이터를 MySQL에 업로드했습니다.")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 11, 13),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "EJ_Travel_Advices",
    default_args=default_args,
    description="Fetch and upload travel Advice daily",
    schedule_interval="0 0 * * *",
    catchup=False,
) as dag:

    upload_data_task = PythonOperator(
        task_id="upload_data",
        python_callable=upload_data
    )

    upload_data_task