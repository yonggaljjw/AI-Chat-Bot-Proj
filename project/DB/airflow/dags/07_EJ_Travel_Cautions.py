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
    url = "https://www.0404.go.kr/dev/country.mofa?idx=&hash=&chkvalue=no1&stext=&group_idx="
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    advice_levels = ["Travel_Caution", "Travel_Restriction", "Departure_Advisory", "Travel_Ban", "Special_Travel_Advisory"]
    data = []
    countries = soup.select("ul.country_list > li")
    for country in countries:
        country_name = country.select_one("a").text.strip()
        img_tags = country.select("img")
        travel_advice = [img["alt"].strip() for img in img_tags if img.get("alt")]
        advice_flags = {level: True if level in travel_advice else False for level in advice_levels}
        advice_flags = {"Country": country_name, **advice_flags}
        data.append(advice_flags)
    return pd.DataFrame(data)

def upload_data():
    df = fetch_data()
    df.to_sql('travel_cautions', con=engine, if_exists='replace', index=False)
    print(f"{len(df)}개의 데이터를 MySQL에 업로드했습니다.")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 11, 13),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "EJ_Travel_Cautions",
    default_args=default_args,
    description="Fetch and upload travel cautions daily",
    schedule_interval="0 0 * * *",
    catchup=False,
) as dag:

    upload_data_task = PythonOperator(
        task_id="upload_data",
        python_callable=upload_data
    )

    upload_data_task
