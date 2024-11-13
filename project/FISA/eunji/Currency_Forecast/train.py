# train.py

import numpy as np
import tensorflow as tf
import pandas as pd
from tensorflow.keras.layers import Input, Dense, LSTM, Conv1D, Dropout, Bidirectional, Multiply, Permute, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split
import yfinance as yf
from datetime import datetime
from tensorflow.keras.models import load_model

# Attention 블록 정의
def attention_3d_block(inputs):
    input_dim = int(inputs.shape[2])
    a = Dense(input_dim, activation='softmax')(inputs)
    a_probs = Permute((1, 2), name='attention_vec')(a)
    return Multiply()([inputs, a_probs])

# 모델 정의
def attention_model(input_dims, time_steps, lstm_units):
    inputs = Input(shape=(time_steps, input_dims))
    x = Conv1D(filters=64, kernel_size=1, activation='relu')(inputs)
    x = Dropout(0.1)(x)
    lstm_out = Dropout(0.3)(Bidirectional(LSTM(lstm_units, return_sequences=True))(x))
    lstm_out2 = Dropout(0.3)(Bidirectional(LSTM(lstm_units, return_sequences=True))(lstm_out))
    attention_mul = Flatten()(attention_3d_block(lstm_out2))
    output = Dense(1, activation='linear')(attention_mul)
    return Model(inputs=[inputs], outputs=output)

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

# R^2 지표 정의
def r2_keras(y_true, y_pred):
    SS_res = tf.reduce_sum(tf.square(y_true - y_pred))
    SS_tot = tf.reduce_sum(tf.square(y_true - tf.reduce_mean(y_true)))
    return 1 - SS_res / (SS_tot + tf.keras.backend.epsilon())

# 데이터셋 생성
def create_dataset(dataset, look_back):
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back - 1):
        dataX.append(dataset[i:(i + look_back), :])
        dataY.append(dataset[i + look_back, :])
    return np.array(dataX), np.array(dataY)

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

# 모델 학습 함수
def train_model(train_X, train_Y, input_dims, time_steps, lstm_units, model_path, epochs=20, batch_size=64):
    model = attention_model(input_dims, time_steps, lstm_units)
    model.compile(loss='mse', optimizer='adam', metrics=['mse'])
    model.fit(
        [train_X], train_Y,
        epochs=epochs, batch_size=batch_size, validation_split=0.25,
        callbacks=[
            EarlyStopping(monitor='val_loss', patience=10, mode='min'),
            ModelCheckpoint(model_path, monitor='val_loss', save_best_only=True, mode='min')
        ]
    )
    model.save(model_path)

# 학습을 위한 메인 함수
def main():
    base_currency = 'KRW'
    target_currencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP']
    start_date = "2012-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 환율 데이터 가져오기
    exchange_df = get_historical_exchange_rates(base_currency, target_currencies, start_date, end_date)
    df = fill_na_with_avg(exchange_df['GBP'])

    # 데이터 분할 및 준비
    test_index = int(len(df) * 0.8)
    train_full, test = df[:test_index], df[test_index:]
    val_index = int(len(train_full) * 0.75)
    train, valid = train_full[:val_index], train_full[val_index:]

    train = np.array(train).reshape(-1, 1)
    train, normalize = normalize_mult(train)
    TIME_STEPS = 100
    INPUT_DIMS = 1
    LSTM_UNITS = 64
    MODEL_PATH = './model.keras'

    train_X, _ = create_dataset(train, TIME_STEPS)
    _, train_Y = create_dataset(train[:, 0].reshape(len(train), 1), TIME_STEPS)

    # 모델 학습
    train_model(train_X, train_Y, INPUT_DIMS, TIME_STEPS, LSTM_UNITS, MODEL_PATH)

if __name__ == "__main__":
    main()
