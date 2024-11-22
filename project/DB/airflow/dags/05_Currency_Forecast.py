from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
from airflow import DAG
from airflow.operators.python import PythonOperator
from dotenv import load_dotenv
import os
import pymysql
from sqlalchemy import create_engine

load_dotenv()

# 데이터베이스 연결 정보
username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
database = 'team5'
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}")



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
    MODEL_PATH = './dags/package/model.h5'
    TIME_STEPS = 100
    FUTURE_DAYS = 100
    base_currency = 'KRW'
    target_currencies = ['CAD', 'JPY', 'USD', 'AED', 'AUD', 'BHD', 'CHF', 'CNH', 'DKK', 
                         'EUR', 'GBP', 'HKD', 'IDR', 'KWD', 'MYR', 'NOK', 'NZD', 'SAR', 'SEK', 'SGD', 'THB']
    
    # 모델 로드
    model = load_model(MODEL_PATH)
    
    # 미래 날짜 생성
    future_dates = [datetime.now() + timedelta(days=i) for i in range(1, FUTURE_DAYS + 1)]
    
    # 빈 DataFrame 초기화
    predictions_df = pd.DataFrame({'date': future_dates})

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
    
    # MySQL에 데이터 업로드
    predictions_df.to_sql(name='currency_forecast', con=engine, if_exists='replace', index=False)
    print("Predictions successfully saved to MySQL database 'currency_forecast' table.")

# Airflow DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 5,
    'retry_delay': timedelta(hours=1),
}

with DAG(
    '05_Currency_Forecast',
    default_args=default_args,
    description='Predicts future currency exchange rates and uploads to MySQL daily',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    upload_task = PythonOperator(
        task_id='run_prediction_and_upload',
        python_callable=run_prediction_and_upload
    )

    upload_task
