import pandas as pd
import plotly.express as px
from plotly.io import to_json
from chatbot.sql import engine


def load_travel_trend_from_sql():
    try:
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM travel_trend"
        travel_trend = pd.read_sql(query, engine)
        
        return travel_trend
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()
    
def load_travel_trend_cv_from_sql():
    try:
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM travel_trend_cv"
        travel_trend_cv = pd.read_sql(query, engine)
        
        return travel_trend_cv
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()
    
def travel_trend_line():
    travel_trend = load_travel_trend_from_sql()
    travel_trend_cv = load_travel_trend_cv_from_sql()
    # 나라별 ratio 평균 계산
    mean_ratio = travel_trend.groupby('country')['ratio'].mean().reset_index()

    # ratio의 평균이 큰 상위 30개 나라 추출
    top_30_mean_ratio_countries = mean_ratio.nlargest(30, 'ratio')

    # 상위 30개 나라 중 trend_cv가 큰 상위 10개 선택
    top_30_with_cv = travel_trend_cv[travel_trend_cv['country'].isin(top_30_mean_ratio_countries['country'])]
    top_10_trend_cv_from_top_30 = top_30_with_cv.nlargest(10, 'trend_cv')

    # travel_trend 데이터에서 top 10 나라에 해당하는 데이터 필터링
    filtered_travel_trend_top_10 = travel_trend[travel_trend['country'].isin(top_10_trend_cv_from_top_30['country'])]
    
    # Plotly로 라인 그래프 그리기
    fig = px.line(
        filtered_travel_trend_top_10,
        x="date",
        y="ratio",
        color="country",
        template="plotly_white",
        markers=True,
        # title="변동성이 큰 여행 관심 TOP 10 국가 (30개국 중)",
        labels={"date": "Date", "ratio": "Ratio", "country": "Country"}
    )

    return to_json(fig) 
