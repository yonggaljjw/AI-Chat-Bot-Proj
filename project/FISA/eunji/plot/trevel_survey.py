import pandas as pd
import plotly.express as px


# 필터링 가능한 값들 추출
sex_options = df["SEXDSTN_FLAG_CD"].unique()
age_options = df["AGRDE_FLAG_NM"].unique()
area_options = df["ANSWRR_OC_AREA_NM"].unique()

# 컬럼명 매핑 딕셔너리
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

# 필터링 및 그래프 생성 함수
def generate_stacked_bar(selected_sex=None, selected_age=None, selected_area=None):
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
    return bar_fig

# 함수 호출 예시
fig = generate_stacked_bar(selected_sex=None, selected_age=None, selected_area=None)

# 그래프 출력
fig.show()
