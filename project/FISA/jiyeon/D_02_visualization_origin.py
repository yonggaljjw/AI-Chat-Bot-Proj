
# !pip install fredapi
import pandas_datareader.data as web
import datetime

from fredapi import Fred
import pandas as pd
import os

# FRED API 키 설정
fred = Fred(api_key=FRED_API_KEY) 
fred = Fred(api_key=os.getenv('FRED_API_KEY'))
# !pip install PublicDataReader --upgrade

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
print(df.tail())

# 모든 변수에 대해 결측값 채우기
df_filled = pd.DataFrame()

for key, value in data_frames.items():
    if value is not None:
        temp_df = value.reset_index()
        temp_df.columns = ['date', key]
        if df_filled.empty:
            df_filled = temp_df
        else:
            df_filled = pd.merge(df_filled, temp_df, on='date', how='outer')

# 결측값을 직전 값으로 채우기
df_filled.sort_values(by='date', inplace=True)
df_filled.fillna(method='ffill', inplace=True)

# 결측값 채운 결과 확인
print("결측값 채운 데이터프레임 확인:")
print(df_filled.tail())


# 시각화

import pandas as pd
import plotly.graph_objects as go

# 결측값 처리 코드
df_filled = pd.DataFrame()

for key, value in data_frames.items():
    if value is not None:
        temp_df = value.reset_index()
        temp_df.columns = ['date', key]
        if df_filled.empty:
            df_filled = temp_df
        else:
            df_filled = pd.merge(df_filled, temp_df, on='date', how='outer')

# 결측값을 직전 값으로 채우기
df_filled.sort_values(by='date', inplace=True)
df_filled.fillna(method='ffill', inplace=True)

# 결측값 채운 결과 확인
print("결측값 채운 데이터프레임 확인:")
print(df_filled.tail())

# 시각화 코드
fig = go.Figure()

# GDP 성장률 - 좌측 y축
fig.add_trace(go.Scatter(x=df_filled['date'], y=df_filled['GDP Growth Rate'],
mode='lines', name='GDP 성장률',
line=dict(color='blue')))

# FFTR - 우측 y축
fig.add_trace(go.Scatter(x=df_filled['date'], y=df_filled['FFTR'],
mode='lines', name='연방기금금리(FFTR)',
line=dict(color='red'), yaxis='y2'))

# 실업률 - 우측 y축
fig.add_trace(go.Scatter(x=df_filled['date'], y=df_filled['Unemployment Rate'],
mode='lines', name='실업률',
line=dict(color='green'), yaxis='y2'))

# 레이아웃 설정
fig.update_layout(
    title='GDP 성장률과 연방기금금리, 실업률 비교 (좌우 축 사용)',
    xaxis_title='날짜',
    yaxis=dict(
        title='GDP 성장률 (%)',
        titlefont=dict(color='blue'),
        tickfont=dict(color='blue')
    ),
    yaxis2=dict(
        title='연방기금금리(FFTR) 및 실업률 (%)',
        titlefont=dict(color='red'),
        tickfont=dict(color='red'),
        anchor='x',
        overlaying='y',
        side='right'
    ),
    legend=dict(x=0, y=1),
    template='plotly_dark'
)

fig.show()
