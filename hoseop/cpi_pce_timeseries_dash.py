import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# CSV 파일에서 데이터 로드
def load_data():
    return pd.read_csv('/opt/airflow/data/credit_card_spending.csv', parse_dates=['ds'])

# Dash 애플리케이션 초기화
app = dash.Dash(__name__)

# 레이아웃 설정
app.layout = html.Div([
    html.H1("Credit Card Spending Forecast"),
    dcc.Graph(id='lineplot'),
])

# 그래프 업데이트 콜백
@app.callback(
    Output('lineplot', 'figure'),
    Input('lineplot', 'id')  # dummy input to trigger callback once
)
def update_graph(_):
    # CSV 파일에서 데이터 로드
    pce_eat_df = load_data()

    fig = go.Figure()

    # 예측 값 (yhat) 라인 추가
    fig.add_trace(go.Scatter(
        x=pce_eat_df['ds'],
        y=pce_eat_df['yhat'],
        mode='lines',
        name='Forecast (yhat)',
        line=dict(color='blue')
    ))

    # 신뢰 구간 (yhat_lower, yhat_upper) 영역 추가
    fig.add_trace(go.Scatter(
        x=pd.concat([pce_eat_df['ds'], pce_eat_df['ds'][::-1]]),
        y=pd.concat([pce_eat_df['yhat_upper'], pce_eat_df['yhat_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(173, 216, 230, 0.2)',  # Light blue fill for confidence interval
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name='Confidence Interval'
    ))

    # 레이아웃 설정
    fig.update_layout(
        title="Forecast of Credit Card Spending",
        xaxis_title="Date",
        yaxis_title="Spending",
        template="plotly_white"
    )

    return fig

# Dash 서버 실행
if __name__ == '__main__':
    app.run_server(debug=True)