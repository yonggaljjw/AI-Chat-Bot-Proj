from datetime import datetime, timedelta
from tqdm import tqdm
import requests
import pandas as pd
from dotenv import load_dotenv
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import pymysql
from sqlalchemy import create_engine


load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')

engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")

url = 'https://www.koreaexim.go.kr/site/program/financial/exchangeJSON'
authkey = os.getenv('cur_authkey')
data = 'AP01'
date = datetime.today().strftime('%Y-%m-%d')

def extract_currency_rate() :
    params = {
        'authkey': authkey,
        'searchdate' : date,
        'data' : data}
    
    response = pd.DataFrame(requests.get(url, params=params, verify=False).json())
    response['date'] = date
    response = response.drop(columns=['result'])

    response['ttb'] = response['ttb'].apply(lambda x : x.replace(",",""))
    response['tts'] = response['tts'].apply(lambda x : x.replace(",",""))
    response['deal_bas_r'] = response['deal_bas_r'].apply(lambda x : x.replace(",",""))
    response['bkpr'] = response['bkpr'].apply(lambda x : x.replace(",",""))
    response['kftc_bkpr'] = response['kftc_bkpr'].apply(lambda x : x.replace(",",""))
    response['kftc_deal_bas_r'] = response['kftc_deal_bas_r'].apply(lambda x : x.replace(",",""))

    response['date'] = pd.to_datetime(response['date'], format='%Y-%m-%d')
    response['ttb'] = response['ttb'].astype('float')
    response['tts'] = response['tts'].astype('float')
    response['deal_bas_r'] = response['deal_bas_r'].astype('float')
    response['bkpr'] = response['bkpr'].astype('float')
    response['yy_efee_r'] = response['yy_efee_r'].astype('float')
    response['ten_dd_efee_r'] = response['ten_dd_efee_r'].astype('float')
    response['kftc_bkpr'] = response['kftc_bkpr'].astype('float')
    response['kftc_deal_bas_r'] = response['kftc_deal_bas_r'].astype('float')

    return response

def upload_currency_rate() :
    df = extract_currency_rate()

    df.to_sql('currency_rate', con=engine, if_exists='append', index=False)


# Airflow DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
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