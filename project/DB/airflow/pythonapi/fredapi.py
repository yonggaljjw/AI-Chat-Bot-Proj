import pandas_datareader.data as web
import datetime
from fredapi import Fred
import pandas as pd

# FRED API 키 설정
fred = Fred(api_key='5cafaa9a5f90981d7a9c005ea24ba83a')  ############ API 키 외부유출 조심해 주세요~ ##################

# # 데이터 조회 함수
# def fetch_data(series_id, start_date='2000-01-01', end_date='2023-12-31'):
#     try:
#         data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
#         return data
#     except ValueError as e:
#         print(f"Error fetching data for {series_id}: {e}")
#         return None

# # 데이터 프레임으로 변환
# gdp_df = pd.DataFrame(gdp, columns=['GDP'])
# pce_df = pd.DataFrame(pce, columns=['PCE'])
# cpi_df = pd.DataFrame(cpi, columns=['CPI'])

# # 데이터 출력
# print("GDP Data:\n", gdp_df.head())
# print("PCE Data:\n", pce_df.head())
# print("CPI Data:\n", cpi_df.head())

# # 데이터 출력
# print("GDP Data:\n", gdp_df.tail())
# print("PCE Data:\n", pce_df.tail())
# print("CPI Data:\n", cpi_df.tail())

"""### 주요 지표 시리즈 ID
```
fftr = fetch_data('DFEDTARU')   #ederal Funds Target Range - Upper Limit
gdp = fetch_data('GDP')
gdp_growth_rate = fetch_data('A191RL1Q225SBEA')
pce = fetch_data('PCE')
core_pce = fetch_data('PCEPILFE')
cpi = fetch_data('CPIAUCSL')
core_cpi = fetch_data('CPILFESL')
personal_income = fetch_data('PI')
unemployment_rate = fetch_data('UNRATE')
ism_manufacturing = fetch_data('MANEMP')
ism_non_manufacturing = fetch_data('NAPMNMI')       ## 오류나서 제외 함
durable_goods_orders = fetch_data('DGORDER')
building_permits = fetch_data('PERMIT')
retail_sales = fetch_data('RSAFS')
consumer_sentiment = fetch_data('UMCSENT')
nonfarm_payrolls = fetch_data('PAYEMS')
jolts_hires = fetch_data('JTSHIL')
```

> 우선 전체 키워드와 저희가 찾는 정보랑 매칭이 안되는 것도 있긴한데, 테스트 먼저 해보고 있습니다.

"""

# API_KEY = '5cafaa9a5f90981d7a9c005ea24ba83a'
# fred = Fred(api_key=API_KEY)
# # 주요 지표 데이터 조회
# gdp = fetch_data('GDP')
# gdp_growth_rate = fetch_data('A191RL1Q225SBEA')
# pce = fetch_data('PCE')
# core_pce = fetch_data('PCEPILFE')
# cpi = fetch_data('CPIAUCSL')
# core_cpi = fetch_data('CPILFESL')
# personal_income = fetch_data('PI')
# unemployment_rate = fetch_data('UNRATE')
# ism_manufacturing = fetch_data('MANEMP')
# durable_goods_orders = fetch_data('DGORDER')
# building_permits = fetch_data('PERMIT')
# retail_sales = fetch_data('RSAFS')
# consumer_sentiment = fetch_data('UMCSENT')
# nonfarm_payrolls = fetch_data('PAYEMS')
# jolts_hires = fetch_data('JTSHIL')

# # 유효한 데이터만 데이터 프레임으로 변환
# data = {
#     'GDP': gdp,
#     'GDP Growth Rate': gdp_growth_rate,
#     'PCE': pce,
#     'Core PCE': core_pce,
#     'CPI': cpi,
#     'Core CPI': core_cpi,
#     'Personal Income': personal_income,
#     'Unemployment Rate': unemployment_rate,
#     'ISM Manufacturing': ism_manufacturing,
#     'ISM Non-Manufacturing': ism_non_manufacturing,
#     'Durable Goods Orders': durable_goods_orders,
#     'Building Permits': building_permits,
#     'Retail Sales': retail_sales,
#     'Consumer Sentiment': consumer_sentiment,
#     'Nonfarm Payrolls': nonfarm_payrolls,
#     'JOLTS Hires': jolts_hires
# }

# # 데이터 출력
# for key, value in data.items():
#     if value is not None:
#         print(f"{key} Data:\n", value.head())

# API_KEY = '5cafaa9a5f90981d7a9c005ea24ba83a'
# fred = Fred(api_key=API_KEY)

# 데이터 조회 함수
from datetime import datetime

# 현재 날짜를 end_date로 사용
end_date = datetime.today().strftime('%Y-%m-%d')

# 데이터 가져오기 함수
def fetch_data(series_id, start_date='2015-01-01', end_date=end_date):
    try:
        data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
        return data
    except ValueError as e:
        print(f"Error fetching data for {series_id}: {e}")
        return None


# 주요 지표 데이터 조회
fftr = fetch_data('DFEDTARU')
gdp = fetch_data('GDP')
gdp_growth_rate = fetch_data('A191RL1Q225SBEA')
pce = fetch_data('PCE')
core_pce = fetch_data('PCEPILFE')
cpi = fetch_data('CPIAUCSL')
core_cpi = fetch_data('CPILFESL')
personal_income = fetch_data('PI')
unemployment_rate = fetch_data('UNRATE')
ism_manufacturing = fetch_data('MANEMP')
durable_goods_orders = fetch_data('DGORDER')
building_permits = fetch_data('PERMIT')
retail_sales = fetch_data('RSAFS')
consumer_sentiment = fetch_data('UMCSENT')
nonfarm_payrolls = fetch_data('PAYEMS')
jolts_hires = fetch_data('JTSHIL')

# 데이터프레임으로 변환
data_frames = {
    'FFTR': fftr,
    'GDP': gdp,
    'GDP Growth Rate': gdp_growth_rate,
    'PCE': pce,
    'Core PCE': core_pce,
    'CPI': cpi,
    'Core CPI': core_cpi,
    'Personal Income': personal_income,
    'Unemployment Rate': unemployment_rate,
    'ISM Manufacturing': ism_manufacturing,
    'Durable Goods Orders': durable_goods_orders,
    'Building Permits': building_permits,
    'Retail Sales': retail_sales,
    'Consumer Sentiment': consumer_sentiment,
    'Nonfarm Payrolls': nonfarm_payrolls,
    'JOLTS Hires': jolts_hires
}

# 데이터프레임 병합
df = pd.DataFrame()
for key, value in data_frames.items():
    if value is not None:
        temp_df = value.reset_index()
        temp_df.columns = ['date', key]
        if df.empty:
            df = temp_df
        else:
            df = pd.merge(df, temp_df, on='date', how='outer')

# 결과 출력
print(df.head())

### % 단위로 하나의 그래프에 넣을 수 있는 거시경제지표만 우선 테스트
import matplotlib.pyplot as plt

# FFTR, Unemployment Rate, GDP Growth Rate 열만 선택
df_selected = df[['date', 'FFTR', 'Unemployment Rate', 'GDP Growth Rate']]

# 시각화
plt.figure(figsize=(10, 6))
plt.plot(df_selected['date'], df_selected['FFTR'], label='FFTR', color='blue')
plt.plot(df_selected['date'], df_selected['Unemployment Rate'], label='Unemployment Rate', color='green')
plt.plot(df_selected['date'], df_selected['GDP Growth Rate'], label='GDP Growth Rate', color='red')

plt.xlabel('Date')
plt.ylabel('Percentage (%)')
plt.title('FFTR, Unemployment Rate, GDP Growth Rate Over Time')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 엑셀 파일로 저장
output_file = '주요 증시 데이터.xlsx'
df.to_excel(output_file, index=False)

# 결과 출력
print(f"Data has been saved to {output_file}")

"""# 증시 데이터 전처리

> 행 기준, 데이터가 빈 경우 그 행 삭제
"""

from google.colab import drive

# 구글 드라이브 마운트
drive.mount('/content/drive')

# 파일 경로 설정
file_path = '/content/drive/MyDrive/미래에셋X네이버 공모전/주요 증시 데이터.xlsx'

import pandas as pd
# 엑셀 파일 불러오기
df = pd.read_excel(file_path, sheet_name='Sheet1')

# 빈 열 삭제
df_cleaned = df.dropna(axis=0, how='any')

# 새로운 엑셀 파일로 저장
output_path = '/content/drive/MyDrive/미래에셋X네이버 공모전/주요 증시 데이터_열전처리.xlsx'
df_cleaned.to_excel(output_path, index=False)


print("빈 열이 삭제된 파일이 저장되었습니다.")

"""### 파생변수 생성
전분기 대비 ffrt가 '상승/동일/하락'한 경우, '1', '2', '3'으로 데이터를 처리
"""

# 엑셀 파일 경로
Derived_vari_file = '/content/drive/MyDrive/미래에셋X네이버 공모전/주요 증시 데이터_열전처리.xlsx'

# 엑셀 파일 불러오기
df = pd.read_excel(Derived_vari_file)

# 'FFTR_change' 파생변수 생성
df['FFTR_change'] = df['FFTR'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

# 새로운 엑셀 파일로 저장
output_path_with_fftr_change = '/content/drive/MyDrive/미래에셋X네이버 공모전/fftr_change.xlsx'
df.to_excel(output_path_with_fftr_change, index=False)

print("FFTR 변화에 따른 파생변수가 추가된 파일이 저장되었습니다.")

"""# 분류분석- LSTM"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.metrics import mean_squared_error, r2_score

# 엑셀 파일 경로를 변수에 저장
Derived_vari_file = '/content/drive/MyDrive/미래에셋X네이버 공모전/fftr_change.xlsx'

# 엑셀 파일 불러오기
df = pd.read_excel(Derived_vari_file)

# 'date' 열을 datetime 형식으로 변환
df['date'] = pd.to_datetime(df['date'])

# NaN 값을 가진 행 삭제
df = df.dropna()

# 'date' 열을 인덱스로 설정
df.set_index('date', inplace=True)

# Feature와 Target 변수 분리
X = df.drop(columns=['FFTR'])
y = df['FFTR']



X

# 데이터 스케일링
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)
# y_scaled = scaler.transform(y.values.reshape(-1, 1))

# LSTM 입력 형식에 맞게 데이터 변환
def prepare_lstm_data(X, y, time_step=1, split_ratio=0.8):
    def create_dataset(X, y, time_step):
        Xs, ys = [], []
        for i in range(len(X) - time_step):
            Xs.append(X[i:(i + time_step), :])
            ys.append(y[i + time_step])
        return np.array(Xs), np.array(ys)

    # 데이터셋 생성
    X_lstm, y_lstm = create_dataset(X, y, time_step)

    # 학습/테스트 데이터 분할
    split = int(split_ratio * len(X_lstm))
    X_train, X_test = X_lstm[:split], X_lstm[split:]
    y_train, y_test = y_lstm[:split], y_lstm[split:]

    return X_train, y_train, X_test, y_test

time_step = 12
X_train, y_train, X_test, y_test = prepare_lstm_data(X_scaled, y, time_step)

# LSTM 모델 정의
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, X.shape[1])))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(1))

model.compile(optimizer='adam', loss='mean_squared_error')
model.summary()

# 모델 학습
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test), verbose=1)

# 모델 예측
y_pred = model.predict(X_test)

# 예측 결과 역스케일링
y_pred_inv = scaler.inverse_transform(y_pred)
y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))

# 성능 평가
mse = mean_squared_error(y_test_inv, y_pred_inv)
r2 = r2_score(y_test_inv, y_pred_inv)

print(f'Mean Squared Error: {mse}')
print(f'R^2 Score: {r2}')



"""
# LSTM - 윈도우 1~11 사이에서 확인했을 때
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.metrics import mean_squared_error, r2_score

from google.colab import drive
drive.mount('/content/drive')

# 엑셀 파일 경로를 변수에 저장
Derived_vari_file = '/content/drive/MyDrive/미래에셋X네이버 공모전/fftr_change.xlsx'

# 엑셀 파일 불러오기
df = pd.read_excel(Derived_vari_file)

# 'date' 열을 datetime 형식으로 변환
df['date'] = pd.to_datetime(df['date'])

# NaN 값을 가진 행 삭제
df = df.dropna()

# 'date' 열을 인덱스로 설정
df.set_index('date', inplace=True)

# Feature와 Target 변수 분리
X = df.drop(columns=['FFTR'])
y = df['FFTR']

def prepare_lstm_data(X, y, time_step=1, split_ratio=0.8):
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # LSTM 입력 형식에 맞게 데이터 변환
    def create_dataset(X, y, time_step):
        Xs, ys = [], []
        for i in range(len(X) - time_step):
            Xs.append(X[i:(i + time_step), :])
            ys.append(y[i + time_step])
        return np.array(Xs), np.array(ys)

    # 데이터셋 생성
    X_lstm, y_lstm = create_dataset(X_scaled, y, time_step)

    # 학습/테스트 데이터 분할
    split = int(split_ratio * len(X_lstm))
    X_train, X_test = X_lstm[:split], X_lstm[split:]
    y_train, y_test = y_lstm[:split], y_lstm[split:]

    return X_train, y_train, X_test, y_test

# 사용 예시
time_step = 12

result = {}
for i in range(1, time_step):
    time_step = i
    X_train, y_train, X_test, y_test = prepare_lstm_data(X, y, time_step)

    # LSTM 모델 정의
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(time_step, X.shape[1])))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.summary()

    # 모델 학습
    model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test), verbose=1)

    # 모델 예측
    y_pred = model.predict(X_test)


    # 성능 평가
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f'Mean Squared Error: {mse}')
    print(f'R^2 Score: {r2}')
    result[time_step] = {'mse': mse, 'r2':r2...