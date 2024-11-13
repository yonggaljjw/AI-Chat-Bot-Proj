import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from datetime import datetime, timedelta
import yfinance as yf
from train import normalize_mult, create_dataset, FNormalizeMult, r2_keras

# 필요한 함수들 정의 (이미 있는 것으로 가정)
# - normalize_mult
# - create_dataset
# - FNormalizeMult

# 모델 및 설정 값
MODEL_PATH = './model.keras'
TIME_STEPS = 100
BASE_CURRENCY = 'KRW'
TARGET_CURRENCY = 'USD'

# 저장된 모델 로드
def load_trained_model(model_path, custom_objects=None):
    return load_model(model_path, custom_objects=custom_objects)
# 저장된 모델 로드
model = load_trained_model(MODEL_PATH, custom_objects={'r2_keras': r2_keras})

# 데이터셋 생성
def create_dataset(dataset, look_back):
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back - 1):
        dataX.append(dataset[i:(i + look_back), :])
        dataY.append(dataset[i + look_back, :])
    return np.array(dataX), np.array(dataY)

# 예측 수행 함수
def make_predictions(model, data, normalize, time_steps):
    # 데이터 정규화
    test, _ = normalize_mult(data.values.reshape(-1, 1))
    test_X, _ = create_dataset(test, time_steps)
    
    # 예측 수행
    predictions = model.predict(test_X)
    
    # 정규화 해제
    predictions = FNormalizeMult(predictions, normalize)
    return predictions

# # 미래 예측 함수
# def predict_future(model, initial_data, normalize, time_steps, future_steps):
#     predictions = []
#     last_sequence = initial_data[-time_steps:]  # 마지막 시퀀스 가져오기
    
#     for _ in range(future_steps):
#         # 시퀀스를 모델 입력 형식으로 변경
#         input_data = last_sequence.reshape(1, time_steps, -1)
        
#         # 예측 수행
#         pred = model.predict(input_data)
#         pred = FNormalizeMult(pred, normalize)  # 정규화 해제
        
#         # 예측 결과 저장
#         predictions.append(pred[0, 0])
        
#         # 시퀀스 업데이트
#         last_sequence = np.append(last_sequence, pred).reshape(-1, 1)[1:]
    
#     return predictions



# 최근 100일 데이터 가져오기
def get_recent_data(base_currency, target_currency, days=100):
    end_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
    # end_date = datetime.now().strftime("%Y-%m-%d")
    # start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    symbol = f"{target_currency}{base_currency}=X"
    data = yf.Ticker(symbol).history(start=start_date, end=end_date)
    return data[['Close']]

# 예측 및 결과 저장
def predict_and_save(data, model, time_steps, normalize, output_path='predictions.csv'):
    predictions = make_predictions(model, data, normalize, time_steps)
    
    # 날짜와 예측 결과 결합
    future_dates = pd.date_range(start=data.index[-1] + timedelta(days=1), periods=len(predictions), freq='D')
    result_df = pd.DataFrame({'Date': future_dates, 'Predicted_Close': predictions.flatten()})
    
    # 결과를 CSV로 저장
    result_df.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path}")

# 워크플로 실행
if __name__ == "__main__":
    # 데이터 가져오기
    data = get_recent_data(BASE_CURRENCY, TARGET_CURRENCY, days=100)
    
    # 데이터 정규화
    data_values, normalize = normalize_mult(data.values)
    data['Normalized_Close'] = data_values

    # 예측 수행 및 결과 저장
    predict_and_save(data, model, TIME_STEPS, normalize)
