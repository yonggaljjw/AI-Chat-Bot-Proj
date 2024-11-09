from datetime import datetime, timedelta
# import requests
# from bs4 import BeautifulSoup
import pandas as pd

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
# from elasticsearch import Elasticsearch, helpers
import re

from package.fsc_crawling import crawling
from package.fsc_extract import extract_main_content, extract_reason
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

# Elasticsearch 인스턴스 생성 (Docker 내부에서 실행 중인 호스트에 연결)
# es = Elasticsearch('http://host.docker.internal:9200')

# Elasticsearch 인덱스 생성 (이미 존재하면 무시)
try:
    # es.indices.create(index='raw_data')
    client.indices.create(index='raw_data')
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
    # 현재 날짜와 1년 전 날짜 계산
    current_date = datetime.now()
    one_year_ago = current_date - timedelta(days=365)
    
    # 1년 전부터 현재까지의 범위 쿼리 생성
    query = {
        "query": {
            "range": {
                "날짜": {
                    "gte": one_year_ago.strftime("%Y-%m-%d"),
                    "lte": current_date.strftime("%Y-%m-%d"),
                    "format": "yyyy-MM-dd"
                }
            }
        }
    }
    
    # Elasticsearch에서 검색
    # response = es.search(index="raw_data", body=query, size=10000)
    response = client.search(index="raw_data", body=query, size=10000)
    existing_entries = {(hit['_source']['제목'], hit['_source']['날짜'], hit['_source']['URL']) for hit in response['hits']['hits']}
    
    print(f"검색된 데이터 개수: {response['hits']['total']['value']}")
    print(f"기존 데이터 수: {len(existing_entries)}")
    return existing_entries

def upload_new_data():
    df = crawling_extract_df()
    existing_entries = get_existing_entries()

     # 벡터 임베딩 생성
    df['제목_vector'] = df['제목'].apply(generate_embedding)
    df['내용_vector'] = df['내용'].apply(generate_embedding)
    df['개정이유_vector'] = df['개정이유'].apply(generate_embedding)
    df['주요내용_vector'] = df['주요내용'].apply(generate_embedding)

    actions = [
        {
            "_op_type": "index",
            "_index": "raw_data",
            "_id": f"{row['제목']}_{row['날짜']}",
            "_source": {
                "제목": row['제목'],
                "제목_vector": row['제목_vector'],
                "날짜": row['날짜'],
                "URL": row['URL'],
                "내용": row['내용'],
                "내용_vector": row['내용_vector'],
                "개정이유": row['개정이유'],
                "개정이유_vector": row['개정이유_vector'],
                "주요내용": row['주요내용'],
                "주요내용_vector": row['주요내용_vector'],
            }
        }
        for _, row in df.iterrows()
        if (row['제목'], row['날짜'], row['URL']) not in existing_entries
    ]

    print(f"중복 제거 후 삽입할 데이터 수: {len(actions)}")
    
    if actions:
        # helpers.bulk(es, actions)
        helpers.bulk(client, actions)
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
    schedule_interval='@daily',  # 하루마다 실행
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
