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

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)



def extract_currency_rate() :
    params = {
        'authkey': authkey,
        'searchdate' : datetime.today(),
        'data' : data}
    response = pd.DataFrame(requests.get(url, params=params).json())
    response['date'] = datetime.today()
    response = response.drop(columns=['result'])

    response['ttb'] = response['ttb'].apply(lambda x : x.replace(",",""))
    response['tts'] = response['tts'].apply(lambda x : x.replace(",",""))
    response['deal_bas_r'] = response['deal_bas_r'].apply(lambda x : x.replace(",",""))
    response['bkpr'] = response['bkpr'].apply(lambda x : x.replace(",",""))
    response['kftc_bkpr'] = response['kftc_bkpr'].apply(lambda x : x.replace(",",""))
    response['kftc_deal_bas_r'] = response['kftc_deal_bas_r'].apply(lambda x : x.replace(",",""))

    response['ttb'] = response['ttb'].astype('float')
    response['tts'] = response['tts'].astype('float')
    response['deal_bas_r'] = response['deal_bas_r'].astype('float')
    response['bkpr'] = response['bkpr'].astype('float')
    response['yy_efee_r'] = response['yy_efee_r'].astype('float')
    response['ten_dd_efee_r'] = response['ten_dd_efee_r'].astype('float')
    response['kftc_bkpr'] = response['kftc_bkpr'].astype('float')
    response['kftc_deal_bas_r'] = response['kftc_deal_bas_r'].astype('float')

    return response

## 데이터 적재를 위한 bulk_action 함수 생성
def create_bulk_actions(df, index_name):
    actions = []
    for index, row in df.iterrows():
        # Index action
        action = {
            "_index": index_name,
            "_source": row.to_dict()
        }
        actions.append(action)
    return actions


# Bulk API를 위한 작업 생성
def bulk_insert() :
    actions = create_bulk_actions(extract_currency_rate(), 'currency_rate')
    # Bulk API 호출
    if actions:
        # helpers.bulk(es, actions)
        helpers.bulk(client, actions)
        print(f"{len(actions)}개의 문서가 OpenSearch에 업로드되었습니다.")
    else:
        print("업로드할 문서가 없습니다.")


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
    python_callable=bulk_insert,
    )

    t1