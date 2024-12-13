import requests
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from prophet import Prophet
from dotenv import load_dotenv
from functools import reduce
import os
import pymysql
from sqlalchemy import create_engine

load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")

end_date = datetime.today().strftime('%Y%m')

def fetch_card_data():
    # API 기본 URL과 분류 코드 설정
    base_url = "https://ecos.bok.or.kr/api/StatisticSearch/" + os.getenv("CARD_API") + f"/json/kr/1/100000/601Y002/M/200001/{end_date}/X/" + "{}/DAV"
    codes = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500]

    # 각 분류 코드에 대한 데이터를 저장할 리스트
    df_list = []

    # 각 분류 코드에 맞는 데이터프레임 생성
    for code in codes:
        url = base_url.format(code)
        response = requests.get(url)
        data = response.json()

        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            # 데이터프레임 생성
            df = pd.DataFrame(data['StatisticSearch']['row'])

            # 'ITEM_NAME2'를 새로운 열 이름으로 설정
            item_name = df['ITEM_NAME2'].iloc[0]

            # 필요한 열만 남기고 'DATA_VALUE' 열 이름을 ITEM_NAME2 값으로 변경
            df = df[['TIME', 'DATA_VALUE']]
            df.rename(columns={'DATA_VALUE': item_name}, inplace=True)

            # 데이터프레임 리스트에 추가
            df_list.append(df)
        else:
            print(f"데이터가 없습니다: 코드 {code}")

    # 모든 데이터프레임을 TIME을 기준으로 병합
    if df_list:
        pce_df = reduce(lambda left, right: pd.merge(left, right, on='TIME', how='outer'), df_list)
    else:
        print("병합할 데이터프레임이 없습니다.")

    pce_df.TIME = pd.to_datetime(pce_df.TIME, format='%Y%m')

    # 문자열 형태의 숫자를 수치형으로 변환 후, int로 타입 변환
    for i in pce_df.columns[1:]:
        pce_df[i] = pce_df[i].apply(pd.to_numeric)

    return pce_df


def fetch_cpi_data():
    """KOSIS API에서 데이터를 수집하고 처리합니다."""
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
    "method": "getList",
    "apiKey": os.getenv("KOSIS_API"),
    "itmId": "T+",
    "objL1": "T10",
    "objL2": "0+A+C+D+E+F+G+H+I+J+K+L+",
    "format": "json",
    "jsonVD": "Y",
    "prdSe": "M",
    "startPrdDe": "200912",
    "endPrdDe": end_date,
    "outputFields": "ORG_ID TBL_ID TBL_NM OBJ_ID OBJ_NM NM ITM_ID ITM_NM UNIT_NM PRD_SE PRD_DE LST_CHN_DE",
    "orgId": "101",
    "tblId": "DT_1J22001"
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data)

    # 타입 변환
    df.PRD_DE = pd.to_datetime(df.PRD_DE, format='%Y%m')
    df["DT"] = df["DT"].apply(pd.to_numeric)

    # 피벗 테이블로 변환
    cpi_df = df.pivot_table(index='PRD_DE', columns='C2_NM', values='DT').reset_index()

    # merge를 위한 칼럼 이름 변경
    cpi_df.rename(columns={'PRD_DE': 'TIME'}, inplace=True)

    return cpi_df

def grouping_data(pce_df, cpi_df):
    # 소비 유형별 품목 분류
    category_mapping = {
        '합계': '0 총지수',
        '식료품': '01 식료품 및 비주류음료',
        '의류/잡화': '03 의류 및 신발',
        '연료': '04 주택 수도 전기 및 연료',
        '가구/가전': '05 가정용품 및 가사 서비스',
        '의료/보건': '06 보건',
        '여행/교통': '07 교통',
        '오락/문화': '09 오락 및 문화',
        '교육': '10 교육',
        '숙박/음식': '11 음식 및 숙박',
        '공과금/개인 및 전문 서비스': '12 기타 상품 및 서비스',
    }

    # 10개 카테고리별 데이터프레임 생성

    # 1. category_mapping을 기반으로 각 카테고리별 데이터프레임 생성
    category_dfs = {}

    for pce_category, cpi_category in category_mapping.items():
        # PCE 데이터 추출
        pce_data = pce_df[['TIME', pce_category]]
        
        # CPI 데이터 추출
        cpi_data = cpi_df[['TIME', cpi_category]]
        
        # 두 데이터프레임 병합
        merged_df = pd.merge(pce_data, cpi_data, on='TIME', how='inner')
        
        # 컬럼명 변경
        merged_df.columns = ['TIME', f'{pce_category}_PCE', f'{pce_category}_CPI']
        
        # 결과 저장
        category_dfs[pce_category] = merged_df

    return category_dfs

def forecast_future(df, column_name, periods=3):
    """Prophet 모델을 사용해 미래 예측을 수행합니다."""
    df_prophet = df[['TIME', column_name]].rename(columns={'TIME': 'ds', column_name: 'y'})
    model = Prophet()
    model.fit(df_prophet)
    future = model.make_future_dataframe(periods=periods, freq='M')
    forecast = model.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def forecast_all_categories(category_dfs, periods=3):
    """모든 카테고리에 대해 PCE와 CPI 예측을 수행합니다."""
    
    # 최종 결과를 저장할 데이터프레임
    all_forecasts = None
    
    for category, df in category_dfs.items():
        # PCE 예측
        pce_column = f'{category}_PCE'
        pce_forecast = forecast_future(df, pce_column, periods)
        pce_forecast.columns = ['ds', f'{category}_PCE_pred', f'{category}_PCE_lower', f'{category}_PCE_upper']
        
        # CPI 예측
        cpi_column = f'{category}_CPI'
        cpi_forecast = forecast_future(df, cpi_column, periods)
        cpi_forecast.columns = ['ds', f'{category}_CPI_pred', f'{category}_CPI_lower', f'{category}_CPI_upper']
        
        # PCE와 CPI 예측 결과 병합
        category_forecast = pd.merge(pce_forecast, cpi_forecast, on='ds', how='outer')
        
        # 전체 결과에 병합
        if all_forecasts is None:
            all_forecasts = category_forecast
        else:
            all_forecasts = pd.merge(all_forecasts, category_forecast, on='ds', how='outer')
    
    # 날짜 컬럼명 변경
    all_forecasts.rename(columns={'ds': 'TIME'}, inplace=True)
    
    return all_forecasts

def run_data_pipeline():
    """데이터를 수집, 예측, 그리고 MySQL에 업로드합니다."""
    
    # 데이터 수집
    pce_df = fetch_card_data()
    cpi_df = fetch_cpi_data()
    
    # 카테고리별 데이터 그룹핑
    category_dfs = grouping_data(pce_df, cpi_df)
    
    # 모든 카테고리에 대한 예측 수행
    all_forecasts = forecast_all_categories(category_dfs)
    
    # MySQL에 업로드
    all_forecasts.to_sql('cpi_card_data', con=engine, if_exists='append', index=False)

def cpi_data_upload():
    """매달 cpi 지표를 최신화하여 MySQL에 업로드 합니다."""
    
    cpi_df = fetch_cpi_data()[['TIME', '0 총지수']].rename(columns={'0 총지수' : 'TOTAL'})

    cpi_df.to_sql('cpi_data', con=engine, if_exists='append', index=False)

def pce_data_upload():
    """분기별 pce 지표를 최신화하여 MySQL에 업로드 합니다."""

    # 현재 날짜를 기준으로 end_date 계산
    current_date = datetime.today()
    year = current_date.year
    month = current_date.month

    # 분기 계산 (1분기: 1~3월, 2분기: 4~6월, ...)
    quarter = (month - 1) // 3 + 1
    end_date = f"{year}Q{quarter}"

    url = f"https://ecos.bok.or.kr/api/StatisticSearch/2IJKJSOY6OFOQZ28900C/json/kr/1/100000/200Y102/Q/2023Q1/{end_date}/10222"

    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data['StatisticSearch']['row'])[['TIME', 'STAT_NAME', 'ITEM_NAME1', 'DATA_VALUE']]

    df.to_sql('pce_data', con=engine, if_exists='append', index=False)

# 기본 DAG 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    '03_CPI_CARD_data',
    default_args=default_args,
    description="소비자물가, 개인신용카드 소비현황 예측 데이터를 업로드합니다.",
    schedule_interval='@monthly',
    start_date=datetime.now(),
    catchup=False,
    tags=['MySQL', 'api', 'forecast'],
    dagrun_timeout=timedelta(minutes=20)
) as dag:

    # 데이터 파이프라인 실행 태스크
    run_pipeline_task = PythonOperator(
        task_id='run_data_pipeline',
        python_callable=run_data_pipeline,
        execution_timeout=timedelta(hours=1)
    )

    cpi_upload_task = PythonOperator(
        task_id='cpi_data_upload',
        python_callable=cpi_data_upload,
        execution_timeout=timedelta(hours=1)
    )

    pce_upload_task = PythonOperator(
        task_id='pce_data_upload',
        python_callable=pce_data_upload,
        execution_timeout=timedelta(hours=1)
    )

    # 태스크 간의 의존성 설정
    run_pipeline_task >> cpi_upload_task >> pce_upload_task