import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html
import requests
from chatbot.sql import engine


def load_currency_rate_from_sql():
    try:
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM currency_rate"
        currency_rate = pd.read_sql(query, engine)

        return currency_rate
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()
    
def load_currency_forecast_from_sql():
    try:
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM currency_forecast"
        currency_forecast = pd.read_sql(query, engine)

        return currency_forecast
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()    
    
def load_and_preprocess_data():
    """
    통화 환율 및 예측 데이터를 로드하고 전처리하는 함수.
    """
    # 데이터 로드
    currency_rate = load_currency_rate_from_sql()
    currency_forecast = load_currency_forecast_from_sql()

    # 날짜 데이터를 datetime 형식으로 변환
    currency_rate['TIME'] = pd.to_datetime(currency_rate['TIME'])
    currency_forecast['date'] = pd.to_datetime(currency_forecast['date'])

    # 숫자형 데이터로 변환 (오류 발생 시 NaN 처리)
    for col in ['USD', 'CNY', 'JPY', 'EUR']:
        currency_rate[col] = pd.to_numeric(currency_rate[col], errors='coerce')
        currency_forecast[col] = pd.to_numeric(currency_forecast[col], errors='coerce')

    # 열 이름을 통일
    currency_forecast.rename(columns={'date': 'TIME'}, inplace=True)

    # 데이터 구분을 위한 'source' 열 추가
    currency_rate['source'] = 'actual'
    currency_forecast['source'] = 'predict'

    # 데이터 결합 및 시간 순으로 정렬
    combined_data = pd.concat([currency_rate, currency_forecast], ignore_index=True).sort_values(by='TIME')

    return combined_data

def create_currency_plot():
    """
    통화 환율 데이터를 기반으로 Plotly 그래프를 생성하는 함수.
    """
    combined_data = load_and_preprocess_data()
    # Plotly 그래프 객체 생성
    fig = go.Figure()

    # 분석할 통화 목록 및 데이터 출처 구분
    currencies = ["USD", "CNY", "JPY", "EUR"]
    sources = combined_data['source'].unique()

    # 통화 및 데이터 출처별로 그래프 라인 추가
    for currency in currencies:
        for source in sources:
            # 특정 통화 및 출처에 해당하는 데이터 필터링
            filtered_data = combined_data[combined_data['source'] == source]
            fig.add_trace(
                go.Scatter(
                    x=filtered_data['TIME'],
                    y=filtered_data[currency],
                    mode='lines',
                    name=f"{currency} ({source})",
                    visible=(currency == "USD"),  # 초기에는 USD 데이터만 표시
                )
            )

    # 드롭다운 메뉴 생성
    dropdown_buttons = [
        {
            "label": currency,
            "method": "update",
            "args": [
                {
                    "visible": [
                        (currency == c) for c in currencies for _ in sources
                    ],  # 선택된 통화에 해당하는 그래프만 표시
                },
                {
                    "title": f"Currency Rates Over Time - {currency}",  # 그래프 제목 업데이트
                },
            ],
        }
        for currency in currencies
    ]

    # 그래프 레이아웃 설정
    fig.update_layout(
        updatemenus=[
            {
                "buttons": dropdown_buttons,  # 드롭다운 메뉴 추가
                "direction": "down",  # 드롭다운 메뉴 방향 설정
                "showactive": True,  # 활성 메뉴 표시
            }
        ],
        title="Currency Rates Over Time - USD",  # 초기 제목 설정
        xaxis_title="Time",  # X축 제목
        yaxis_title="Currency Value",  # Y축 제목
    )

    return to_html(fig)


