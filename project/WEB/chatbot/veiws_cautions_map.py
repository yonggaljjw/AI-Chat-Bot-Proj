from datetime import datetime
from opensearchpy import OpenSearch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

import pandas as pd
import geopandas as gpd
from plotly.io import to_html
import plotly.graph_objects as go
from deep_translator import GoogleTranslator
import plotly.express as px
from django.conf import settings
from sqlalchemy import create_engine

import pycountry

def load_data_from_sql():
    try:
        # MySQL 연결 문자열 생성
        db_settings = settings.DATABASES['default']
        connection_string = f"mysql+pymysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        
        # SQLAlchemy 엔진 생성
        engine = create_engine(connection_string)
        
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM travel_caution"
        travel_caution = pd.read_sql(query, engine)
        
        return travel_caution
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()



def merge_and_process_data():
    """
    여행 권고 데이터를 병합하고 위험 수준 및 ISO 국가 코드를 추가합니다.
    """
    # 여행 권고 데이터 가져오기
    df = load_data_from_sql()

    # 데이터가 비어있는 경우 처리
    if df.empty:
        print("경고: 데이터가 비어 있습니다. 기본값으로 대체하거나 추가 조치를 취하세요.")
        return pd.DataFrame()  # 빈 데이터프레임 반환
    
    # ISO 국가 코드 추가 함수
    def get_iso_code(country_name):
        try:
            country = pycountry.countries.get(name=country_name)
            return country.alpha_3 if country else None
        except KeyError:
            return None

    # ISO 국가 코드 열 추가
    df['ISO_Alpha_3'] = df['Country'].apply(get_iso_code)

    # 위험 수준 계산 함수
    def calculate_risk(row):
        risk_level = 0
        if row.get('Travel_Caution', False):
            risk_level = 1
        if row.get('Travel_Restriction', False):
            risk_level = 2
        if row.get('Departure_Advisory', False):
            risk_level = 3
        if row.get('Travel_Ban', False):
            risk_level = 4
        if row.get('Special_Travel_Advisory', False):
            risk_level = 5
        return risk_level

    # 위험 수준 컬럼 추가
    df['Risk_Level'] = df.apply(calculate_risk, axis=1)

    return df

def visualize_travel_advice():
    """
    여행 권고 데이터를 시각화합니다.
    """
    # 데이터 병합 및 처리
    df = merge_and_process_data()

    # 데이터가 비어있는 경우 처리
    if df.empty:
        print("경고: 시각화할 데이터가 없습니다.")
        return None

    # Plotly를 이용한 지도 시각화
    fig = px.choropleth(df, 
                        locations='ISO_Alpha_3',  # 국가별 ISO 코드
                        color='Risk_Level',  # 위험 수준에 따라 색상 변경
                        hover_name='Country',  # 마우스를 올리면 국가 이름 표시
                        color_continuous_scale="Emrld",  # 색상 팔레트
                        )

    # 지도 투영 방식 설정: 'natural earth'
    fig.update_geos(projection_type="natural earth")

    # 지도 크기 및 마진 설정
    fig.update_layout(width=400, height=300, margin={"r":0, "t":0, "l":0, "b":0}) 
    # 국가 경계를 표시하도록 설정
    fig.update_geos(showcountries=True, countrycolor="Gray")
    
    # 색상 바를 숨기기 위한 설정
    fig.update_layout(coloraxis_showscale=False)

    # 결과 출력
    return to_html(fig, full_html=False)



































# # 여행 위험 지역 지도 그래프
# def create_and_show_travel_warning_map():
#     travel_data = load_data_from_sql()
#     geojson_url="https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
#     travel_data.columns = ["나라", "여행유의", "여행자제", "출국권고", "여행금지", "특별여행주의보"]
#     # GeoJSON 데이터를 가져와 번역
#     world = gpd.read_file(geojson_url)
#     translator = GoogleTranslator(source='en', target='ko')
#     world['나라'] = world['name'].apply(lambda x: translator.translate(x))

#     # GeoJSON 데이터와 여행 데이터 병합
#     world = world.merge(travel_data, on='나라', how='left')
#     world = world.fillna(False)
#     # 여행 경보 단계에 따라 색상 지정
#     def get_travel_warning(row):
#         if row['여행금지']:
#             return '4단계 (여행금지)'
#         elif row['출국권고']:
#             return '3단계 (출국권고)'
#         elif row['여행자제']:
#             return '2단계 (여행자제)'
#         elif row['여행유의']:
#             return '1단계 (여행유의)'
#         elif row['특별여행주의보']:
#             return '특별여행주의보'
#         else:
#             return '정보 없음'

#     world['여행경보'] = world.apply(get_travel_warning, axis=1)

#     # 색상 매핑 정의
#     color_scale = {
#         '1단계 (여행유의)': '#4dabf7',
#         '2단계 (여행자제)': '#ffd43b',
#         '3단계 (출국권고)': '#ff6b6b',
#         '4단계 (여행금지)': '#343a40',
#         '특별여행주의보': '#e64980',
#         '정보 없음': '#f8f9fa'
#     }
#     # 지도 시각화 생성
#     fig = go.Figure()

#     for warning_level in color_scale.keys():
#         subset = world[world['여행경보'] == warning_level]
#         if not subset.empty:
#             fig.add_trace(
#                 go.Choropleth(
#                     locations=subset['나라'],
#                     geojson=world.__geo_interface__,
#                     z=[1] * len(subset),
#                     colorscale=[[0, color_scale[warning_level]], [1, color_scale[warning_level]]],
#                     showscale=False,
#                     featureidkey="properties.나라",
#                     name=warning_level,
#                     legendgroup=warning_level,  # 범례 그룹화
#                     hovertemplate="<b>국가:</b> %{location}<br>" +
#                                   "<b>여행경보:</b> " + warning_level +
#                                   "<extra></extra>",
#                     marker=dict(
#                         line=dict(
#                             color='white',
#                             width=0.5
#                         )
#                     )
#                 )
#             )

#     # 색상 범례를 위한 추가 트레이스
#     for warning_level in color_scale.keys():
#         fig.add_trace(
#             go.Scatter(
#                 x=[None],
#                 y=[None],
#                 mode='markers',
#                 marker=dict(size=15, color=color_scale[warning_level]),
#                 showlegend=True,
#                 name=warning_level,
#                 legendgroup=warning_level,  # 범례 그룹화
#                 legendgrouptitle=dict(
#                     text="단계별 색상",
#                     font=dict(size=16, family="Malgun Gothic")
#                 )
#             )
#         )

#     # 레이아웃 설정
#     fig.update_layout(
#         title=dict(
#             text="대한민국 외교부 여행경보 단계별 세계 지도",
#             x=0.5,
#             y=0.99,
#             xanchor='center',
#             yanchor='top',
#             font=dict(
#                 size=18,
#                 family="Malgun Gothic",
#                 color="#333333"
#             )
#         ),
#         dragmode='zoom',  # 확대/축소를 위한 드래그 모드
#         showlegend=True,
#         legend=dict(
#             orientation="h",  # 범례를 가로로 배치
#             x=0.5,            # 범례를 중심으로 배치
#             y=-0.2,           # 범례를 지도 아래로 이동
#             xanchor="center", 
#             yanchor="top",
#             bgcolor="rgba(255, 255, 255, 0.9)",
#             bordercolor="lightgray",
#             borderwidth=1,
#             itemsizing='constant',
#             traceorder="normal",  # 범례 순서를 정상적으로 표시
#         ),
#         geo=dict(
#             showframe=False,
#             showcoastlines=True,
#             projection_type="equirectangular",
#             coastlinecolor="darkgray",
#             coastlinewidth=0.8,
#             showland=True,
#             landcolor="white",
#             showocean=True,
#             oceancolor="#74c0fc",
#             showlakes=True,
#             lakecolor="#4dabf7",
#             showcountries=True,
#             countrycolor="lightgray",
#             countrywidth=0.5,
#             resolution=50,
#             lonaxis=dict(range=[-180, 180]),
#             lataxis=dict(range=[-60, 90])
#         ),
#         width=1000,  # 지도 크기 적정화
#         height=600,  # 높이 조정
#         margin=dict(t=20, r=20, b=100, l=20),  # 하단 여백 확보
#         paper_bgcolor='white',
#         plot_bgcolor='white',
#         hoverlabel=dict(
#             bgcolor="white",
#             font=dict(
#                 family="Malgun Gothic",
#                 size=12
#             ),
#             bordercolor="lightgray"
#         )
#     )
#     # 그래프 출력
#     fig.show(config={
#         'scrollZoom': True, 
#         'displayModeBar': True, 
#         'modeBarButtonsToAdd': ['pan2d', 'zoomIn2d', 'zoomOut2d'], 
#         'displaylogo': False
#     })
#     return to_html(fig, full_html=False)


# # print(create_and_show_travel_warning_map())