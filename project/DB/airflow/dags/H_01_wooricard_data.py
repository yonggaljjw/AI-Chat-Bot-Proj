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
    # http_auth=auth,
    use_ssl=False,
    verify_certs=False
)

# 'age_payment' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_age_payment_data():
    file_path = '/opt/airflow/data/wooricard_data/age_payment.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)

    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='age_payment'):
        client.indices.create(
            index='age_payment',
            body={
                "mappings": {
                    "properties": {
                        "연령대" : {"type": "keyword"},
                        "결제방식" : {"type": "keyword"},
                        "이용금액" : {"type": "integer"},
                    }
                }
            }
        )
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="age_payment",
        os_if_exists="append",
        os_refresh=True
    )

# 'male_expense' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_male_expense_data():
    file_path = '/opt/airflow/data/wooricard_data/male_expense.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="male_expense",
        os_if_exists="append",
        os_refresh=True
    )

# 'female_expense' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_female_expense_data():
    file_path = '/opt/airflow/data/wooricard_data/female_expense.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="female_expense",
        os_if_exists="append",
        os_refresh=True
    )

# 'region_consumption' CSV 파일을 OpenSearch에 업로드하는 함수
def region_consumption():
    file_path = '/opt/airflow/data/wooricard_data/region_consumption.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='region_consumption'):
        client.indices.create(
            index='region_consumption',
            body={
                "mappings": {
                    "properties": {
                        "거주지역_1": {"type": "keyword"},
                        "가전/가구/주방용품": {"type": "double"},
                        "보험/병원": {"type": "double"},
                        "사무통신/서적/학원": {"type": "double"},
                        "여행/레져/문화": {"type": "double"},
                        "요식업": {"type": "double"},
                        "용역/수리/건축자재": {"type": "double"},
                        "유통": {"type": "double"},
                        "보건위생": {"type": "double"},
                        "의류/신변잡화": {"type": "double"},
                        "자동차/연료/정비": {"type": "double"},
                        "가구": {"type": "double"},
                        "가전제품": {"type": "double"},
                        "건물및시설관리": {"type": "double"},
                        "건축/자재": {"type": "double"},
                        "광학제품": {"type": "double"},
                        "농업": {"type": "double"},
                        "레져업소": {"type": "double"},
                        "레져용품": {"type": "double"},
                        "문화/취미": {"type": "double"},
                        "보건/위생": {"type": "double"},
                        "보험": {"type": "double"},
                        "사무/통신기기": {"type": "double"},
                        "서적/문구": {"type": "double"},
                        "수리서비스": {"type": "double"},
                        "숙박업": {"type": "double"},
                        "신변잡화": {"type": "double"},
                        "여행업": {"type": "double"},
                        "연료판매": {"type": "double"},
                        "용역서비스": {"type": "double"},
                        "유통업비영리": {"type": "double"},
                        "유통업영리": {"type": "double"},
                        "음식료품": {"type": "double"},
                        "의료기관": {"type": "double"},
                        "의류": {"type": "double"},
                        "일반/휴게음식": {"type": "double"},
                        "자동차정비/유지": {"type": "double"},
                        "자동차판매": {"type": "double"},
                        "주방용품": {"type": "double"},
                        "직물": {"type": "double"},
                        "학원": {"type": "double"},
                        "회원제형태업소": {"type": "double"}
                    }
                }
            }
        )
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="region_consumption",
        os_if_exists="append",
        os_refresh=True
    )

# 'top_age_categories' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_top_age_categories_data():
    file_path = '/opt/airflow/data/wooricard_data/top_age_categories.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='top_age_categories'):
        client.indices.create(
            index='top_age_categories',
            body={
                "mappings": {
                    "properties": {
                        "연령대" : {"type": "keyword"},
                        "소비 카테고리" : {"type": "keyword"},
                        "이용 금액" : {"type": "integer"},
                    }
                }
            }
        )
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="top_age_categories",
        os_if_exists="append",
        os_refresh=True
    )

# 'top10_level_categories' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_top10_level_categories_data():
    file_path = '/opt/airflow/data/wooricard_data/top10_level_categories.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='top10_level_categories'):
        client.indices.create(
            index='top10_level_categories',
            body={
                "mappings": {
                    "properties": {
                        "회원등급" : {"type": "keyword"},
                        "보험/병원": {"type": "double"},
                        "여행/레져/문화": {"type": "double"},
                        "요식업": {"type": "double"},
                        "용역/수리/건축자재": {"type": "double"},
                        "용역서비스": {"type": "double"},
                        "유통": {"type": "double"},
                        "유통업영리": {"type": "double"},
                        "의료기관": {"type": "double"},
                        "일반/휴게음식": {"type": "double"},
                        "자동차/연료/정비": {"type": "double"}

                    }
                }
            }
        )
    
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="top10_level_categories",
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
    'upload_wooricard_data_to_opensearch',
    default_args=default_args,
    description="wooricard_data.CSV 데이터를 OpenSearch에 업로드합니다.",
    schedule_interval='@monthly',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['opensearch', 'csv', 'data']
) as dag:
    
    upload_age_payment_task = PythonOperator(
        task_id="upload_age_payment",
        python_callable=upload_age_payment_data,
    )

    upload_male_task = PythonOperator(
        task_id="upload_male",
        python_callable=upload_male_expense_data,
    )

    upload_female_task = PythonOperator(
        task_id="upload_female",
        python_callable=upload_female_expense_data,
    )

    upload_region_consumption_task = PythonOperator(
        task_id="upload_region_consumption",
        python_callable=region_consumption,
    )

    upload_top_age_task = PythonOperator(
        task_id="upload_top_age",
        python_callable=upload_top_age_categories_data,
    )

    upload_top_level_task = PythonOperator(
        task_id="upload_top_level",
        python_callable=upload_top10_level_categories_data,
    )

    # 작업 순서 설정
    upload_age_payment_task >> upload_male_task >> upload_female_task >> upload_region_consumption_task >> upload_top_age_task >> upload_top_level_task