from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
import subprocess
import json
from elasticsearch import Elasticsearch

# Elasticsearch 설정
es = Elasticsearch("http://192.168.0.101:9200")

def run_script(script_name):
    script_path = f"/opt/airflow/dags/{script_name}"
    print(f"Running script: {script_path}")
    subprocess.run(["python", script_path])

def upload_to_elasticsearch():
    # 당일 날짜를 기반으로 인덱스 이름 생성
    index_name = f"topic_modeling_result-{datetime.now().strftime('%Y%m%d')}"
    
    # JSON 파일을 읽어서 Elasticsearch에 업로드
    with open("/opt/airflow/dags/topic_modeling_result.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            es.index(index=index_name, body=item)
    print(f"Elasticsearch에 데이터 업로드 완료: {index_name}")

default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG('my_workflow', default_args=default_args, catchup=False, start_date=datetime.now(), schedule_interval=None) as dag:
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

    # task3 = PythonOperator(
    #     task_id='watching_word',
    #     python_callable=run_script,
    #     op_kwargs={'script_name': 'watching_word.py'},
    # )

    task4 = PythonOperator(
        task_id='upload_to_elasticsearch',
        python_callable=upload_to_elasticsearch
    )

    # task2 실행 후 Elasticsearch에 업로드
    task1 >> task2 >> task4
