from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
# from elasticsearch import Elasticsearch, helpers
import re

import os
from package.fsc_crawling import crawling
from package.fsc_extract import extract_main_content, extract_reason
from package.vector_embedding import generate_embedding

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

# Elasticsearch 인스턴스 생성 (Docker 내부에서 실행 중인 호스트에 연결)
# es = Elasticsearch('http://host.docker.internal:9200')

# Elasticsearch 인덱스 생성 또는 재설정 함수
def create_or_update_index():
    """Elasticsearch 인덱스를 생성 또는 갱신하여 '날짜' 필드를 date 타입으로 설정"""
    # 인덱스가 이미 존재하면 삭제
    # if es.indices.exists(index='raw_data'):
    #     es.indices.delete(index='raw_data')
    #     print("기존 인덱스 삭제 완료")
    if client.indices.exists(index='Korean_Law_data'):
        client.indices.delete(index='Korean_Law_data')
        print("기존 인덱스 삭제 완료")

    # 새로운 인덱스 생성 (날짜 필드를 date 타입으로 설정)
    index_settings = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "title_vector" : {"type":"knn_vector", "dimension": 1536},
                "date": {"type": "date"},
                "URL": {"type": "text"},
                "content": {"type": "text"},
                "content_vector" : {"type":"knn_vector", "dimension": 1536},
                "revision_reason": {"type": "text"},
                "revision_reason_vector" : {"type":"knn_vector", "dimension": 1536},
                "main_content": {"type": "text"},
                "main_content_vector" : {"type":"knn_vector", "dimension": 1536}
            }
        }
    }
    # es.indices.create(index='raw_data', body=index_settings)
    client.indices.create(index='Korean_Law_data', body=index_settings)
    print("새로운 인덱스 생성 완료")

def crawling_extract_df():
    df = crawling(10)
    column_mapping = {
        "제목": "title",
        "날짜": "date",
        "내용": "URL",
        "도착공항": "content",
        "개정이유": "revision_reason",
        "주요내용": "main_content"
    }   

    df.rename(columns=column_mapping, inplace=True)
    
    if df is None or df.empty:
        print("크롤링된 데이터가 없습니다. 빈 DataFrame을 반환합니다.")
        return pd.DataFrame(columns=['title', 'date', 'URL', 'content', 'revision_reason', 'main_content'])

    df['title'] = df['title'].fillna('내용없음')
    df['revision_reason'] = df['content'].apply(extract_reason)
    df['main_content'] = df['content'].apply(extract_main_content)
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')  # 날짜 형식 통일

    return df


def upload_data():
    df = crawling_extract_df()
    
    # 벡터 임베딩 생성
    df['title_vector'] = df['title'].apply(generate_embedding)
    df['content_vector'] = df['content'].apply(generate_embedding)
    df['revision_reason_vector'] = df['revision_reason'].apply(generate_embedding)
    df['main_content_vector'] = df['main_content'].apply(generate_embedding)
    
    actions = [
        {   
            "_op_type": "index",
            "_index": "raw_data",
            "_id": f"{row['title']}_{row['date']}",
            "_source": {
                "title": row['title'],
                "title_vector": row['title_vector'],
                "date": row['date'],
                "URL": row['URL'],
                "content": row['content'],
                "content_vector": row['content_vector'],
                "revision_reason": row['revision_reason'],
                "revision_reason_vector": row['revision_reason_vector'],
                "main_content": row['main_content'],
                "main_content_vector": row['main_content_vector'],
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


# Airflow DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Airflow DAG 정의
with DAG(
    '02.Korean_Law_Index_data',
    default_args=default_args,
    description="입법예고/규정변경예고 데이터를 생성하고 적재합니다.",
    schedule_interval='@monthly',
    start_date=datetime.now(),
    catchup=False,
    tags=['elasticsearch', 'crawl', 'finance']
) as dag:

    # Elasticsearch 인덱스 초기화 작업
    initialize_index = PythonOperator(
        task_id="initialize_elasticsearch_index",
        python_callable=create_or_update_index,
    )

    # 데이터 업로드 작업 정의
    upload_task = PythonOperator(
        task_id="upload_data_to_elasticsearch",
        python_callable=upload_data,
    )

    # DAG 실행 순서 설정
    initialize_index >> upload_task
