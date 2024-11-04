from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess

def run_script(script_name):
    subprocess.run(["python", f"/usr/local/airflow/dags/{script_name}"])

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),  # 시작 날짜를 설정하세요
}

with DAG('my_workflow', default_args=default_args, schedule_interval=None) as dag:
    task1 = PythonOperator(
        task_id='run_naver_new',
        python_callable=run_script,
        op_kwargs={'script_name': 'naver_news2.py'},
    )

    task2 = PythonOperator(
        task_id='run_topic_model2',
        python_callable=run_script,
        op_kwargs={'script_name': 'topic_model3.py'},
    )

    task3 = PythonOperator(
        task_id='watching_word',
        python_callable=run_script,
        op_kwargs={'script_name': 'watching_word.py'},
    )

    task1 >> task2 >> task3 