import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from plotly.io import to_html
from deep_translator import GoogleTranslator
import plotly.express as px
from django.conf import settings
from sqlalchemy import create_engine

from dash import Dash, dcc, html, Input, Output

def load_data_from_sql():
    try:
        # MySQL 연결 문자열 생성
        db_settings = settings.DATABASES['default']
        connection_string = f"mysql+pymysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        
        # SQLAlchemy 엔진 생성
        engine = create_engine(connection_string)
        
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM tour_intrst"
        tour_intrst = pd.read_sql(query, engine)
        
        return tour_intrst
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()
    
def df_rename():
    df = load_data_from_sql()
    column_mapping = {
    "CHINA_TOUR_INTRST_VALUE": "중국여행관심값",
    "JP_TOUR_INTRST_VALUE": "일본여행관심값",
    "HONGKONG_MACAU_TOUR_INTRST_VALUE": "홍콩마카오여행관심값",
    "SEASIA_TOUR_INTRST_VALUE": "동남아시아여행관심값",
    "MDLEST_SWASIA_TOUR_INTRST_VALUE": "중동서남아시아여행관심값",
    "USA_CANADA_TOUR_INTRST_VALUE": "미국캐나다여행관심값",
    "SAMRC_LAMRC_TOUR_INTRST_VALUE": "남미중남미여행관심값",
    "WEURP_NEURP_TOUR_INTRST_VALUE": "서유럽북유럽여행관심값",
    "EEURP_TOUR_INTRST_VALUE": "동유럽여행관심값",
    "SEURP_TOUR_INTRST_VALUE": "남유럽여행관심값",
    "SPCPC_TOUR_INTRST_VALUE": "남태평양여행관심값",
    "AFRICA_TOUR_INTRST_VALUE": "아프리카여행관심값",
    }

    # 컬럼명 변경
    df.rename(columns=column_mapping, inplace=True)
    return df

def tour_intrst():
    df = df_rename()

    # 긴 형식으로 변환
    melted = df.melt(
        id_vars=["RESPOND_ID", "SEXDSTN_FLAG_CD", "AGRDE_FLAG_NM", "ANSWRR_OC_AREA_NM"],
        value_vars=[
            '중국여행관심값', '일본여행관심값', '홍콩마카오여행관심값', '동남아시아여행관심값', '중동서남아시아여행관심값',
            '미국캐나다여행관심값', '남미중남미여행관심값', '서유럽북유럽여행관심값', '동유럽여행관심값', '남유럽여행관심값',
            '남태평양여행관심값', '아프리카여행관심값'],
        var_name="Region",
        value_name="Interest Change",
    )

    # 관심 변화 수준 순서 강제 적용
    desired_order = ["많이 적어졌다", "약간 적어졌다", "예전과 비슷하다", "약간 커졌다", "많이 커졌다"]
    melted["Interest Change"] = pd.Categorical(melted["Interest Change"], categories=desired_order, ordered=True)
    melted = melted.sort_values("Interest Change")

    # 기본 그래프 생성
    fig = px.bar(
        melted,
        x="Region",
        color="Interest Change",
        title="여행 관심 변화",
        labels={"Region": "지역", "value": "빈도", "Interest Change": "관심 변화 수준"},
        barmode="stack",  # 누적 막대그래프
    )

    # 필터링 옵션 정의
    sexes = [None] + melted["SEXDSTN_FLAG_CD"].unique().tolist()
    ages = [None] + melted["AGRDE_FLAG_NM"].unique().tolist()
    areas = [None] + melted["ANSWRR_OC_AREA_NM"].unique().tolist()

    # 초기값 설정
    selected_sex = None
    selected_age = None
    selected_area = None

    # 데이터 필터링 함수
    def get_filtered_data(sex, age, area):
        return melted[
            ((melted["SEXDSTN_FLAG_CD"] == sex) | (sex is None)) &
            ((melted["AGRDE_FLAG_NM"] == age) | (age is None)) &
            ((melted["ANSWRR_OC_AREA_NM"] == area) | (area is None))
        ]

    # 버튼 생성 함수
    def create_buttons(options, key):
        buttons = []
        for option in options:
            label = option if option is not None else f"전체 {key}"
            buttons.append(dict(
                args=[{
                    "x": [get_filtered_data(
                        selected_sex if key != "성별" else option,
                        selected_age if key != "연령대" else option,
                        selected_area if key != "지역" else option
                    )["Region"]],
                    "y": [get_filtered_data(
                        selected_sex if key != "성별" else option,
                        selected_age if key != "연령대" else option,
                        selected_area if key != "지역" else option
                    )["Interest Change"]],
                }],
                label=label,
                method="update"
            ))
        return buttons

    # 각 메뉴 추가
    fig.update_layout(
        updatemenus=[
            {
                "buttons": create_buttons(sexes, "성별"),
                "direction": "down",
                "showactive": True,
                "x": 0.17,
                "y": 1.15,
                "xanchor": "left",
                "yanchor": "top"
            },
            {
                "buttons": create_buttons(ages, "연령대"),
                "direction": "down",
                "showactive": True,
                "x": 0.37,
                "y": 1.15,
                "xanchor": "left",
                "yanchor": "top"
            },
            {
                "buttons": create_buttons(areas, "지역"),
                "direction": "down",
                "showactive": True,
                "x": 0.57,
                "y": 1.15,
                "xanchor": "left",
                "yanchor": "top"
            }
        ]
    )

    # 그래프 스타일 업데이트
    fig.update_traces(opacity=1)  # 막대 투명도를 완전 불투명으로 설정
    fig.update_layout(width=1200, height=500)  # 그래프 크기 설정

    # HTML 생성 및 반환
    return to_html(fig, full_html=False)

def generate_stacked_bar(selected_sex=None, selected_age=None, selected_area=None):
    df = df_rename()

    # 데이터 필터링 조건 생성
    filtered_data = df[
        ((df["SEXDSTN_FLAG_CD"] == selected_sex) | (selected_sex is None)) &
        ((df["AGRDE_FLAG_NM"] == selected_age) | (selected_age is None)) &
        ((df["ANSWRR_OC_AREA_NM"] == selected_area) | (selected_area is None))
    ]

    # 긴 형식으로 변환
    melted = filtered_data.melt(
        id_vars=["RESPOND_ID", "SEXDSTN_FLAG_CD", "AGRDE_FLAG_NM", "ANSWRR_OC_AREA_NM"],
        value_vars=['중국여행관심값', '일본여행관심값', '홍콩마카오여행관심값', '동남아시아여행관심값', '중동서남아시아여행관심값',
       '미국캐나다여행관심값', '남미중남미여행관심값', '서유럽북유럽여행관심값', '동유럽여행관심값', '남유럽여행관심값',
       '남태평양여행관심값', '아프리카여행관심값'],
        var_name="Region",
        value_name="Interest Change",
    )

    # 관심 변화 수준 순서 강제 적용
    desired_order = ["많이 적어졌다", "약간 적어졌다", "예전과 비슷하다", "약간 커졌다", "많이 커졌다"]
    melted["Interest Change"] = pd.Categorical(melted["Interest Change"], categories=desired_order, ordered=True)

    # 데이터를 순서대로 정렬
    melted = melted.sort_values("Interest Change")

    # 누적 막대그래프 생성
    bar_fig = px.bar(
        melted,
        x="Region",
        color="Interest Change",
        title=f"{selected_area or '전체 지역'}, {selected_age or '전체 연령대'}, {selected_sex or '전체 성별'}의 여행 관심 변화",
        labels={"Region": "지역", "value": "빈도", "Interest Change": "관심 변화 수준"},
        barmode="stack",  # 누적 막대그래프
    )
    return to_html(bar_fig, full_html=False)


# 데이터 로드 및 전처리 함수
def df_rename():
    df = pd.read_csv("CI_OVSEA_TOUR_AREA_INTRST_DGREE_INFO_20240930.csv")
    column_mapping = {
        "CHINA_TOUR_INTRST_VALUE": "중국여행관심값",
        "JP_TOUR_INTRST_VALUE": "일본여행관심값",
        "HONGKONG_MACAU_TOUR_INTRST_VALUE": "홍콩마카오여행관심값",
        "SEASIA_TOUR_INTRST_VALUE": "동남아시아여행관심값",
        "MDLEST_SWASIA_TOUR_INTRST_VALUE": "중동서남아시아여행관심값",
        "USA_CANADA_TOUR_INTRST_VALUE": "미국캐나다여행관심값",
        "SAMRC_LAMRC_TOUR_INTRST_VALUE": "남미중남미여행관심값",
        "WEURP_NEURP_TOUR_INTRST_VALUE": "서유럽북유럽여행관심값",
        "EEURP_TOUR_INTRST_VALUE": "동유럽여행관심값",
        "SEURP_TOUR_INTRST_VALUE": "남유럽여행관심값",
        "SPCPC_TOUR_INTRST_VALUE": "남태평양여행관심값",
        "AFRICA_TOUR_INTRST_VALUE": "아프리카여행관심값",
    }
    df.rename(columns=column_mapping, inplace=True)
    melted = df.melt(
        id_vars=["RESPOND_ID", "SEXDSTN_FLAG_CD", "AGRDE_FLAG_NM", "ANSWRR_OC_AREA_NM"],
        value_vars=list(column_mapping.values()),
        var_name="Region",
        value_name="Interest Change",
    )
    return melted

