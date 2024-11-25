# test.py

from datetime import datetime
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from train import normalize_mult, create_dataset, FNormalizeMult, get_historical_exchange_rates, fill_na_with_avg


# 테스트 데이터를 준비하는 함수
def prepare_test_data(test_data, time_steps, normalize):
    test, _ = normalize_mult(test_data)  # test_data는 이미 numpy 배열 형태
    test_X, test_Y = create_dataset(test, time_steps)
    test_Y = FNormalizeMult(test_Y, normalize)
    return test_X, test_Y

# 미래 예측 함수
def predict_future(model, last_sequence, future_steps, normalize):
    future_predictions = []
    current_sequence = last_sequence.copy()

    for _ in range(future_steps):
        prediction = model.predict(current_sequence[np.newaxis, :, :])[0, 0]
        # Denormalize prediction
        denormalized_prediction = prediction * (normalize[0, 1] - normalize[0, 0]) + normalize[0, 0]
        future_predictions.append(denormalized_prediction)

        # Update the sequence
        current_sequence = np.roll(current_sequence, -1, axis=0)
        current_sequence[-1, 0] = prediction  # Append the new prediction to the sequence

    return np.array(future_predictions)

# 모델 평가 및 시각화 함수
def evaluate_model(model_path, test_X, test_Y, normalize, currency, future_steps, test_time):
    model = load_model(model_path)

    # Generate predictions for test data
    predictions = model.predict(test_X)
    predictions = FNormalizeMult(predictions, normalize).flatten()  # Flatten to 1D array
    test_Y = test_Y.flatten()  # Flatten to 1D array

    # Ensure test_time matches test_Y
    test_time = test_time[:len(test_Y)]  # Truncate test_time to match test_Y length

    # R^2 Score
    r2 = r2_score(test_Y, predictions)
    print(f"Currency: {currency}, R^2 Score: {r2}")

    # Future Predictions
    last_sequence = test_X[-1]
    future_predictions = predict_future(model, last_sequence, future_steps, normalize)

    # Generate future time axis
    future_time = pd.date_range(test_time[-1], periods=future_steps + 1, freq='D')[1:]

    # Plot actual, predicted, and future values
    plt.figure(figsize=(12, 6))
    plt.plot(test_time, test_Y, label="Actual Values")
    plt.plot(test_time, predictions, label="Predicted Values")
    plt.plot(future_time, future_predictions, label="Future Predictions", linestyle="--")
    plt.xlabel("Time")
    plt.ylabel("Values")
    plt.title(f"Actual, Predicted, and Future Forecasts for {currency}")
    plt.legend()
    plt.grid(True)
    plt.show()

    return predictions, future_predictions


# 테스트를 위한 메인 함수
def main():
    TIME_STEPS = 60
    FUTURE_STEPS = 60  # Number of future days to predict

    target_currencies = ['USD', 'CNY', 'JPY', 'EUR']
    exchange_df = load_data_from_sql()
    if exchange_df.empty:
        print("No data loaded. Exiting.")
        return

    exchange_df['TIME'] = pd.to_datetime(exchange_df['TIME'], errors='coerce')
    exchange_df = exchange_df.dropna().sort_values(by='TIME')  # Drop rows with NaT or NaN
    exchange_df['USD'] = pd.to_numeric(exchange_df['USD'], errors='coerce')  # 숫자로 변환
    exchange_df['CNY'] = pd.to_numeric(exchange_df['CNY'], errors='coerce')  # 숫자로 변환
    exchange_df['JPY'] = pd.to_numeric(exchange_df['JPY'], errors='coerce')  # 숫자로 변환
    exchange_df['EUR'] = pd.to_numeric(exchange_df['EUR'], errors='coerce')  # 숫자로 변환

    # 각 target currency에 대해 반복
    for currency in target_currencies:
        print(f"Evaluating for currency: {currency}")

        MODEL_PATH = f'./{currency}.h5'

        # 해당 통화의 데이터 가져오기 및 결측치 처리
        df = fill_na_with_avg(exchange_df[currency])
        timestamps = exchange_df['TIME'].values

        # 데이터 정규화
        df = np.array(df).reshape(-1, 1)
        df, normalize = normalize_mult(df)

        # 테스트 데이터 준비
        test_index = int(len(df) * 0.8)
        _, test = df[:test_index], df[test_index:]
        _, test_time = timestamps[:test_index], timestamps[test_index:]
        test_X, test_Y = prepare_test_data(test, TIME_STEPS, normalize)

        # 모델 평가 및 결과 시각화
        predictions, future_predictions = evaluate_model(MODEL_PATH, test_X, test_Y, normalize, currency, FUTURE_STEPS, test_time)

if __name__ == "__main__":
    main()
