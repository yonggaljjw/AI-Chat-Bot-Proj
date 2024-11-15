# test.py

from datetime import datetime
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
# from train import normalize_mult, create_dataset, FNormalizeMult, get_historical_exchange_rates, fill_na_with_avg

# 테스트 데이터를 준비하는 함수
def prepare_test_data(test_data, time_steps, normalize):
    test, _ = normalize_mult(test_data)  # test_data는 이미 numpy 배열 형태
    test_X, test_Y = create_dataset(test, time_steps)
    test_Y = FNormalizeMult(test_Y, normalize)
    return test_X, test_Y

# 모델 평가 및 시각화 함수
def evaluate_model(model_path, test_X, test_Y, normalize, currency):
    model = load_model(model_path)
    predictions = model.predict(test_X)
    predictions = FNormalizeMult(predictions, normalize)
    r2 = r2_score(test_Y, predictions)
    print(f"Currency: {currency}, R^2 Score: {r2}")
    
    # 실제값과 예측값을 그래프로 시각화
    plt.figure(figsize=(12, 6))
    plt.plot(test_Y, label="Actual Values")
    plt.plot(predictions, label="Predicted Values")
    plt.xlabel("Time Steps")
    plt.ylabel("Values")
    plt.title(f"Actual vs Predicted Values for {currency}")
    plt.legend()
    plt.show()

    return predictions

# 테스트를 위한 메인 함수
def main():
    MODEL_PATH = './model.keras'
    TIME_STEPS = 100
    
    # 테스트 데이터 로드 및 처리
    base_currency = 'KRW'
    target_currencies = ['USD', 'EUR', 'JPY', 'GBP', "GBP", "AUD", "CAD", "NZD", "THB", "HKD", "TWD"]
    start_date = "2012-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 환율 데이터 가져오기
    exchange_df = get_historical_exchange_rates(base_currency, target_currencies, start_date, end_date)
    
    # 각 target currency에 대해 반복
    for currency in target_currencies:
        print(f"Evaluating for currency: {currency}")
        
        # 해당 통화의 데이터 가져오기 및 결측치 처리
        df = fill_na_with_avg(exchange_df[currency])
        
        # 데이터 정규화
        df = np.array(df).reshape(-1, 1)
        df, normalize = normalize_mult(df)

        # 테스트 데이터 준비
        test_index = int(len(df) * 0.8)
        _, test = df[:test_index], df[test_index:]
        test_X, test_Y = prepare_test_data(test, TIME_STEPS, normalize)

        # 모델 평가 및 결과 시각화
        predictions = evaluate_model(MODEL_PATH, test_X, test_Y, normalize, currency)

if __name__ == "__main__":
    main()
