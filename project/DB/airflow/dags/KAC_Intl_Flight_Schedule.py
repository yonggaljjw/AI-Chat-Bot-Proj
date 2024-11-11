from datetime import datetime, timedelta
import pandas as pd
import eland as ed  # Pandas와 Elasticsearch 연동 라이브러리
from airflow import DAG  # Airflow에서 DAG을 정의하기 위한 모듈
from airflow.operators.python_operator import PythonOperator  # Python 작업 정의용 Operator
from opensearchpy import OpenSearch
import opensearch_py_ml as oml
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# OpenSearch client configuration
host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))  # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=False
)

# Elasticsearch index creation and update function
def create_or_reset():
    """Creates or resets the 'flight_schedule' index with defined mappings."""
    if client.indices.exists(index='flight_schedule'):
        client.indices.delete(index='flight_schedule')
        print("Existing index deleted.")

    index_settings = {
        "mappings": {
            "properties": {
                "airline": {"type": "keyword"},
                "flight_number": {"type": "keyword"},
                "departure_airport": {"type": "keyword"},
                "arrival_airport": {"type": "keyword"},
                "departure_time": {"type": "date", "format": "HH:mm"},
                "arrival_time": {"type": "date", "format": "HH:mm"},
                "operating_days": {"type": "keyword"},
                "start_date": {"type": "date", "format": "yyyy-MM-dd"},
                "end_date": {"type": "date", "format": "yyyy-MM-dd"},
                "domestic_international": {"type": "keyword"}
            }
        }
    }

    client.indices.create(index='flight_schedule', body=index_settings)
    print("New index created.")

# Function to upload CSV data to Elasticsearch
def upload_csv():
    """Loads CSV data and uploads it to the 'flight_schedule' index in Elasticsearch."""
    df = pd.read_csv("./dags/package/한국공항공사_국제선 항공기스케줄_20240809.csv")
    column_mapping = {
        "항공사": "airline",
        "운항편명": "flight_number",
        "출발공항": "departure_airport",
        "도착공항": "arrival_airport",
        "출발시간": "departure_time",
        "도착시간": "arrival_time",
        "운항요일": "operating_days",
        "시작일자": "start_date",
        "종료일자": "end_date",
        "국내_국제": "domestic_international"
    }

    df.rename(columns=column_mapping, inplace=True)

    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index="flight_schedule",
        os_if_exists="append",
        os_refresh=True
    )
    print("Data upload complete.")

# Airflow default arguments
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# Define DAG
with DAG(
    'flight_schedule',
    default_args=default_args,
    description="한국공항공사_국제선 항공기스케줄",
    schedule_interval=None,
    start_date=datetime.now(),
    catchup=False,
    tags=['elasticsearch', 'crawl', 'finance']
) as dag:

    # Task: Clear Elasticsearch data
    clear_data = PythonOperator(
        task_id="reset_flight_schedule_index",
        python_callable=create_or_reset,
    )

    # Task: Upload CSV data to Elasticsearch
    upload_data = PythonOperator(
        task_id="upload_csv_to_flight_schedule_index",
        python_callable=upload_csv,
    )

    # Task sequence
    clear_data >> upload_data
