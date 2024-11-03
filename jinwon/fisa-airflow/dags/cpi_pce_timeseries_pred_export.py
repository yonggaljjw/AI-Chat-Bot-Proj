import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import os

# Elasticsearch 설정
es = Elasticsearch('http://host.docker.internal:9200')

# CSV 파일 경로 설정
CSV_FILE_PATH = '/opt/airflow/data/credit_card_spending.csv'

def get_existing_entries():
    """Elasticsearch에 있는 모든 데이터의 (ds, yhat, yhat_lower, yhat_upper) 조합을 CSV로 저장"""
    query = {
        "size": 10000,
        "query": {
            "match_all": {}
        }
    }

    response = es.search(index="항목별_개인신용카드_소비현황", body=query)

    # 각 결과에서 필요한 필드 추출
    data = [
        {
            "ds": hit['_source']['ds'],
            "yhat": hit['_source']['yhat'],
            "yhat_lower": hit['_source']['yhat_lower'],
            "yhat_upper": hit['_source']['yhat_upper']
        }
        for hit in response['hits']['hits']
    ]

    # DataFrame으로 변환 후 CSV 파일 저장
    df = pd.DataFrame(data)
    df['ds'] = pd.to_datetime(df['ds'])
    df.to_csv(CSV_FILE_PATH, index=False)

# 기본 DAG 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    'pci_cpi_to_csv',
    default_args=default_args,
    description="Export data from Elasticsearch to CSV",
    schedule_interval=None,
    start_date=datetime.now(),
    catchup=False,
    tags=['elasticsearch', 'csv_export'],
) as dag:

    export_to_csv_task = PythonOperator(
        task_id='export_to_csv',
        python_callable=get_existing_entries
    )

    export_to_csv_task