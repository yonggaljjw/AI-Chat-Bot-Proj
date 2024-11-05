
from datetime import datetime, timedelta
import pandas as pd
from fredapi import Fred
import eland as ed
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

load_dotenv()

fred = Fred(api_key=os.getenv('FRED_API_KEY'))

# 현재 날짜를 end_date로 사용
end_date = datetime.today().strftime('%Y-%m-%d')

# 데이터 가져오기 함수
def fetch_data(series_id, start_date='2015-01-01', end_date=end_date):
    try:
        data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
        return data
    except ValueError as e:
        print(f"Error fetching data for {series_id}: {e}")
        return None

# 데이터프레임 생성 함수
def make_df():
    data_frames = {
        'FFTR': fetch_data('DFEDTARU'),
        'GDP': fetch_data('GDP'),
        'GDP Growth Rate': fetch_data('A191RL1Q225SBEA'),
        'PCE': fetch_data('PCE'),
        'Core PCE': fetch_data('PCEPILFE'),
        'CPI': fetch_data('CPIAUCSL'),
        'Core CPI': fetch_data('CPILFESL'),
        'Personal Income': fetch_data('PI'),
        'Unemployment Rate': fetch_data('UNRATE'),
        'ISM Manufacturing': fetch_data('MANEMP'),
        'Durable Goods Orders': fetch_data('DGORDER'),
        'Building Permits': fetch_data('PERMIT'),
        'Retail Sales': fetch_data('RSAFS'),
        'Consumer Sentiment': fetch_data('UMCSENT'),
        'Nonfarm Payrolls': fetch_data('PAYEMS'),
        'JOLTS Hires': fetch_data('JTSHIL')
    }

    df = pd.DataFrame()
    for key, value in data_frames.items():
        if value is not None:
            temp_df = value.reset_index()
            temp_df.columns = ['date', key]
            if df.empty:
                df = temp_df
            else:
                df = pd.merge(df, temp_df, on='date', how='outer')
    
    df.sort_values(by='date', inplace=True)
    df.fillna(method='ffill', inplace=True)
    
    return df


es = Elasticsearch('http://host.docker.internal:9200')

try:
    es.indices.create(index='fred_data')
except Exception as e:
    print(f"Index creation error: {e}")

# 데이터프레임을 Elasticsearch로 전송하는 함수
def dataframe_to_elasticsearch():
    df = make_df()
    ed.pandas_to_eland(
        pd_df=df,
        es_client=es,
        es_dest_index="fred_data",
        es_if_exists="append",
        es_refresh=True
    )

# Airflow 기본 설정
default_args = {
    'depends_on_past': False,
    'retires': 1,
    'retry_delay': timedelta(minutes=5)
}

# DAG 정의
with DAG(
    'fred_uploader_elasticsearch_v2',
    default_args=default_args,
    description="연준 데이터를 Elasticsearch에 업로드합니다.",
    schedule_interval='@daily',
    start_date=datetime(2015, 1, 1),
    catchup=False,
    tags=['elasticsearch', 'fred', 'data']
) as dag:
    
    # PythonOperator 설정
    t1 = PythonOperator(
        task_id="upload_fred_data_to_elasticsearch",
        python_callable=dataframe_to_elasticsearch,
    )

    t1
