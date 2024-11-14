from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from airflow import DAG
from airflow.operators.python import PythonOperator
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv
import os

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


def setup_index(opensearch_client, index_name):
    # If the index exists, delete it
    if opensearch_client.indices.exists(index=index_name):
        opensearch_client.indices.delete(index=index_name)
    
    # Define the index mapping
    index_mapping = {
        "mappings": {
            "properties": {
                "date": {"type": "date"},
                "USD": {"type": "float"},
                "EUR": {"type": "float"},
                "JPY": {"type": "float"},
                "GBP": {"type": "float"},
                "AUD": {"type": "float"},
                "CAD": {"type": "float"},
                "NZD": {"type": "float"},
                "THB": {"type": "float"},
                "VND": {"type": "float"},
                "HKD": {"type": "float"},
                "TWD": {"type": "float"}
            }
        }
    }
    # Create the index with the mapping
    opensearch_client.indices.create(index=index_name, body=index_mapping)

# 환율 데이터 가져오기
def get_historical_exchange_rates(base_currency, target_currencies, start_date, end_date):
    exchange_data = {}
    for currency in target_currencies:
        symbol = f"{currency}{base_currency}=X"
        try:
            data = yf.Ticker(symbol).history(start=start_date, end=end_date)
            exchange_data[currency] = data['Close']
        except Exception as e:
            print(f"Error fetching data for {currency}: {e}")
    return pd.DataFrame(exchange_data)

# 데이터 OpenSearch에 저장
def upload_exchange_rates_to_opensearch(**context):
    base_currency = 'KRW'
    target_currencies = ['USD', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'NZD', 'THB', 'VND', 'HKD', 'TWD']
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")  # Two years prior
    
    # 환율 데이터 가져오기
    exchange_df = get_historical_exchange_rates(base_currency, target_currencies, start_date, end_date)
    exchange_df.reset_index(inplace=True)
    exchange_df.rename(columns={'Date': 'date'}, inplace=True)
    
    # OpenSearch client and index setup
    opensearch_client = client
    index_name = "currency_yfinance"
    setup_index(opensearch_client, index_name)
    
    # Create bulk actions for OpenSearch
    actions = [
        {
            "_index": index_name,
            "_source": row.to_dict()
        }
        for _, row in exchange_df.iterrows()
    ]
    
    # Bulk insert to OpenSearch
    helpers.bulk(opensearch_client, actions)
    print(f"Exchange rates successfully uploaded to OpenSearch index '{index_name}'.")

# Airflow DAG 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'EJ_Currency_yfinance',
    default_args=default_args,
    description='Fetches daily exchange rates and uploads to OpenSearch',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    upload_task = PythonOperator(
        task_id='upload_exchange_rates_to_opensearch',
        python_callable=upload_exchange_rates_to_opensearch,
        provide_context=True
    )

    upload_task
