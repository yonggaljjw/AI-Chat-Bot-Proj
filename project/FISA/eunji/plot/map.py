import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from deep_translator import GoogleTranslator


def create_and_show_travel_warning_map():
    travel_data = df
    geojson_url="https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    travel_data.columns = ["나라", "여행유의", "여행자제", "출국권고", "여행금지", "특별여행주의보"]
    # GeoJSON 데이터를 가져와 번역
    world = gpd.read_file(geojson_url)
    translator = GoogleTranslator(source='en', target='ko')
    world['나라'] = world['name'].apply(lambda x: translator.translate(x))

    # GeoJSON 데이터와 여행 데이터 병합
    world = world.merge(travel_data, on='나라', how='left')
    world = world.fillna(False)
    # 여행 경보 단계에 따라 색상 지정
    def get_travel_warning(row):
        if row['여행금지']:
            return '4단계 (여행금지)'
        elif row['출국권고']:
            return '3단계 (출국권고)'
        elif row['여행자제']:
            return '2단계 (여행자제)'
        elif row['여행유의']:
            return '1단계 (여행유의)'
        elif row['특별여행주의보']:
            return '특별여행주의보'
        else:
            return '정보 없음'

    world['여행경보'] = world.apply(get_travel_warning, axis=1)

    # 색상 매핑 정의
    color_scale = {
        '1단계 (여행유의)': '#4dabf7',
        '2단계 (여행자제)': '#ffd43b',
        '3단계 (출국권고)': '#ff6b6b',
        '4단계 (여행금지)': '#343a40',
        '특별여행주의보': '#e64980',
        '정보 없음': '#f8f9fa'
    }
    # 지도 시각화 생성
    fig = go.Figure()

    for warning_level in color_scale.keys():
        subset = world[world['여행경보'] == warning_level]
        if not subset.empty:
            fig.add_trace(
                go.Choropleth(
                    locations=subset['나라'],
                    geojson=world.__geo_interface__,
                    z=[1] * len(subset),
                    colorscale=[[0, color_scale[warning_level]], [1, color_scale[warning_level]]],
                    showscale=False,
                    featureidkey="properties.나라",
                    name=warning_level,
                    legendgroup=warning_level,  # 범례 그룹화
                    hovertemplate="<b>국가:</b> %{location}<br>" +
                                  "<b>여행경보:</b> " + warning_level +
                                  "<extra></extra>",
                    marker=dict(
                        line=dict(
                            color='white',
                            width=0.5
                        )
                    )
                )
            )

    # 색상 범례를 위한 추가 트레이스
    for warning_level in color_scale.keys():
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(size=15, color=color_scale[warning_level]),
                showlegend=True,
                name=warning_level,
                legendgroup=warning_level,  # 범례 그룹화
                legendgrouptitle=dict(
                    text="단계별 색상",
                    font=dict(size=16, family="Malgun Gothic")
                )
            )
        )

    # 레이아웃 설정
    fig.update_layout(
        title=dict(
            text="대한민국 외교부 여행경보 단계별 세계 지도",
            x=0.5,
            y=0.99,
            xanchor='center',
            yanchor='top',
            font=dict(
                size=18,
                family="Malgun Gothic",
                color="#333333"
            )
        ),
        dragmode='zoom',  # 확대/축소를 위한 드래그 모드
        showlegend=True,
        legend=dict(
            orientation="h",  # 범례를 가로로 배치
            x=0.5,            # 범례를 중심으로 배치
            y=-0.2,           # 범례를 지도 아래로 이동
            xanchor="center", 
            yanchor="top",
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="lightgray",
            borderwidth=1,
            itemsizing='constant',
            traceorder="normal",  # 범례 순서를 정상적으로 표시
        ),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="equirectangular",
            coastlinecolor="darkgray",
            coastlinewidth=0.8,
            showland=True,
            landcolor="white",
            showocean=True,
            oceancolor="#74c0fc",
            showlakes=True,
            lakecolor="#4dabf7",
            showcountries=True,
            countrycolor="lightgray",
            countrywidth=0.5,
            resolution=50,
            lonaxis=dict(range=[-180, 180]),
            lataxis=dict(range=[-60, 90])
        ),
        width=1000,  # 지도 크기 적정화
        height=600,  # 높이 조정
        margin=dict(t=20, r=20, b=100, l=20),  # 하단 여백 확보
        paper_bgcolor='white',
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font=dict(
                family="Malgun Gothic",
                size=12
            ),
            bordercolor="lightgray"
        )
    )
    # 그래프 출력
    fig.show(config={
        'scrollZoom': True, 
        'displayModeBar': True, 
        'modeBarButtonsToAdd': ['pan2d', 'zoomIn2d', 'zoomOut2d'], 
        'displaylogo': False
    })
