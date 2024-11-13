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

   # 1. 'edu_data_F_cleaned' CSV 파일을 OpenSearch에 업로드하는 함수
# def upload_wooricard_data():
#     # ./dags/package/dddd.csv
#     file_path = '/opt/airflow/data/wooricard_data/edu_data_F_cleaned.csv'  # 실제 경로로 변경하세요.
#     df = pd.read_csv(file_path)

#     # 인덱스 생성 및 매핑 설정
#     if not client.indices.exists(index='wooricard_data'):
#         client.indices.create(
#             index='wooricard_data',
#             body={
#                 "mappings": {
#                     "properties": {
#                         "고객번호": {"type": "text"},
#                         "연령대": {"type": "text"},
#                         "성별": {"type": "keyword"},
#                         "회원등급": {"type": "keyword"},
#                         "거주지역_1": {"type": "text"},
#                         "라이프스테이지": {"type": "keyword"},
#                         "총이용금액": {"type": "int"},
#                         "신용카드이용금액": {"type": "int"},
#                         "체크카드이용금액": {"type": "int"},
#                         "가전/가구/주방용품": {"type": "int"},
#                         "보험/병원": {"type": "int"},
#                         "사무통신/서적/학원": {"type": "int"},
#                         "여행/레져/문화": {"type": "int"},
#                         "요식업": {"type": "int"},
#                         "용역/수리/건축자재": {"type": "int"},
#                         "유통": {"type": "int"},
#                         "보건위생": {"type": "int"},
#                         "의류/신변잡화": {"type": "int"},
#                         "자동차/연료/정비": {"type": "int"},
#                         "가구": {"type": "int"},
#                         "가전제품": {"type": "int"},
#                         "건물및시설관리": {"type": "int"},
#                         "건축/자재": {"type": "int"},
#                         "광학제품": {"type": "int"},
#                         "농업": {"type": "int"},
#                         "레져업소": {"type": "int"},
#                         "레져용품": {"type": "int"},
#                         "문화/취미": {"type": "int"},
#                         "보건/위생": {"type": "int"},
#                         "보험": {"type": "int"},
#                         "사무/통신기기": {"type": "int"},
#                         "서적/문구": {"type": "int"},
#                         "수리서비스": {"type": "int"},
#                         "숙박업": {"type": "int"},
#                         "신변잡화": {"type": "int"},
#                         "여행업": {"type": "int"},
#                         "연료판매": {"type": "int"},
#                         "용역서비스": {"type": "int"},
#                         "유통업비영리": {"type": "int"},
#                         "유통업영리": {"type": "int"},
#                         "음식료품": {"type": "int"},
#                         "의료기관": {"type": "int"},
#                         "의류": {"type": "int"},
#                         "일반/휴게음식": {"type": "int"},
#                         "자동차정비/유지": {"type": "int"},
#                         "자동차판매": {"type": "int"},
#                         "주방용품": {"type": "int"},
#                         "직물": {"type": "int"},
#                         "학원": {"type": "int"},
#                         "회원제형태업소": {"type": "int"}
#                     }
#                 }
#             }
#         )
    
#     oml.pandas_to_opensearch(
#         pd_df=df,
#         os_client=client,
#         os_dest_index="wooricard_data",
#         os_if_exists="append",
#         os_refresh=True
#     )

# 'age_payment' CSV 파일을 OpenSearch에 업로드하는 함수
def upload_age_payment_data():
    file_path = '/opt/airflow/dags/data/age_payment.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='age_payment'):
        client.indices.create(
            index='age_payment',
            body={
                "mappings": {
                    "properties": {
                        "연령대" : {"type": "text"},
                        "결제방식" : {"type": "text"},
                        "이용금액" : {"type": "int"},
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
    file_path = '/opt/airflow/dags/data/male_expense.csv'  # 실제 경로로 변경하세요.
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
    file_path = '/opt/airflow/dags/data/female_expense.csv'  # 실제 경로로 변경하세요.
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
    file_path = '/opt/airflow/dags/data/region_consumption.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='region_consumption'):
        client.indices.create(
            index='region_consumption',
            body={
                "mappings": {
                    "properties": {
                        "거주지역_1": {"type": "keyword"},
                        "가전/가구/주방용품": {"type": "float"},
                        "보험/병원": {"type": "float"},
                        "사무통신/서적/학원": {"type": "float"},
                        "여행/레져/문화": {"type": "float"},
                        "요식업": {"type": "float"},
                        "용역/수리/건축자재": {"type": "float"},
                        "유통": {"type": "float"},
                        "보건위생": {"type": "float"},
                        "의류/신변잡화": {"type": "float"},
                        "자동차/연료/정비": {"type": "float"},
                        "가구": {"type": "float"},
                        "가전제품": {"type": "float"},
                        "건물및시설관리": {"type": "float"},
                        "건축/자재": {"type": "float"},
                        "광학제품": {"type": "float"},
                        "농업": {"type": "float"},
                        "레져업소": {"type": "float"},
                        "레져용품": {"type": "float"},
                        "문화/취미": {"type": "float"},
                        "보건/위생": {"type": "float"},
                        "보험": {"type": "float"},
                        "사무/통신기기": {"type": "float"},
                        "서적/문구": {"type": "float"},
                        "수리서비스": {"type": "float"},
                        "숙박업": {"type": "float"},
                        "신변잡화": {"type": "float"},
                        "여행업": {"type": "float"},
                        "연료판매": {"type": "float"},
                        "용역서비스": {"type": "float"},
                        "유통업비영리": {"type": "float"},
                        "유통업영리": {"type": "float"},
                        "음식료품": {"type": "float"},
                        "의료기관": {"type": "float"},
                        "의류": {"type": "float"},
                        "일반/휴게음식": {"type": "float"},
                        "자동차정비/유지": {"type": "float"},
                        "자동차판매": {"type": "float"},
                        "주방용품": {"type": "float"},
                        "직물": {"type": "float"},
                        "학원": {"type": "float"},
                        "회원제형태업소": {"type": "float"}
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
    file_path = '/opt/airflow/dags/data/top_age_categories.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='top_age_categories'):
        client.indices.create(
            index='top_age_categories',
            body={
                "mappings": {
                    "properties": {
                        "연령대" : {"type": "text"},
                        "소비 카테고리" : {"type": "text"},
                        "이용 금액" : {"type": "int"},
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
    file_path = '/opt/airflow/dags/data/top10_level_categories.csv'  # 실제 경로로 변경하세요.
    df = pd.read_csv(file_path)
    
    # 인덱스 생성 및 매핑 설정
    if not client.indices.exists(index='top10_level_categories'):
        client.indices.create(
            index='top10_level_categories',
            body={
                "mappings": {
                    "properties": {
                        "회원등급" : {"type": "text"},
                        "보험/병원": {"type": "int"},
                        "여행/레져/문화": {"type": "int"},
                        "요식업": {"type": "int"},
                        "용역/수리/건축자재": {"type": "int"},
                        "용역서비스": {"type": "int"},
                        "유통": {"type": "int"},
                        "유통업영리": {"type": "int"},
                        "의료기관": {"type": "int"},
                        "일반/휴게음식": {"type": "int"},
                        "자동차/연료/정비": {"type": "int"}
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
    upload_age_payment_task >> upload_male_expense_task >> upload_female_expense_task >> upload_region_consumption_task >> upload_top_age_categories_task >> upload_top10_level_categories_task