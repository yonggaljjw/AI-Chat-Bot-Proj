from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import os
from opensearchpy import OpenSearch
import opensearch_py_ml as oml

# 환경 변수 로드
load_dotenv()

# OpenSearch 연결 설정
host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=False
)

# 1. 'combined_card_members' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_members_data():
    file_path = '/opt/airflow/dags/data/combined_card_members.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 데이터 형식 변환
    float_columns = ["롯데카드", "비씨카드(자체)", "삼성카드", "신한카드", "우리카드", "하나카드", "현대카드", "KB국민카드"]
    df[float_columns] = df[float_columns].astype(float)
    df['년월'] = df['년월'].apply(str) + '01'
    df['년월'] = pd.to_datetime(df['년월'], errors='coerce')

    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='card_members'):
        client.indices.create(
            index='card_members',
            body={
                "mappings": {
                    "properties": {
                        "대분류": {"type": "text"},
                        "카드 종류": {"type": "text"},
                        "사용구분": {"type": "text"},
                        "회원 관련 정보": {"type": "text"},
                        "롯데카드": {"type": "float"},
                        "비씨카드(자체)": {"type": "float"},
                        "삼성카드": {"type": "float"},
                        "신한카드": {"type": "float"},
                        "우리카드": {"type": "float"},
                        "하나카드": {"type": "float"},
                        "현대카드": {"type": "float"},
                        "KB국민카드": {"type": "float"},
                        "년월": {"type": "date"}
                    }
                }
            }
        )
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="card_members",
        os_if_exists="append",
        os_refresh=True
    )

# 'combined_card_sales' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_sales_data():
    file_path = '/opt/airflow/dags/data/combined_card_sales.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 데이터 형식 변환
    float_columns = ["롯데카드", "비씨카드(자체)", "삼성카드", "신한카드", "우리카드", "하나카드", "현대카드", "KB국민카드", "합계"]
    df[float_columns] = df[float_columns].astype(float)
    df['년월'] = df['년월'].apply(str) + '01'
    df['년월'] = pd.to_datetime(df['년월'], errors='coerce')
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='card_sales'):
        client.indices.create(
            index='card_sales',
            body={
                "mappings": {
                    "properties": {
                        "대분류": {"type": "text"},
                        "카드 종류": {"type": "text"},
                        "사용구분": {"type": "text"},
                        "결제 방법": {"type": "text"},
                        "롯데카드": {"type": "float"},
                        "비씨카드(자체)": {"type": "float"},
                        "삼성카드": {"type": "float"},
                        "신한카드": {"type": "float"},
                        "우리카드": {"type": "float"},
                        "하나카드": {"type": "float"},
                        "현대카드": {"type": "float"},
                        "KB국민카드": {"type": "float"},
                        "합계": {"type": "float"},
                        "년월": {"type": "date"}
                    }
                }
            }
        )
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="card_sales",
        os_if_exists="append",
        os_refresh=True
    )

# DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retires': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG 정의 (매월 실행)
with DAG(
    'upload_card_data_to_opensearch',
    default_args=default_args,
    description="card_data.CSV 데이터를 OpenSearch에 업로드합니다.",
    schedule_interval='@monthly',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['opensearch', 'csv', 'data']
) as dag:
    
    # 각각의 CSV 파일 업로드 작업 설정
    upload_members_task = PythonOperator(
        task_id="upload_members_data_to_opensearch",
        python_callable=upload_members_data,
    )
    
    upload_sales_task = PythonOperator(
        task_id="upload_sales_data_to_opensearch",
        python_callable=upload_sales_data,
    )

    # 작업 순서 설정
    upload_members_task >> upload_sales_task