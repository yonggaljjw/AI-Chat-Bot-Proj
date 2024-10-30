from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from elasticsearch import Elasticsearch, helpers

from fsc_crawling import crawling

# Elasticsearch 인스턴스 생성 (Docker 내부에서 실행 중인 호스트에 연결)
es = Elasticsearch('http://host.docker.internal:9200')

# Elasticsearch 인덱스 생성 (이미 존재하면 무시)
try:
    es.indices.create(index='raw_data')
except Exception as e:
    print(f"인덱스 생성 오류 또는 이미 존재: {e}")

def crawling_extract_df():
    df = crawling()
    # '내용' 열에 결측치가 있는지 확인 후 처리
    df['내용'] = df['내용'].fillna('')  # 결측치를 빈 문자열로 대체
    # # '내용' 열에서 주요 내용 추출 후 '주요내용' 열에 저장
    df['개정이유'] = df['내용'].apply(extract_reason)

    # # '내용' 열에서 주요 내용 추출 후 '주요내용' 열에 저장
    df['주요내용'] = df['내용'].apply(extract_main_content)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_existing_entries():
    """Elasticsearch에 있는 모든 데이터의 (제목, 날짜, URL) 조합을 가져옴"""
    query = {"query": {"match_all": {}}}
    response = es.search(index="raw_data", body=query, size=10000)  # 최대 10,000개 조회
    return {(hit['_source']['제목'], hit['_source']['날짜'], hit['_source']['URL']) for hit in response['hits']['hits']}

def upload_new_data():
    """중복되지 않는 데이터만 Elasticsearch에 업로드"""
    df = crawling_extract_df()  # 크롤링한 데이터 가져오기
    existing_entries = get_existing_entries()  # Elasticsearch에서 기존 데이터 가져오기

    # 중복되지 않는 데이터만 추출하여 업로드 준비
    actions = [
        {
            "_op_type": "index",
            "_index": "raw_data",
            "_id": f"{row['제목']}_{row['날짜']}",  # 고유 ID 생성
            "_source": row.to_dict()
        }
        for _, row in df.iterrows()
        if (row['제목'], row['날짜'], row['URL']) not in existing_entries  # 중복 여부 확인
    ]

    if actions:
        helpers.bulk(es, actions)  # 배치 업로드
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
    'fsc_hourly_raw_elasticsearch',  # DAG 이름
    default_args=default_args,  # 기본 설정
    description="입법예고 데이터를 중복 없이 Elasticsearch에 저장합니다.",  # 설명
    schedule_interval='@hourly',  # 1시간마다 실행
    start_date=datetime(2024, 10, 30),  # 시작 날짜
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
