from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import os
import pymysql
from sqlalchemy import create_engine

# 환경 변수 로드
load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
database = 'team5'
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}")

# 'combined_card_members' CSV 파일을 MySQL에 업로드하는 함수
def upload_members_data():
    file_path = '/opt/airflow/data/card_data/combined_card_members.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 데이터 형식 변환
    float_columns = ["롯데카드", "비씨카드(자체)", "삼성카드", "신한카드", "우리카드", "하나카드", "현대카드", "KB국민카드"]
    df[float_columns] = df[float_columns].astype(float)
    df['년월'] = df['년월'].apply(str) + '01'
    df['년월'] = pd.to_datetime(df['년월'], errors='coerce')

    # 데이터프레임을 MySQL에 업로드
    df.to_sql('card_members', con=engine, if_exists='replace', index=False)
    print(f"{len(df)}개의 데이터가 'card_members' 테이블에 업로드되었습니다.")

# 'combined_card_sales' CSV 파일을 MySQL에 업로드하는 함수
def upload_sales_data():
    file_path = '/opt/airflow/data/card_data/combined_card_sales.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 데이터 형식 변환
    float_columns = ["롯데카드", "비씨카드(자체)", "삼성카드", "신한카드", "우리카드", "하나카드", "현대카드", "KB국민카드", "합계"]
    df[float_columns] = df[float_columns].astype(float)
    df['년월'] = df['년월'].apply(str) + '01'
    df['년월'] = pd.to_datetime(df['년월'], errors='coerce')

    # 데이터프레임을 MySQL에 업로드
    df.to_sql('card_sales', con=engine, if_exists='replace', index=False)
    print(f"{len(df)}개의 데이터가 'card_sales' 테이블에 업로드되었습니다.")

# DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retires': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG 정의 (매월 실행)
with DAG(
    '10_upload_card_data_to_mysql',
    default_args=default_args,
    description="card_data.CSV 데이터를 MySQL에 업로드합니다.",
    schedule_interval='@monthly',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['mysql', 'csv', 'data']
) as dag:
    
    # 각각의 CSV 파일 업로드 작업 설정
    upload_members_task = PythonOperator(
        task_id="upload_members_data_to_mysql",
        python_callable=upload_members_data,
    )
    
    upload_sales_task = PythonOperator(
        task_id="upload_sales_data_to_mysql",
        python_callable=upload_sales_data,
    )

    # 작업 순서 설정
    upload_members_task >> upload_sales_task