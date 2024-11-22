from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import pymysql
import requests
from sqlalchemy import create_engine


load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
apikey = os.getenv('ECOS_KEY')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")

date = datetime.today().strftime('%Y%m%d')

def extract_currency_rate() :
    # 달러
    url = f'https://ecos.bok.or.kr/api/StatisticSearch/{apikey}/json/kr/1/10000/731Y001/D/{date}/{date}/0000001'
    response = requests.get(url).json()
    df1 = pd.DataFrame(response['StatisticSearch']['row'])[['TIME','DATA_VALUE']]
    df1 = df1.rename(columns={'DATA_VALUE' : 'USD'})

    # 위안
    url = f'https://ecos.bok.or.kr/api/StatisticSearch/{apikey}/json/kr/1/10000/731Y001/D/{date}/{date}/0000053'
    response = requests.get(url).json()
    df2 = pd.DataFrame(response['StatisticSearch']['row'])[['TIME','DATA_VALUE']]
    df2 = df2.rename(columns={'DATA_VALUE' : 'CNY'})

    # 엔화
    url = f'https://ecos.bok.or.kr/api/StatisticSearch/{apikey}/json/kr/1/10000/731Y001/D/{date}/{date}/0000002'
    response = requests.get(url).json()
    df3 = pd.DataFrame(response['StatisticSearch']['row'])[['TIME','DATA_VALUE']]
    df3 = df3.rename(columns={'DATA_VALUE' : 'JPY'})

    # 유로
    url = f'https://ecos.bok.or.kr/api/StatisticSearch/{apikey}/json/kr/1/10000/731Y001/D/{date}/{date}/0000003'
    response = requests.get(url).json()
    df4 = pd.DataFrame(response['StatisticSearch']['row'])[['TIME','DATA_VALUE']]
    df4 = df4.rename(columns={'DATA_VALUE' : 'EUR'})

    df = pd.merge(df1,df2, on='TIME')
    df = pd.merge(df,df3, on='TIME', how='left')
    df = pd.merge(df,df4, on='TIME', how='left')
    df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m%d')

    return df


def upload_currency_rate() :
    df = extract_currency_rate()

    df.to_sql('currency_rate', con=engine, if_exists='append', index=False)


# Airflow DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retries': 5,
    'retry_delay': timedelta(hours=1),
}

# DAG 정의
with DAG(
    '04_currency_rate_data',
    default_args=default_args,
    description="환율데이터를 수집하여 적재합니다.",
    schedule_interval='@daily',
    start_date=datetime(2010, 1, 1),
    catchup=False,
    tags=['Mysql', 'currency', 'data']
) as dag:
    
    # PythonOperator 설정
    t1 = PythonOperator(
    task_id="currency_rate_upload",
    python_callable=upload_currency_rate,
    )

    t1