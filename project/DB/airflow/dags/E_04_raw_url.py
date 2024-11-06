from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from elasticsearch import Elasticsearch, helpers
import os

# Elasticsearch 연결 설정
es = Elasticsearch("http://host.docker.internal:9200")

OC = os.getenv("OC_key")

# 함수 정의: XML 데이터를 크롤링하여 데이터프레임으로 변환
def fetch_law_data(**kwargs):
    keywords = ['신용', '금융', '증권', '여신', '투자', '대부', '자산', '보험', '은행', '자본']
    base_url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=law&type=XML&display=100" 
    all_data = []

    for keyword in keywords:
        url = f"{base_url}&query={keyword}"
        response = requests.get(url)

        if response.status_code == 200:
            try:
                root = ET.fromstring(response.content)  # XML 파싱 시도
                for law in root.findall("law"):
                    law_data = {
                        "분류": keyword,
                        "법령일련번호": law.find("법령일련번호").text if law.find("법령일련번호") is not None else '',
                        "현행연혁코드": law.find("현행연혁코드").text if law.find("현행연혁코드") is not None else '',
                        "법령명한글": law.find("법령명한글").text.strip() if law.find("법령명한글") is not None else '',
                        "법령상세링크": "https://www.law.go.kr" + law.find("법령상세링크").text if law.find("법령상세링크") is not None else ''
                    }
                    all_data.append(law_data)
            except ET.ParseError as e:
                print(f"XML 파싱 오류 발생: {e}")
                print(response.content.decode('utf-8'))  # XML 내용 출력하여 문제 확인
        else:
            print(f"키워드 {keyword}에 대한 요청 실패. 상태 코드: {response.status_code}")

    df = pd.DataFrame(all_data)
    json_str = df.to_json(orient="records")  # DataFrame을 JSON 문자열로 변환
    kwargs['ti'].xcom_push(key='law_data_df', value=json_str)  # JSON 문자열을 XCom에 저장

def create_or_update_index():
    """ElasticSearch 인덱스를 생성 또는 갱신"""
    if es.indices.exists(index='law_url'):
        es.indices.delete(index='law_url')
        print("기존 인덱스 삭제 완료")

    index_settings = {
        "mappings": {
            "properties": {
                "분류": {"type": "keyword"},
                "법령일련번호": {"type": "keyword"},
                "현행연혁코드": {"type": "keyword"},
                "법령명한글": {"type": "keyword"},
                "법령상세링크": {"type": "keyword"}
            }
        }
    }
    es.indices.create(index='law_url', body=index_settings)
    print("새로운 인덱스 생성 완료")

def upload_to_elasticsearch(**kwargs):
    json_str = kwargs['ti'].xcom_pull(key='law_data_df', task_ids='fetch_data')  # XCom에서 JSON 문자열 가져오기
    df = pd.read_json(json_str, orient="records")  # JSON 문자열을 DataFrame으로 변환

    actions = [
        {
            "_op_type": "index",
            "_index": "law_url",
            "_id": f"{row['법령일련번호']}",
            "_source": row.to_dict()
        }
        for _, row in df.iterrows()
    ]

    print(f"삽입할 데이터 수: {len(actions)}")
    
    if actions:
        helpers.bulk(es, actions)
        print(f"{len(actions)}개의 데이터를 업로드했습니다.")
    else:
        print("업로드할 데이터가 없습니다.")

default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'fsc_real_raw_url',
    default_args=default_args,
    description='매일 법률 데이터를 수집하여 ElasticSearch에 업로드',
    schedule_interval='@daily',
    start_date=datetime(2024, 11, 6),
    catchup=False,
    tags=['elasticsearch', 'crawl', 'finance']
) as dag:

    # Elasticsearch 인덱스 초기화 작업
    initialize_index = PythonOperator(
        task_id="initialize_elasticsearch_index",
        python_callable=create_or_update_index,
    )

    # 데이터 수집 작업
    fetch_data_task = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_law_data,
        provide_context=True
    )

    # ElasticSearch 업로드 작업
    upload_data_task = PythonOperator(
        task_id='upload_data',
        python_callable=upload_to_elasticsearch,
        provide_context=True
    )

    # 순서 정의
    initialize_index >> fetch_data_task >> upload_data_task