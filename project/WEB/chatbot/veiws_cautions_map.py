import pandas as pd
import plotly.express as px
from plotly.io import to_html,write_html
from sqlalchemy import create_engine
import pycountry
from django.conf import settings
import requests
from bs4 import BeautifulSoup

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

# 웹 스크래핑 함수
def fetch_data():
    url = "https://www.0404.go.kr/dev/country.mofa?idx=&hash=&chkvalue=no1&stext=&group_idx="
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    data = []
    countries = soup.select("ul.country_list > li")

    for country in countries:
        country_name = country.select_one("a").text.strip()
        img_tags = country.select("img")
        travel_advice = [img["alt"].strip() for img in img_tags if img.get("alt")]
        travel_advice = ", ".join(travel_advice) if travel_advice else "정보 없음"
        data.append([country_name, travel_advice])

    return pd.DataFrame(data, columns=["Country", "Travel_Advice"])

# 위험 수준 계산 함수
def get_risk_level(advice):
    if '여행금지' in advice:
        return 4
    elif '출국권고' in advice:
        return 3
    elif '여행자제' in advice:
        return 2
    elif '여행유의' in advice:
        return 1
    else:
        return 0

# 데이터 병합 및 처리 함수
def merge_and_process_data():
    web_data = fetch_data()
    sql_data = load_data_from_sql()
    
    if 'Country' not in sql_data.columns and 'Country_EN' in sql_data.columns:
        sql_data['Country'] = sql_data['Country_EN']
    
    merged_df = pd.merge(web_data, sql_data, on='Country', how='outer')
    
    # translator = GoogleTranslator(source='ko', target='en')
    # merged_df['Country_EN'] = merged_df['Country'].apply(lambda x: translator.translate(x) if pd.notnull(x) else None)
    
    def get_iso_code(country_name):
        try:
            if pd.isnull(country_name):
                return None
            country = pycountry.countries.search_fuzzy(country_name)
            return country[0].alpha_3 if country else None
        except LookupError:
            return None

    merged_df['ISO_Alpha_3'] = merged_df['Country_EN'].apply(get_iso_code)
    merged_df['Risk_level'] = merged_df['Travel_Advice'].apply(get_risk_level)
    
    return merged_df

# 시각화 함수
def visualize_travel_advice():
    df = merge_and_process_data()
    if df.empty:
        print("경고: 시각화할 데이터가 없습니다.")
        return None

    fig = px.choropleth(df,
                        locations='ISO_Alpha_3',
                        color='Risk_level',
                        hover_name='Country',
                        color_continuous_scale="Emrld")

    fig.update_geos(projection_type="natural earth", showcountries=True, countrycolor="Gray")
    fig.update_layout(coloraxis_showscale=False, autosize=True, width=1000)

    return to_html(fig)