import dash
from dash import dcc, html
from prophet import Prophet
import matplotlib.pyplot as plt
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import base64
from io import BytesIO
# import plotly.graph_objects as go
import pandas as pd
import requests

# # CSV 파일에서 데이터 로드
# def load_data():
#     return pd.read_csv('/opt/airflow/data/credit_card_spending.csv', parse_dates=['ds'])

# # Dash 애플리케이션 초기화
# app = dash.Dash(__name__)

# # 레이아웃 설정
# app.layout = html.Div([
#     html.H1("Credit Card Spending Forecast"),
#     dcc.Graph(id='lineplot'),
# ])

# # 그래프 업데이트 콜백
# @app.callback(
#     Output('lineplot', 'figure'),
#     Input('lineplot', 'id')  # dummy input to trigger callback once
# )
# def update_graph(_):
#     # CSV 파일에서 데이터 로드
#     pce_eat_df = load_data()

#     fig = go.Figure()

#     # 예측 값 (yhat) 라인 추가
#     fig.add_trace(go.Scatter(
#         x=pce_eat_df['ds'],
#         y=pce_eat_df['yhat'],
#         mode='lines',
#         name='Forecast (yhat)',
#         line=dict(color='blue')
#     ))

#     # 신뢰 구간 (yhat_lower, yhat_upper) 영역 추가
#     fig.add_trace(go.Scatter(
#         x=pd.concat([pce_eat_df['ds'], pce_eat_df['ds'][::-1]]),
#         y=pd.concat([pce_eat_df['yhat_upper'], pce_eat_df['yhat_lower'][::-1]]),
#         fill='toself',
#         fillcolor='rgba(173, 216, 230, 0.2)',  # Light blue fill for confidence interval
#         line=dict(color='rgba(255,255,255,0)'),
#         hoverinfo="skip",
#         name='Confidence Interval'
#     ))

#     # 레이아웃 설정
#     fig.update_layout(
#         title="Forecast of Credit Card Spending",
#         xaxis_title="Date",
#         yaxis_title="Spending",
#         template="plotly_white"
#     )

#     return fig

# API 기본 URL과 분류 코드 설정
BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch/2IJKJSOY6OFOQZ28900C/json/kr/1/100000/601Y002/M/200001/202409/X/{}/DAV"
CODES = 1300

def pce_data_from_api():
    """API에서 데이터를 수집하고 병합합니다."""

    url = BASE_URL.format(CODES)
    response = requests.get(url)
    data = response.json()

    if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
        df = pd.DataFrame(data['StatisticSearch']['row'])
        item_name = df['ITEM_NAME2'].iloc[0]
        df = df[['TIME', 'DATA_VALUE']].rename(columns={'DATA_VALUE': item_name})

    else:
        print(f"데이터 없음: 코드 {CODES}")

    df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m')
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric)
    return df


def cpi_kosis_data():
    """KOSIS API에서 데이터를 수집하고 처리합니다."""
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList",
        "apiKey": "NGFlNDEwNzU4NTVjN2Y2ZTcyYzJiYmI5NjlhY2ExMzc=",
        "orgId": "101",
        "tblId": "DT_1J22112",
        "itmId": "T+",
        "objL1": "T10+",
        "objL2": "ALL",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "M",
        "startPrdDe": "202001",
        "endPrdDe": "202409",
        "outputFields": "NM PRD_DE"
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data)
    pivot_df = df.pivot_table(index='PRD_DE', columns='C2_NM', values='DT', aggfunc='max').reset_index()
    pivot_df['PRD_DE'] = pd.to_datetime(pivot_df['PRD_DE'], format='%Y%m')
    pivot_df.iloc[:, 1:] = pivot_df.iloc[:, 1:].apply(pd.to_numeric)
    pivot_df.rename(columns={'PRD_DE': 'TIME'}, inplace=True)
    
    return pivot_df

# 예측 및 시각화 함수 정의
def forecast_future(dataframe, column_name, periods=3):
    # Prophet이 요구하는 ds, y 열 이름으로 변경
    df_prophet = dataframe[['TIME', column_name]].rename(columns={'TIME': 'ds', column_name: 'y'})
    model = Prophet()
    model.fit(df_prophet)

    # 미래 날짜 생성 및 예측 수행
    future = model.make_future_dataframe(periods=periods, freq='MS')
    forecast = model.predict(future)

    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]


def plot_forecast_and_cpi(eat_df, feature_name, cpi_feature_name):
    # 예측 결과 얻기
    forecast_feature = forecast_future(eat_df, feature_name)
    forecast_cpi_feature = forecast_future(eat_df, cpi_feature_name)

    # 그래프 시각화
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 첫 번째 y축 (왼쪽): feature
    ax1.plot(forecast_feature['ds'], forecast_feature['yhat'], label='Card Spending', color="blue")
    ax1.fill_between(forecast_feature['ds'], forecast_feature['yhat_lower'], forecast_feature['yhat_upper'], color="blue", alpha=0.2)
    ax1.set_ylabel(f"PCE {feature_name} 지출", color="blue")
    ax1.tick_params(axis='y', labelcolor="blue")

    # 두 번째 y축 (오른쪽): cpi_feature
    ax2 = ax1.twinx()
    ax2.plot(forecast_cpi_feature['ds'], forecast_cpi_feature['yhat'], label='CPI', color="orange")
    ax2.fill_between(forecast_cpi_feature['ds'], forecast_cpi_feature['yhat_lower'], forecast_cpi_feature['yhat_upper'], color="orange", alpha=0.2)
    ax2.set_ylabel(f"{cpi_feature_name} 지수", color="orange")
    ax2.tick_params(axis='y', labelcolor="orange")

    # 범례 설정
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    plt.title(f"{feature_name} 지출 및 {cpi_feature_name} 지수 예측")
    
    # 이미지를 BytesIO 객체에 저장하고 base64 인코딩하여 반환
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# DjangoDash 애플리케이션 생성 및 레이아웃 정의
app = DjangoDash('forecast_dashboard')

app.layout = html.Div([
    html.H3("PCE 지출 및 CPI 예측", style={'textAlign': 'center'}),
    
    html.Div(id='forecast-graph-container'),
])

# 콜백 함수: 그래프 업데이트 및 렌더링
@app.callback(
   Output('forecast-graph-container', 'children'),
   Input('forecast-graph-container', 'id')  # 더미 입력을 사용해 콜백 트리거
)
def update_forecast_graph(_):
    
   pce_df = pce_data_from_api()
   cpi_df = cpi_kosis_data()

   eat_df = pd.merge(pce_df[['TIME', '식료품']], pd.concat([cpi_df['TIME'], cpi_df[['농축수산물', '가공식품']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_식료품'}))

   img_base64_str = plot_forecast_and_cpi(eat_df, eat_df.columns[1], eat_df.columns[2])
   
   return html.Img(src=f'data:image/png;base64,{img_base64_str}', style={'width': '100%', 'height': '100%'})