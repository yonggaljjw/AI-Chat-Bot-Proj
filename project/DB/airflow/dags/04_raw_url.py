from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from opensearchpy import OpenSearch, helpers
from package.vector_embedding import generate_embedding
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}]
)

OC = os.getenv("OC_key")

# 함수 정의: XML 데이터를 크롤링하여 데이터프레임으로 변환
def fetch_law_data(**kwargs):
    texts = ['신용', '금융', '증권', '여신', '투자', '대부', '자산', '보험', '은행', '자본']
    base_url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=law&type=XML&display=100" 
    all_data = []

    for text in texts:
        url = f"{base_url}&query={text}"
        response = requests.get(url)

        if response.status_code == 200:
            try:
                root = ET.fromstring(response.content)  # XML 파싱 시도
                for law in root.findall("law"):
                    law_data = {
                        "분류": text,
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
            print(f"키워드 {text}에 대한 요청 실패. 상태 코드: {response.status_code}")

    df = pd.DataFrame(all_data)
    json_str = df.to_json(orient="records")  # DataFrame을 JSON 문자열로 변환
    kwargs['ti'].xcom_push(key='law_data_df', value=json_str)  # JSON 문자열을 XCom에 저장

def create_or_update_index():
    if client.indices.exists(index='law_url'):
        client.indices.delete(index='law_url')
        print("기존 인덱스 삭제 완료")

    index_settings = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                'embedding_vector': {
                    'type': 'knn_vector',
                    'dimension': 1536,
                },
                "분류": {"type": "text"},
                "법령일련번호": {"type": "text"},
                "현행연혁코드": {"type": "text"},
                "법령명한글": {"type": "text"},
                "법령상세링크": {"type": "text"}
            }
        }
    }
    client.indices.create(index='law_url', body=index_settings)
    print("새로운 인덱스 생성 완료")

def upload_to_opensearch(**kwargs):
    json_str = kwargs['ti'].xcom_pull(key='law_data_df', task_ids='fetch_data')  # XCom에서 JSON 문자열 가져오기
    df = pd.read_json(json_str, orient="records")  # JSON 문자열을 DataFrame으로 변환

    # 법률 데이터에 대한 embedding_vector 생성
    df['embedding_vector'] = df.apply(
        lambda row:
            f"""'분류': {row['분류']}
            '법령일련번호': {row['법령일련번호']}
            '현행연혁코드': {row['현행연혁코드']}
            '법령명한글': {row['법령명한글']}
            '법령상세링크': {row['법령상세링크']}""", 
            axis=1
        )
    df['embedding_vector'] = df['embedding_vector'].apply(generate_embedding)
    # 법률 데이터 Action 생성
    actions = create_bulk_actions(df, 'law_url')
    # 법률 데이터 업로드
    helpers.bulk(client, actions)
    
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
    print(actions[0])
    return actions

default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    '04.Law_URL_data',
    default_args=default_args,
    description='매일 법률 데이터의 원본의 URL을 업로드 합니다.',
    schedule_interval='@daily',
    start_date=datetime(2024, 11, 6),
    catchup=False,
    tags=['OpenSearch', 'crawl', 'Law']
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
        python_callable=upload_to_opensearch,
        provide_context=True
        
    )

    # 순서 정의
    initialize_index >> fetch_data_task >> upload_data_task