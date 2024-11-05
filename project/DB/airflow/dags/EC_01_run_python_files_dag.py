from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
import subprocess

def run_script(script_name):
    # Docker 환경에 맞게 파일 경로를 수정했습니다.
    script_path = f"/opt/airflow/dags/package/{script_name}"
    print(f"Running script: {script_path}")
    
    # 스크립트 실행
    subprocess.run(["python", script_path])


default_args = {
    'depends_on_past': False,  # 이전 작업의 성공 여부와 상관없이 실행
    'retries': 1,  # 실패 시 재시도 횟수
    'retry_delay': timedelta(minutes=5)  # 재시도 간격 (5분)
}

with DAG('my_workflow', default_args=default_args,catchup=False,start_date=datetime.now(), schedule_interval=None) as dag:
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
