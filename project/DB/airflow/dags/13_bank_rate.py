import os
import numpy as np
from dotenv import load_dotenv
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import pymysql
import requests
from sqlalchemy import create_engine

load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")
apikey = os.getenv('CARD_API')
today = datetime.today()

def extract_rate() :
    today = datetime.today().strftime('%Y%m%d') 
    url = f'https://ecos.bok.or.kr/api/StatisticSearch/{apikey}/json/kr/1/4000/722Y001/D/{today}/{today}/0101000/'

    response = requests.get(url)
    try :
        result = response.json()

        df = pd.DataFrame(result['StatisticSearch']['row'])[['TIME','DATA_VALUE']]
        df = df.rename(columns = {'DATA_VALUE' : 'BOR'})
        df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
        df['BOR'] = df['BOR'].astype('float')
        
    except :
        df = pd.DataFrame({'TIME' : [datetime.todayr()],'BOR':[np.nan]})
        df['TIME'] = pd.to_datetime(df['TIME'], fomat='%Y%m%d')

    return df



def upload_data() :
    df = extract_rate()

    df.to_sql('korea_base_rate', con=engine, if_exists='append', index=False)



# Airflow DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 5,
    'retry_delay': timedelta(hours=1),
}

with DAG(
    '01_Fred_Data',
    default_args=default_args,
    description="미 연준 데이터를 업로드 합니다.",
    schedule_interval='@daily',
    start_date=datetime(2015, 1, 1),
    catchup=False,
    tags=['Opensearch', 'fred', 'data']
) as dag :
    t1 = PythonOperator(
        task_id='create_index_and_mapping',
        python_callable=upload_data
    )
    
    t1