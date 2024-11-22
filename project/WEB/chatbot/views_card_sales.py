from django.shortcuts import render
import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.io import to_json
import plotly.express as px
import pandas as pd
import numpy as np
from django.conf import settings
from sqlalchemy import create_engine
import pymysql
import datetime


def load_card_sales_data_from_sql():
    """SQL에서 card_sales 데이터를 불러오는 함수"""
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


def card_total_sales_ladar_view():
    """카드사별 사용금액 비교 레이더 차트 뷰"""
    card_sales = load_card_sales_data_from_sql()

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
        # title={
        #     'y': 0.5,
        #     'x': 0.1,
        #     'xanchor': 'center',
        #     'yanchor': 'top'
        # },
        autosize=True
    )
    return to_json(fig)

def create_card_heatmap_view():
    """카드사별 세부 비교 히트맵 생성 (데이터 전치)"""
    # 데이터 로드
    card_sales = load_card_sales_data_from_sql()

    if card_sales.empty:
        return None

    # 최신 연월 데이터 추출
    year_month = card_sales['년월'].max()

    # 특정 연월 데이터 필터링
    df_filtered = card_sales[card_sales['년월'] == year_month]

    # 카드사 목록
    card_companies = [
        '롯데카드', '비씨카드(자체)', '삼성카드', '신한카드',
        '우리카드', '하나카드', '현대카드', 'KB국민카드'
    ]

    # 세부 구성 정보를 위한 그룹화
    results = []
    for company in card_companies:
        domestic_personal_credit = df_filtered[
            (df_filtered['대분류'] == '국내이용금액 ') & 
            (df_filtered['카드 종류'] == '신용카드') & 
            (df_filtered['사용구분'] == '개인')
        ][company].sum() / 1_000_000

        domestic_corporate_credit = df_filtered[
            (df_filtered['대분류'] == '국내이용금액 ') & 
            (df_filtered['카드 종류'] == '신용카드') & 
            (df_filtered['사용구분'] == '법인')
        ][company].sum() / 1_000_000

        domestic_personal_check = df_filtered[
            (df_filtered['대분류'] == '국내이용금액 ') & 
            (df_filtered['카드 종류'] == '직불/체크카드') & 
            (df_filtered['사용구분'] == '개인')
        ][company].sum() / 1_000_000

        domestic_corporate_check = df_filtered[
            (df_filtered['대분류'] == '국내이용금액 ') & 
            (df_filtered['카드 종류'] == '직불/체크카드') & 
            (df_filtered['사용구분'] == '법인')
        ][company].sum() / 1_000_000

        overseas_personal_credit = df_filtered[
            (df_filtered['대분류'] == '해외이용금액') & 
            (df_filtered['카드 종류'] == '신용카드') & 
            (df_filtered['사용구분'] == '개인')
        ][company].sum() / 1_000_000

        overseas_corporate_credit = df_filtered[
            (df_filtered['대분류'] == '해외이용금액') & 
            (df_filtered['카드 종류'] == '신용카드') & 
            (df_filtered['사용구분'] == '법인')
        ][company].sum() / 1_000_000

        overseas_personal_check = df_filtered[
            (df_filtered['대분류'] == '해외이용금액') & 
            (df_filtered['카드 종류'] == '직불/체크카드') & 
            (df_filtered['사용구분'] == '개인')
        ][company].sum() / 1_000_000

        overseas_corporate_check = df_filtered[
            (df_filtered['대분류'] == '해외이용금액') & 
            (df_filtered['카드 종류'] == '직불/체크카드') & 
            (df_filtered['사용구분'] == '법인')
        ][company].sum() / 1_000_000

        results.append([
            domestic_personal_credit, domestic_corporate_credit,
            domestic_personal_check, domestic_corporate_check,
            overseas_personal_credit, overseas_corporate_credit,
            overseas_personal_check, overseas_corporate_check
        ])

    # 데이터 배열 생성 및 전치
    z = np.array(results)

    # 카테고리 레이블 생성
    categories = [
        '국내 신용(개인)', '국내 신용(법인)',
        '국내 체크(개인)', '국내 체크(법인)',
        '해외 신용(개인)', '해외 신용(법인)',
        '해외 체크(개인)', '해외 체크(법인)'
    ]

    # 히트맵 생성
    fig = ff.create_annotated_heatmap(
        z=z.T,  # 데이터를 전치하여 회전
        x=card_companies,  # 카드사를 X축에 배치
        y=categories,      # 카테고리를 Y축에 배치
        colorscale='Blues',
        annotation_text=np.around(z.T, 1).astype(str),  # 전치된 데이터를 표시
        showscale=True
    )

    # 레이아웃 수정
    fig.update_layout(
        title={
            'text': f'{year_month} 카드사별 세부 구성 비교 (단위: 백만원)',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        autosize=True
    )

    return to_json(fig)

def wooricard_sales_treemap_view():
    """우리카드 실제 현황"""
    # 데이터 로드
    card_sales = load_card_sales_data_from_sql()

    if card_sales.empty:
        return None

    # 최신 연월 데이터 추출
    year_month = card_sales['년월'].max()

    # 특정 연월 데이터 필터링
    df_filtered = card_sales[card_sales['년월'] == year_month]
    # 우리카드 데이터만 선택하여 새로운 열 생성
    df_filtered['사용금액'] = df_filtered['우리카드']

    # 데이터 집계
    df_sum = df_filtered.groupby(['대분류', '카드 종류', '사용구분', '결제 방법'])['사용금액'].sum().reset_index()

    # 금액이 0인 행 제거
    df_sum = df_sum[df_sum['사용금액'] > 0]

    # 금액 포맷팅 (단위: 백만원)
    df_sum['사용금액_백만원'] = df_sum['사용금액'] / 1_000_000
    df_sum['표시금액'] = df_sum['사용금액_백만원'].round(1).astype(str) + 'M'

    # Treemap 생성
    fig = px.treemap(df_sum,
                     path=['대분류', '카드 종류', '사용구분', '결제 방법'],
                     values='사용금액',
                     title=f'{year_month} 우리카드 월별 매출 현황',
                     color='사용금액',
                     color_continuous_scale='Blues',
                     custom_data=['표시금액'])

    # 레이아웃 수정
    fig.update_traces(
        textinfo="label+text",
        hovertemplate="<b>%{label}</b><br>금액: %{customdata[0]}<extra></extra>"
    )

    fig.update_layout(
        autosize=True
    )

    return to_json(fig)