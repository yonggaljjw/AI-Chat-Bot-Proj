from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
import subprocess
import json
from elasticsearch import Elasticsearch, helpers

import os
from opensearchpy import OpenSearch
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

# Elasticsearch 설정
es = Elasticsearch("http://host.docker.internal:9200")

def run_script(script_name):
    # Docker 환경에 맞게 파일 경로를 수정했습니다.
    script_path = f"/opt/airflow/dags/package/{script_name}"
    print(f"Running script: {script_path}")
    subprocess.run(["python", script_path])

def upload_to_elasticsearch():
    # JSON 파일을 읽어서 Elasticsearch에 업로드
    with open("/opt/airflow/topic_modeling_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Bulk API를 위한 작업 생성
    actions = []
    index_name = f"topic_modeling_results-{datetime.now().strftime('%Y%m%d')}"

    for category, results in data.items():
        for word_info in results['top_words']:
            action = {
                "_op_type": "index",  # 문서 인덱싱 작업
                "_index": index_name,
                "_id": f"{category}-{word_info['word']}",  # 카테고리와 단어를 조합하여 ID 생성
                "_source": {
                    "word": word_info['word'],
                    "count": word_info['count'],
                    "links": word_info['links'],
                    "category": category  # 카테고리 추가
                }
            }
            actions.append(action)

    # Bulk API 호출
    if actions:
        helpers.bulk(es, actions)
        helpers.bulk(client, actions)
        print(f"{len(actions)}개의 문서가 Elasticsearch에 업로드되었습니다.")
    else:
        print("업로드할 문서가 없습니다.")

default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG('my_workflow', default_args=default_args, catchup=False, start_date=datetime.now(), schedule_interval='@daily') as dag:
    task1 = PythonOperator(
        task_id='run_naver_news',
        python_callable=run_script,
        op_kwargs={'script_name': 'naver_news2.py'},
    )

    task2 = PythonOperator(
        task_id='run_topic_model',
        python_callable=run_script,
        op_kwargs={'script_name': 'topic_model3.py'},
    )

    task3 = PythonOperator(
        task_id='upload_to_elasticsearch',
        python_callable=upload_to_elasticsearch
    )

    # task1 실행 후 task2 실행, 그 후 task3 실행
    task1 >> task2 >> task3
