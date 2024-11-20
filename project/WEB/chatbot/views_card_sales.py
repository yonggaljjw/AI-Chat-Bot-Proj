from django.shortcuts import render
import plotly.graph_objs as go
from plotly.io import to_html
import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine
import pymysql
import datetime

def load_card_sales_data_from_sql():
    try:
        # MySQL 연결 문자열 생성
        db_settings = settings.DATABASES['default']
        connection_string = f"mysql+pymysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"

        # SQLAlchemy 엔진 생성
        engine = create_engine(connection_string)

        # 가장 최신의 년월을 선택하는 쿼리
        query = """
        SELECT * FROM card_sales
        WHERE 년월 = (
            SELECT MAX(년월) FROM card_sales
        )
        """
        card_sales = pd.read_sql(query, engine)

        return card_sales

    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()

def card_total_sales_ladar_view(request):
    """카드사별 사용금액 비교 레이더 차트 뷰"""
    card_sales = load_card_sales_data_from_sql()

    if card_sales.empty:
        return render(request, "dashboard_hoseop.html", {"error_message": "데이터를 불러올 수 없습니다."})

    card_companies = [
        '롯데카드', '비씨카드(자체)', '삼성카드', '신한카드',
        '우리카드', '하나카드', '현대카드', 'KB국민카드'
    ]

    # 데이터 변환: 백만원 단위로 계산
    values = [card_sales[company].sum() / 1_000_000 for company in card_companies]

    # 최대값에 여유분을 두어 설정
    max_value = max(values) * 1.1  # 최대값의 110%를 최대 범위로 설정

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=card_companies,
        fill='toself',
        name='카드사별 사용금액',
        line_color='rgb(70, 130, 180)',
        fillcolor='rgba(70, 130, 180, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max_value],  # 여기를 조정
                ticksuffix='M',
                tickformat=',d'
            )
        ),
        showlegend=False,
        title={
            'text': '최신 카드사별 총사용금액 비교 (단위: 백만원)',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        width=650,
        height=400
    )
    return to_html(fig, full_html=False)


def card_sales_view(request):

    card_total_sales_ladar_html = card_total_sales_ladar_view(request)

    # 템플릿에 전달
    return render(request, "dashboard_hoseop.html", {
        "card_total_sales_ladar_html": card_total_sales_ladar_html
        })

