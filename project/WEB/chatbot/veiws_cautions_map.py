import pandas as pd
import plotly.express as px
from plotly.io import to_html
from sqlalchemy import create_engine
import pycountry
from deep_translator import GoogleTranslator
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

def get_risk_level(advice):
    if '여행유의' in advice:
        return 1
    elif '여행자제' in advice:
        return 2
    elif '출국권고' in advice:
        return 3
    elif '여행금지' in advice:
        return 4
    else:
        return 0

def merge_data():
    print("merge_data start")
    web_data = fetch_data()
    print(web_data, "web_data")
    sql_data = load_data_from_sql()
    print(sql_data, "sql_data")
    if 'Country' not in sql_data.columns and 'Country_EN' in sql_data.columns:
        sql_data['Country'] = sql_data['Country_EN']
    
    merged_df = pd.merge(web_data, sql_data, on='Country', how='outer')
    # print(merged_df, "merged_df")
    # translator = GoogleTranslator(source='ko', target='en')
    # merged_df['Country_EN'] = merged_df['Country_EN'].fillna(merged_df['Country'].apply(translator.translate))
    
    def get_iso_code(country_name):
        try:
            country = pycountry.countries.search_fuzzy(country_name)
            return country[0].alpha_3 if country else None
        except LookupError:
            return None

    merged_df['ISO_Alpha_3'] = merged_df['Country_EN'].apply(get_iso_code)
    
    merged_df['Risk_level'] = merged_df['Travel_Advice'].apply(get_risk_level)
    print(merged_df, "merged_df")
    return merged_df

def translate_country_name(name):
    try:
        return GoogleTranslator(source='ko', target='en').translate(name)
    except:
        return name

def calculate_risk_level(row):
    """
    여행 주의 단계를 계산하는 통합 함수
    """
    if isinstance(row, str):  # Travel_Advice 문자열 처리
        if '여행금지' in row:
            return 4
        elif '출국권고' in row:
            return 3
        elif '여행자제' in row:
            return 2
        elif '여행유의' in row:
            return 1
        return 0
    
    # 기존 컬럼 기반 계산
    if row.get('Special_Travel_Advisory') == 1:
        return 5
    if row.get('Travel_Ban') == 1:
        return 4
    if row.get('Departure_Advisory') == 1:
        return 3
    if row.get('Travel_Restriction') == 1:
        return 2
    if row.get('Travel_Caution') == 1:
        return 1
    return 0

def get_iso_code(country_name):
    """
    국가명으로 ISO 코드를 조회하는 함수
    """
    if not country_name or not isinstance(country_name, str):
        return None
        
    try:
        # 직접 검색 시도
        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_3
            
        # fuzzy 검색 시도
        countries = pycountry.countries.search_fuzzy(country_name)
        return countries[0].alpha_3 if countries else None
    except (LookupError, IndexError) as e:
        print(f"ISO 코드 조회 실패 ({country_name}): {str(e)}")
        return None

def merge_and_process_data():
    """
    데이터 병합 및 처리 함수
    """
    df = merge_data()
    if df.empty:
        print("경고: 데이터가 비어 있습니다.")
        return pd.DataFrame()

    # 데이터 검증
    required_columns = ['Country', 'Travel_Advice']
    if not all(col in df.columns for col in required_columns):
        print("경고: 필수 컬럼이 누락되었습니다.")
        return pd.DataFrame()

    try:
        # 영문 국가명 변환
        df['Country_EN'] = df['Country'].apply(translate_country_name)
        df['ISO_Alpha_3'] = df['Country_EN'].apply(get_iso_code)
        df['Risk_Level'] = df.apply(lambda x: calculate_risk_level(x['Travel_Advice']), axis=1)
        
        # 결과 데이터 검증
        df = df.dropna(subset=['ISO_Alpha_3'])  # ISO 코드가 없는 행 제거
        
        return df
    except Exception as e:
        print(f"데이터 처리 중 오류 발생: {str(e)}")
        return pd.DataFrame()

def visualize_travel_advice():
    df = merge_and_process_data()
    if df.empty:
        print("경고: 시각화할 데이터가 없습니다.")
        return None

    fig = px.choropleth(df, 
                        locations='ISO_Alpha_3',
                        color='Risk_Level',
                        hover_name='Country',
                        color_continuous_scale="Emrld")

    fig.update_geos(projection_type="natural earth")
    fig.update_layout(width=400, height=300, margin={"r":0, "t":0, "l":0, "b":0})
    fig.update_geos(showcountries=True, countrycolor="Gray")
    fig.update_layout(coloraxis_showscale=False, autosize=True)

    # 결과 출력
    return to_html(fig, full_html=False)