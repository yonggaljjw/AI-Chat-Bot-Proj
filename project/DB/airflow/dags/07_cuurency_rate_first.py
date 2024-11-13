from datetime import datetime, timedelta
from tqdm import tqdm
import requests
import pandas as pd
from dotenv import load_dotenv
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from opensearchpy import OpenSearch
import opensearch_py_ml as oml


load_dotenv()


host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))

url = 'https://www.koreaexim.go.kr/site/program/financial/exchangeJSON'
authkey = os.getenv("cur_authkey")
data = 'AP01'

def extract_currency_rate() :
    df = pd.DataFrame(columns = ['result', 'cur_unit', 'ttb', 'tts', 'deal_bas_r', 'bkpr', 'yy_efee_r',
                             'ten_dd_efee_r', 'kftc_bkpr', 'kftc_deal_bas_r', 'cur_nm','date'])
    params = {
        'authkey': authkey,
        'searchdate' : datetime.today(),
        'data' : data}
    response = pd.DataFrame(requests.get(url, params=params).json())
    response['date'] = datetime.today()
    return response

def dataframe_to_elasticsearch():

    df = extract_currency_rate()

    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="currency_rate_data",
        os_if_exists="append",
        os_refresh=True
    )


client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)


# Airflow DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
with DAG(
    '07.currency_rate_data',
    default_args=default_args,
    description="환율데이터를 수집하여 적재합니다.",
    schedule_interval='@daily',
    start_date=datetime(2010, 1, 1),
    catchup=False,
    tags=['Opensearch', 'currency', 'data']
) as dag:
    
    # PythonOperator 설정
    t1 = PythonOperator(
        task_id="currency_rate_upload",
        python_callable=dataframe_to_elasticsearch,
    )

    t1