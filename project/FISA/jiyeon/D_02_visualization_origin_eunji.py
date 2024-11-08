import os
import pandas as pd
from datetime import datetime
from fredapi import Fred
import plotly.graph_objects as go

# FRED API 초기화 함수
def initialize_fred():
    api_key = os.getenv('FRED_API_KEY')
    return Fred(api_key=api_key)

# 데이터 조회 함수
def fetch_data(fred, series_id, start_date='2015-01-01', end_date=None):
    end_date = end_date or datetime.today().strftime('%Y-%m-%d')
    try:
        data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
        return data
    except ValueError as e:
        print(f"Error fetching data for {series_id}: {e}")
        return None

# 데이터 프레임 병합 함수
def merge_data_frames(data_frames):
    df = pd.DataFrame()
    for key, value in data_frames.items():
        if value is not None:
            temp_df = value.reset_index()
            temp_df.columns = ['date', key]
            if df.empty:
                df = temp_df
            else:
                df = pd.merge(df, temp_df, on='date', how='outer')
    return df

# 결측값 채우기 함수
def fill_missing_values(df):
    df.sort_values(by='date', inplace=True)
    df.fillna(method='ffill', inplace=True)
    return df

# 시각화 함수
def plot_economic_data(df, indicators):
    fig = go.Figure()

    # 왼쪽 y축과 오른쪽 y축에 표시할 각 지표 추가
    for indicator, y_axis in indicators.items():
        fig.add_trace(go.Scatter(
            x=df['date'], y=df[indicator],
            mode='lines', name=indicator,
            yaxis=y_axis
        ))

    # 레이아웃 설정
    fig.update_layout(
        title='주요 경제 지표 비교',
        xaxis_title='날짜',
        yaxis=dict(title='GDP 성장률 (%)', titlefont=dict(color='blue'), tickfont=dict(color='blue')),
        yaxis2=dict(title='연방기금금리(FFTR) 및 실업률 (%)', titlefont=dict(color='red'), tickfont=dict(color='red'),
                    anchor='x', overlaying='y', side='right'),
        legend=dict(x=0, y=1),
        template='plotly_dark'
    )
    fig.show()

# 주요 지표 데이터를 조회하고 처리하는 함수
def fetch_and_process_economic_data():
    fred = initialize_fred()
    series_ids = {
        'FFTR': 'DFEDTARU',
        'GDP': 'GDP',
        'GDP Growth Rate': 'A191RL1Q225SBEA',
        'PCE': 'PCE',
        'Core PCE': 'PCEPILFE',
        'CPI': 'CPIAUCSL',
        'Core CPI': 'CPILFESL',
        'Personal Income': 'PI',
        'Unemployment Rate': 'UNRATE',
        'ISM Manufacturing': 'MANEMP',
        'Durable Goods Orders': 'DGORDER',
        'Building Permits': 'PERMIT',
        'Retail Sales': 'RSAFS',
        'Consumer Sentiment': 'UMCSENT',
        'Nonfarm Payrolls': 'PAYEMS',
        'JOLTS Hires': 'JTSHIL'
    }
    data_frames = {name: fetch_data(fred, series_id) for name, series_id in series_ids.items()}
    
    # 데이터 병합 및 결측값 처리
    df = merge_data_frames(data_frames)
    df_filled = fill_missing_values(df)
    
    # 시각화할 지표와 축 설정
    indicators = {
        'GDP Growth Rate': 'y',
        'FFTR': 'y2',
        'Unemployment Rate': 'y2'
    }

    # 시각화 함수 호출
    plot_economic_data(df_filled, indicators)

# 실행 예제
fetch_and_process_economic_data()
