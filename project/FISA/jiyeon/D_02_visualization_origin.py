import pandas as pd
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html
from dash.dependencies import Input, Output
from fredapi import Fred
import pandas as pd
import os

fred = Fred(api_key=os.getenv('FRED_API_KEY'))
# !pip install PublicDataReader --upgrade

# 데이터 조회 함수
from datetime import datetime

# FRED API 설정
fred = Fred(api_key='5cafaa9a5f90981d7a9c005ea24ba83a')
end_date = datetime.today().strftime('%Y-%m-%d')

def fetch_data(series_id, start_date='2015-01-01', end_date=end_date):
    try:
        return fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
    except ValueError as e:
        print(f"Error fetching data for {series_id}: {e}")
        return None

# Dash 앱 생성
app = DjangoDash("simple_example", add_bootstrap_links=True)

# 레이아웃 설정
app.layout = html.Div([
    html.H1("경제 지표 대시보드"),
    dcc.Graph(id='economic-indicators-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1000*60*60*24,  # 24시간마다 업데이트 (밀리초 단위)
        n_intervals=0
    )
])

@app.callback(
    Output('economic-indicators-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    # 주요 지표 데이터 조회
    fftr = fetch_data('DFEDTARU')
    gdp_growth_rate = fetch_data('A191RL1Q225SBEA')
    unemployment_rate = fetch_data('UNRATE')

    # 데이터프레임으로 변환
    data_frames = {
        'FFTR': fftr,
        'GDP Growth Rate': gdp_growth_rate,
        'Unemployment Rate': unemployment_rate,
    }

    df_filled = pd.DataFrame()
    for key, value in data_frames.items():
        if value is not None:
            temp_df = value.reset_index()
            temp_df.columns = ['date', key]
            if df_filled.empty:
                df_filled = temp_df
            else:
                df_filled = pd.merge(df_filled, temp_df, on='date', how='outer')
    df_filled = df_filled.ffill()

    # 그래프 생성
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_filled['date'], y=df_filled['GDP Growth Rate'], mode='lines', name='GDP 성장률', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df_filled['date'], y=df_filled['FFTR'], mode='lines', name='연방기금금리(FFTR)', line=dict(color='red'), yaxis='y2'))
    fig.add_trace(go.Scatter(x=df_filled['date'], y=df_filled['Unemployment Rate'], mode='lines', name='실업률', line=dict(color='green'), yaxis='y2'))

    fig.update_layout(
        title='GDP 성장률과 연방기금금리, 실업률 비교 (좌우 축 사용)',
        xaxis={'title': '날짜'},
        yaxis={'title': 'GDP 성장률 (%)', 'titlefont': {'color': 'blue'}, 'tickfont': {'color': 'blue'}},
        yaxis2={'title': '연방기금금리(FFTR) 및 실업률 (%)', 'titlefont': {'color': 'red'}, 'tickfont': {'color': 'red'},
                'overlaying': 'y', 'side': 'right'}
    )

    return fig
