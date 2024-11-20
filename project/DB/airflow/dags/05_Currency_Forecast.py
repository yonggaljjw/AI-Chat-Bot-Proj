from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
from opensearchpy import OpenSearch, helpers
# from train import normalize_mult, get_historical_exchange_rates, fill_na_with_avg
from airflow import DAG
from airflow.operators.python import PythonOperator
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}]
)

# OpenSearch index setup
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
                "HKD": {"type": "float"},
                "TWD": {"type": "float"}
            }
        }
    }
    # Create the index with the mapping
    opensearch_client.indices.create(index=index_name, body=index_mapping)

# 데이터 정규화
def normalize_mult(data):
    normalize = np.zeros((data.shape[1], 2), dtype='float64')
    for i in range(data.shape[1]):
        listlow, listhigh = np.percentile(data[:, i], [0, 100])
        normalize[i, :] = [listlow, listhigh]
        delta = listhigh - listlow
        if delta != 0:
            data[:, i] = (data[:, i] - listlow) / delta
    return data, normalize

# 역정규화 함수
def FNormalizeMult(data, normalize):
    for i in range(data.shape[1]):
        delta = normalize[i, 1] - normalize[i, 0]
        if delta != 0:
            data[:, i] = data[:, i] * delta + normalize[i, 0]
    return data

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

# 결측값 처리
def fill_na_with_avg(df):
    return (df.ffill() + df.bfill()) / 2

# 미래 예측을 위한 함수
def predict_future(model, last_data, time_steps, normalize, future_days=100):
    future_predictions = []
    input_sequence = last_data[-time_steps:]  # 마지막 100일 데이터 사용
    
    for _ in range(future_days):
        normalized_input = (input_sequence - normalize[:, 0]) / (normalize[:, 1] - normalize[:, 0])
        prediction = model.predict(normalized_input.reshape(1, time_steps, -1))
        prediction_denorm = prediction * (normalize[:, 1] - normalize[:, 0]) + normalize[:, 0]
        
        future_predictions.append(prediction_denorm[0, 0])
        
        # 새로운 예측값을 입력 시퀀스에 추가하여 다음 예측 준비
        input_sequence = np.append(input_sequence[1:], prediction_denorm, axis=0)

    return future_predictions

# 메인 함수
def run_prediction_and_upload():
    MODEL_PATH = './dags/package/model.keras'
    TIME_STEPS = 100
    FUTURE_DAYS = 100
    base_currency = 'KRW'
    target_currencies = ['USD', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'NZD', 'THB', 'HKD', 'TWD']
    
    # 모델 로드
    model = load_model(MODEL_PATH)
    
    # 미래 날짜 생성
    future_dates = [datetime.now() + timedelta(days=i) for i in range(1, FUTURE_DAYS + 1)]
    
    # 빈 DataFrame 초기화
    predictions_df = pd.DataFrame({'date': future_dates})
    
    # OpenSearch client and index setup
    opensearch_client = client
    index_name = "currency_forcast"
    setup_index(opensearch_client, index_name)

    # 각 통화에 대해 반복
    for target_currency in target_currencies:
        print(f"Predicting future rates for {target_currency}")
        
        # 환율 데이터 로드 및 결측치 처리
        start_date = "2012-01-01"
        end_date = datetime.now().strftime("%Y-%m-%d")
        exchange_df = get_historical_exchange_rates(base_currency, [target_currency], start_date, end_date)
        df = fill_na_with_avg(exchange_df[target_currency])
        
        # 데이터 정규화
        df = np.array(df).reshape(-1, 1)
        df, normalize = normalize_mult(df)
        
        # 미래 예측
        future_predictions = predict_future(model, df, TIME_STEPS, normalize, FUTURE_DAYS)
        
        # DataFrame에 예측 결과 추가
        predictions_df[target_currency] = future_predictions
    
    # Bulk 인덱싱을 위한 actions 생성
    actions = [
        {
            "_index": index_name,
            "_source": {
                "date": row['date'],
                "USD": row['USD'],
                "EUR": row['EUR'],
                "JPY": row['JPY'],
                "GBP": row['GBP'],
                "AUD": row['AUD'],
                "CAD": row['CAD'],
                "NZD": row['NZD'],
                "THB": row['THB'],
                "VND": row['VND'],
                "HKD": row['HKD'],
                "TWD": row['TWD'],
            }
        }
        for _, row in predictions_df.iterrows()
    ]
    
    # OpenSearch에 데이터 일괄 삽입
    helpers.bulk(opensearch_client, actions)
    print(f"Predictions successfully saved to OpenSearch index '{index_name}'.")

# Airflow DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    '05_Currency_Forecast',
    default_args=default_args,
    description='Predicts future currency exchange rates and uploads to OpenSearch daily',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    upload_task = PythonOperator(
        task_id='run_prediction_and_upload',
        python_callable=run_prediction_and_upload
    )

    upload_task
