from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from package.vector_embedding import generate_embedding
import os
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)


# Elasticsearch 인덱스 생성 또는 재설정 함수
def create_or_update_index():
    """Elasticsearch 인덱스를 생성 또는 갱신하여 '날짜' 필드를 date 타입으로 설정"""
    # 인덱스가 이미 존재하면 삭제
    if client.indices.exists(index='Korean_Law_data'):
        client.indices.delete(index='Korean_Law_data')
        print("기존 인덱스 삭제 완료")

    # 새로운 인덱스 생성 (날짜 필드를 date 타입으로 설정)
    index_settings = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "start_date": {"type": "date"},
                "end_date": {"type": "date"},
                "URL": {"type": "text"},
                "content": {"type": "text"},
                "revision_reason": {"type": "text"},
                "main_content": {"type": "text"},
                "summary": {"type": "text"},
                "embedding_vector" : {"type":"knn_vector", "dimension": 1536}
            }
        }
    }
    # es.indices.create(index='raw_data', body=index_settings)
    client.indices.create(index='Korean_Law_data', body=index_settings)
    print("새로운 인덱스 생성 완료")

def upload_to_opensearch():
    df = pd.read_csv("./dags/package/fsc_announcements_summary.csv")
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.strftime('%Y-%m-%d')  # 날짜 형식 통일
    df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce').dt.strftime('%Y-%m-%d')  # 날짜 형식 통일

    # 벡터 임베딩 생성
    df['embedding_vector'] = df['content'].apply(generate_embedding)

    actions = [
        {
            "_op_type": "index",
            "_index": "raw_data",
            "_source": {
                "title": row['title'],
                "start_date": row['start_date'],
                "end_date": row['end_date'],
                "URL": row['URL'],
                "content": row['content'],
                "revision_reason": row['revision_reason'],
                "main_content": row['main_content'],
                "summary": row["summary"],
                "embedding_vector": row['embedding_vector']
            }
        }
        for _, row in df.iterrows()
    ]

    print(f"삽입할 데이터 수: {len(actions)}")
    
    if actions:
        # helpers.bulk(es, actions)
        helpers.bulk(client, actions)
        print(f"{len(actions)}개의 데이터를 업로드했습니다.")
    else:
        print("업로드할 데이터가 없습니다.")


# 기본 인자 설정 (Airflow에서 공통으로 사용하는 인자들)
default_args = {
    'depends_on_past': False,  # 이전 작업의 성공 여부와 상관없이 실행
    'retries': 1,  # 실패 시 재시도 횟수
    'retry_delay': timedelta(minutes=5)  # 재시도 간격 (5분)
}


# DAG 정의 (Airflow에서 작업 흐름을 구성하는 단위)
with DAG(
    'fsc_csv',  # DAG 이름
    default_args=default_args,  # 기본 인자 설정
    description="입법예고/규정변경예고 데이터를 Elasticsearch에 저장합니다.",  # 설명
    schedule_interval=None,  # DAG이 한 번만 실행되도록 설정
    start_date=datetime.now(),  # 현재 시점에서 실행
    catchup=False,  # 과거 날짜의 작업은 무시
    tags=['elasticsearch', 'crawl', 'finance']  # 태그 설정 (DAG 분류에 사용)
) as dag:

    # Elasticsearch 데이터 초기화 작업
    clear_data = PythonOperator(
        task_id="create_or_update_index",  # 작업 ID
        python_callable=create_or_update_index,  # 실행할 함수
    )

    # Elasticsearch로 데이터 업로드 작업 정의
    upload_data = PythonOperator(
        task_id="upload_data",  # 작업 ID
        python_callable=upload_to_opensearch,  # 실행할 함수
    )

    # 작업 순서 정의 (데이터 초기화 후 데이터 업로드)
    clear_data >> upload_data
