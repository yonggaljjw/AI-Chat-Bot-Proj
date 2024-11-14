from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from train import normalize_mult, get_historical_exchange_rates, fill_na_with_avg

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
def main():
    MODEL_PATH = './model.keras'
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
    
    # CSV 파일로 저장
    predictions_df.to_csv("future_predictions_all_currencies.csv", index=False)
    print("Predictions saved to future_predictions_all_currencies.csv")

if __name__ == "__main__":
    main()
