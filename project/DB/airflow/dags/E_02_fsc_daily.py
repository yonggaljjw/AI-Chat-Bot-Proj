from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from elasticsearch import Elasticsearch, helpers
import re

from package.fsc_crawling import crawling
from package.fsc_extract import extract_main_content, extract_reason

# Elasticsearch 인스턴스 생성 (Docker 내부에서 실행 중인 호스트에 연결)
es = Elasticsearch('http://192.168.0.101:9200')

# Elasticsearch 인덱스 생성 (이미 존재하면 무시)
try:
    es.indices.create(index='raw_data')
except Exception as e:
    print(f"인덱스 생성 오류 또는 이미 존재: {e}")


def crawling_extract_df():
    df = crawling(3)
    
    if df is None or df.empty:
        print("크롤링된 데이터가 없습니다. 빈 DataFrame을 반환합니다.")
        return pd.DataFrame(columns=['제목', '날짜', 'URL', '내용', '개정이유', '주요내용'])

    df['내용'] = df['내용'].fillna('내용없음')
    df['개정이유'] = df['내용'].apply(extract_reason)
    df['주요내용'] = df['내용'].apply(extract_main_content)
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce').dt.strftime('%Y-%m-%d')  # 날짜 형식 통일

    return df

def get_existing_entries():
    query = {"query": {"range": {"날짜": {"gte": "2024-01-01","format": "yyyy-MM-dd"}}}}
    response = es.search(index="raw_data", body=query, size=10000)
    existing_entries = {(hit['_source']['제목'], hit['_source']['날짜'], hit['_source']['URL']) for hit in response['hits']['hits']}
    
    print(f"기존 데이터 수: {len(existing_entries)}")
    return existing_entries

def upload_new_data():
    df = crawling_extract_df()
    existing_entries = get_existing_entries()
    
    actions = [
        {
            "_op_type": "index",
            "_index": "raw_data",
            "_id": f"{row['제목']}_{row['날짜']}",
            "_source": row.to_dict()
        }
        for _, row in df.iterrows()
        if (row['제목'], row['날짜'], row['URL']) not in existing_entries
    ]

    print(f"중복 제거 후 삽입할 데이터 수: {len(actions)}")
    
    if actions:
        helpers.bulk(es, actions)
        print(f"{len(actions)}개의 새로운 데이터를 업로드했습니다.")
    else:
        print("새로운 데이터가 없습니다.")

# Airflow DAG 기본 설정
default_args = {
    'depends_on_past': False,  # 이전 작업에 의존하지 않음
    'retries': 1,  # 실패 시 재시도 횟수
    'retry_delay': timedelta(minutes=5),  # 재시도 간격
}

# Airflow DAG 정의
with DAG(
    'fsc_daily',  # DAG 이름
    default_args=default_args,  # 기본 설정
    description="입법예고 데이터를 중복 없이 Elasticsearch에 저장합니다.",  # 설명
    schedule_interval='@daily',  # 1시간마다 실행
    start_date=datetime.now(),  # 시작 날짜
    catchup=False,  # 과거 실행 건 무시
    tags=['elasticsearch', 'crawl', 'finance']  # 태그
) as dag:

    # 데이터 업로드 작업 정의
    upload_task = PythonOperator(
        task_id="upload_new_data_to_elasticsearch",  # 작업 ID
        python_callable=upload_new_data,  # 실행할 함수
    )

    # DAG 실행
    upload_task
