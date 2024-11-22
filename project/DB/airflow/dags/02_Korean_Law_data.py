from datetime import datetime, timedelta
# import requests
# from bs4 import BeautifulSoup
import pandas as pd

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
# from elasticsearch import Elasticsearch, helpers
import re

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from package.fsc_crawling import crawling
from package.fsc_extract import extract_main_content, extract_reason
from package.vector_embedding import generate_embedding
import os

from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv
import nltk

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}]
)

nltk.download('punkt_tab')

try:
    client.indices.create(index='korean_law_data')
except Exception as e:
    print(f"인덱스 생성 오류 또는 이미 존재: {e}")

# 요약 생성 함수
def generate_summary(df, tokenizer, model, max_input_length=512):
    """
    모델을 사용하여 'main_content'와 'revision_reason'을 결합한 요약을 생성
    """
    summaries = []  # 결과를 저장할 리스트 초기화

    # 각 행에 대해 요약 생성
    for _, row in df.iterrows():
        combined_input = f"{row['main_content']} {row['revision_reason']}"
        inputs = tokenizer(combined_input, max_length=max_input_length, truncation=True, return_tensors="pt")
        
        # 요약 생성
        output = model.generate(**inputs, num_beams=8, do_sample=True, min_length=10, max_length=100)
        decoded_output = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
        
        # 첫 문장만 추출하여 요약 제목으로 사용
        predicted_title = nltk.sent_tokenize(decoded_output.strip())[0]
        summaries.append(predicted_title)
        print("성공")

    df['summary'] = summaries  # 요약 결과를 데이터프레임에 추가
    return df

def crawling_extract_df():
    df = crawling(2)
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.strftime('%Y-%m-%d')  # 날짜 형식 통일
    df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce').dt.strftime('%Y-%m-%d')  # 날짜 형식 통일
    df['title'] = df['title'].fillna('내용없음')
    df['revision_reason'] = df['content'].apply(extract_reason)
    df['main_content'] = df['content'].apply(extract_main_content)  
    df['summary'] = df['revision_reason'] + df['main_content']

    # 요약문 생성
    input_file = "./fsc_announcements.csv"
    model_directory = "./dags/package/t5-large-korean-text-summary/"
    tokenizer = AutoTokenizer.from_pretrained(model_directory)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_directory)
    df = generate_summary(df, tokenizer, model)
    # 벡터 임베딩 생성
    df['embedding_vector'] = df['content'].apply(generate_embedding)
    return df

def get_existing_entries():
    # 현재 날짜와 1년 전 날짜 계산
    current_date = datetime.now()
    one_year_ago = current_date - timedelta(days=200)
    
    # 1년 전부터 현재까지의 범위 쿼리 생성
    query = {
        "query": {
            "range": {
                "date": {
                    "gte": one_year_ago.strftime("%Y-%m-%d"),
                    "lte": current_date.strftime("%Y-%m-%d"),
                    "format": "yyyy-MM-dd"
                }
            }
        }
    }

    # Elasticsearch에서 검색
    response = client.search(index="korean_law_data", body=query, size=10000)
    existing_entries = {(hit['_source']['title'], hit['_source']['date'], hit['_source']['URL']) for hit in response['hits']['hits']}
    
    print(f"검색된 데이터 개수: {response['hits']['total']['value']}")
    print(f"기존 데이터 수: {len(existing_entries)}")
    return existing_entries

def upload_new_data():
    df = crawling_extract_df()
    existing_entries = get_existing_entries()

    actions = [
        {
            "_op_type": "index",
            "_index": "korean_law_data",
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
        if (row['title'], row['date'], row['URL']) not in existing_entries
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
    '02_Korean_Law_data',  # DAG 이름
    default_args=default_args,  # 기본 설정
    description="입법예고 데이터를 중복 없이 매일 저장합니다.",  # 설명
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
