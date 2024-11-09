# import requests
# import pandas as pd
# from functools import reduce
# from airflow import DAG
# from airflow.operators.python_operator import PythonOperator
# from elasticsearch import Elasticsearch
# from datetime import datetime, timedelta
# from prophet import Prophet
# import eland as ed

# # API 기본 URL
# base_url = "https://ecos.bok.or.kr/api/StatisticSearch/2IJKJSOY6OFOQZ28900C/json/kr/1/100000/601Y002/M/200001/202409/X/{}/DAV"

# # 분류 코드 리스트
# codes = [1000, 1100, 1110, 1120, 1130, 1140, 1150, 1200, 1300, 1310, 1320, 1400, 1410, 1420, 1430, 1440, 1500, 1600, 1610, 1620, 1700, 1710, 1720, 1800, 1810, 1820, 1830, 1900, 1910, 1920, 1930, 2000, 2010, 2020, 2100, 2200, 2210, 2220, 2300, 2400, 2500]

# # 각 분류 코드에 대한 데이터를 저장할 리스트
# df_list = []

# # 각 분류 코드에 맞는 데이터프레임 생성
# for code in codes:
#     url = base_url.format(code)
#     response = requests.get(url)
#     data = response.json()

#     if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
#         # 데이터프레임 생성
#         df = pd.DataFrame(data['StatisticSearch']['row'])

#         # 'ITEM_NAME2'를 새로운 열 이름으로 설정
#         item_name = df['ITEM_NAME2'].iloc[0]

#         # 필요한 열만 남기고 'DATA_VALUE' 열 이름을 ITEM_NAME2 값으로 변경
#         df = df[['TIME', 'DATA_VALUE']]
#         df.rename(columns={'DATA_VALUE': item_name}, inplace=True)

#         # 데이터프레임 리스트에 추가
#         df_list.append(df)
#     else:
#         print(f"데이터가 없습니다: 코드 {code}")

# # 모든 데이터프레임을 TIME을 기준으로 병합
# if df_list:
#     merged_df = reduce(lambda left, right: pd.merge(left, right, on='TIME', how='outer'), df_list)
#     print(merged_df.head())  # 병합된 데이터프레임 확인
# else:
#     print("병합할 데이터프레임이 없습니다.")

# merged_df.TIME = pd.to_datetime(merged_df.TIME, format='%Y%m')
# # 문자열 형태의 숫자를 수치형으로 변환 후, int로 타입 변환
# for i in merged_df.columns[1:]:
#     merged_df[i] = merged_df[i].apply(pd.to_numeric)

# pce_df = merged_df.copy()

# # API 호출 URL
# url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
# params = {
#     "method": "getList",
#     "apiKey": "NGFlNDEwNzU4NTVjN2Y2ZTcyYzJiYmI5NjlhY2ExMzc=",  # API 키
#     "orgId": "101",
#     "tblId": "DT_1J22112",
#     "itmId": "T+",
#     "objL1": "T10+",
#     "objL2": "ALL",
#     "format": "json",
#     "jsonVD": "Y",
#     "prdSe": "M",
#     "startPrdDe": "202001",
#     "endPrdDe": "202409",
#     "outputFields": "ORG_ID TBL_ID TBL_NM OBJ_ID OBJ_NM NM ITM_ID ITM_NM UNIT_NM PRD_SE PRD_DE LST_CHN_DE"
# }

# # API 요청 및 JSON 데이터 가져오기
# response = requests.get(url, params=params)
# data = response.json()

# # 데이터프레임 변환
# df = pd.DataFrame(data)

# # 피벗 테이블 생성
# pivot_df = df.pivot_table(index='PRD_DE', columns='C2_NM', values='DT', aggfunc='max')

# # 인덱스를 리셋하여 날짜를 열로 만듦
# cpi_df = pivot_df.reset_index()

# cpi_df.PRD_DE = pd.to_datetime(cpi_df.PRD_DE, format='%Y%m')
# # 문자열 형태의 숫자를 수치형으로 변환 후, int로 타입 변환
# for i in cpi_df.columns[1:]:
#     cpi_df[i] = cpi_df[i].apply(pd.to_numeric)

# cpi_df.rename(columns={'PRD_DE': 'TIME'}, inplace=True)

# # 소비 유형별 품목 분류
# category_mapping = {
#     '합계': ['총지수'],
#     # '종합소매': [],
#     # '전자상거래/통신판매': [],
#     '식료품': ['농축수산물', '가공식품'],
#     '의류/잡화': ['섬유제품', '장신구', '가방', '핸드백', '우산'],
#     '연료': ['석유류', '전기 · 가스 · 수도'],
#     '가구/가전': ['내구재'],
#     '의료/보건': ['의약품', '의료기기'],
#     '자동차': ['소형승용차', '중형승용차', '대형승용차', '경승용차', '다목적승용차', '수입승용차', '전기동력차', '자전거'],
#     '여행/교통': ['여행', '교통'],
#     '오락/문화': ['문화', '예술'],
#     '교육': ['교육', '서적'],
#     '숙박/음식': ['숙박', '음식'],
#     '공과금/개인 및 전문 서비스': ['공공서비스', '의료서비스'],
#     '금융/보험': ['금융서비스', '보험서비스']
# }

# # 15개 카테고리별 데이터프레임 생성
# total_df = pd.merge(pce_df[['TIME', '합계']], cpi_df[['TIME','총지수']])
# eat_df = pd.merge(pce_df[['TIME', '식료품']], pd.concat([cpi_df['TIME'], cpi_df[['농축수산물', '가공식품']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_식료품'}))
# cloth_df = pd.merge(pce_df[['TIME', '의류/잡화']], pd.concat([cpi_df['TIME'], cpi_df[['섬유제품', '장신구', '가방', '핸드백', '우산']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_의류/잡화'}))
# oil_df = pd.merge(pce_df[['TIME', '연료']], pd.concat([cpi_df['TIME'], cpi_df[['석유류', '전기 · 가스 · 수도']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_연료'}))
# furniture_df = pd.merge(pce_df[['TIME', '가구/가전']], pd.concat([cpi_df['TIME'], cpi_df['내구재']], axis=1).rename(columns={0: 'cpi_가구/가전'}))
# health_df = pd.merge(pce_df[['TIME', '의료/보건']], pd.concat([cpi_df['TIME'], cpi_df[['의약품', '의료측정기', '보청기', '치료재료']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_의료/보건'}))
# car_df = pd.merge(pce_df[['TIME', '자동차']], pd.concat([cpi_df['TIME'], cpi_df[['소형승용차', '중형승용차', '대형승용차', '경승용차', '다목적승용차', '수입승용차', '전기동력차', '자전거']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_자동차'}))
# trip_df = pd.merge(pce_df[['TIME', '여행/교통']], pd.concat([cpi_df['TIME'], cpi_df[['국내단체여행비', '해외단체여행비', '국제항공료', '택시료', '시외버스료', '시내버스료', '도시철도료', '열차료', '도로통행료']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_여행/교통'}))
# art_df = pd.merge(pce_df[['TIME', '오락/문화']], pd.concat([cpi_df['TIME'], cpi_df[['수영장이용료', '놀이시설이용료', '운동경기관람료', '공연예술관람료', '관람시설이용료']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_오락/문화'}))
# edu_df = pd.merge(pce_df[['TIME', '교육']], pd.concat([cpi_df['TIME'], cpi_df[['학교보충교육비', '서적']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_교육'}))
# accomodation_df = pd.merge(pce_df[['TIME', '숙박/음식']], pd.concat([cpi_df['TIME'], cpi_df[['호텔숙박료', '여관숙박료', '콘도이용료','외식']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_숙박/음식'}))
# service_df = pd.merge(pce_df[['TIME', '공과금/개인 및 전문 서비스']], pd.concat([cpi_df['TIME'], cpi_df[['공공서비스', '건강검진비', '병원검사료']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_공과금/개인 및 전문 서비스'}))
# bank_df = pd.merge(pce_df[['TIME', '금융/보험']], pd.concat([cpi_df['TIME'], cpi_df[['금융수수료', '보험서비스료', '자동차보험료']].mean(axis=1)], axis=1).rename(columns={0: 'cpi_금융/보험'}))

# # 예측 및 시각화 함수 정의
# def forecast_future(dataframe, column_name, periods=3):
#     # Prophet이 요구하는 ds, y 열 이름으로 변경
#     df_prophet = dataframe[['TIME', column_name]].rename(columns={'TIME': 'ds', column_name: 'y'})
#     model = Prophet()
#     model.fit(df_prophet)

#     # 미래 날짜 생성 및 예측 수행
#     future = model.make_future_dataframe(periods=periods, freq='MS')
#     forecast = model.predict(future)

#     return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]


# pce_eat_df = forecast_future(eat_df, eat_df.columns[1])
# cpi_eat_df = forecast_future(eat_df, eat_df.columns[2])

# es = Elasticsearch('http://host.docker.internal:9200')

# try :
#     es.indice.create('항목별 개인 신용카드 소비현황')
#     es.indice.create('소비자물가지수')
# except :
#     pass

# def dataframe_to_elasticsearch():
#     ed.pandas_to_eland(
#         pd_df=pce_eat_df,
#         es_client=es,
#         es_dest_index="항목별 개인 신용카드 소비현황",
#         es_if_exists="append",
#         es_refresh=True
#         )
    
#     ed.pandas_to_eland(
#         pd_df=cpi_eat_df,
#         es_client=es,
#         es_dest_index="소비자물가지수",
#         es_if_exists="append",
#         es_refresh=True
#         )

    

# default_args = {
#     'depends_on_past': False,
#     'retires': 1,
#     'retry_delay': timedelta(minutes=5)
# }

# # DAG 정의
# with DAG(
#     'fred_uploader_elasticsearch',
#     default_args=default_args,
#     description="연준 데이터를 Elasticsearch에 집어 넣습니다.",
#     schedule_interval='@daily',
#     start_date=datetime(2015, 1, 1),
#     catchup=False,
#     tags=['elasticsearch','test', 'fred'],
# ) as dag:
    
#     # PythonOperator 설정
#     t1 = PythonOperator(
#         task_id="upload_fred_data_to_elasticsearch",
#         python_callable=dataframe_to_elasticsearch,
#         execution_timeout=timedelta(minutes=5) # 태스크 최대 실행 시간 설정
#     )

#     t1

import requests
import pandas as pd
from functools import reduce
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
# from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from prophet import Prophet
import eland as ed
from opensearchpy import OpenSearch
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)

# API 기본 URL과 분류 코드 설정
BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch/2IJKJSOY6OFOQZ28900C/json/kr/1/100000/601Y002/M/200001/202409/X/{}/DAV"
CODES = 1300

# Elasticsearch 설정
# es = Elasticsearch('http://host.docker.internal:9200')

def fetch_data_from_api():
    """API에서 데이터를 수집하고 병합합니다."""

    url = BASE_URL.format(CODES)
    response = requests.get(url)
    data = response.json()

    if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
        df = pd.DataFrame(data['StatisticSearch']['row'])
        item_name = df['ITEM_NAME2'].iloc[0]
        df = df[['TIME', 'DATA_VALUE']].rename(columns={'DATA_VALUE': item_name})

    else:
        print(f"데이터 없음: 코드 {CODES}")

    df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m')
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric)
    return df


def fetch_kosis_data():
    """KOSIS API에서 데이터를 수집하고 처리합니다."""
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList",
        "apiKey": "NGFlNDEwNzU4NTVjN2Y2ZTcyYzJiYmI5NjlhY2ExMzc=",
        "orgId": "101",
        "tblId": "DT_1J22112",
        "itmId": "T+",
        "objL1": "T10+",
        "objL2": "ALL",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "M",
        "startPrdDe": "202001",
        "endPrdDe": "202409",
        "outputFields": "NM PRD_DE"
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data)
    pivot_df = df.pivot_table(index='PRD_DE', columns='C2_NM', values='DT', aggfunc='max').reset_index()
    pivot_df['PRD_DE'] = pd.to_datetime(pivot_df['PRD_DE'], format='%Y%m')
    pivot_df.iloc[:, 1:] = pivot_df.iloc[:, 1:].apply(pd.to_numeric)
    pivot_df.rename(columns={'PRD_DE': 'TIME'}, inplace=True)
    return pivot_df

def forecast_future(df, column_name, periods=3):
    """Prophet 모델을 사용해 미래 예측을 수행합니다."""
    df_prophet = df[['TIME', column_name]].rename(columns={'TIME': 'ds', column_name: 'y'})
    model = Prophet()
    model.fit(df_prophet)
    future = model.make_future_dataframe(periods=periods, freq='M')
    forecast = model.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def upload_to_elasticsearch(df, index_name):
    """ 인덱스가 이미 존재하면 삭제"""
    # if es.indices.exists(index=index_name):
    #     es.indices.delete(index=index_name)
    #     print("기존 인덱스 삭제 완료")
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        print("기존 인덱스 삭제 완료")

    """데이터를 Elasticsearch에 업로드합니다."""
    # ed.pandas_to_eland(
    #     pd_df=df,
    #     es_client=es,
    #     es_dest_index=index_name,
    #     es_if_exists="append",
    #     es_refresh=True,
    # )
    ed.pandas_to_eland(
        pd_df=df,
        es_client=client,
        es_dest_index=index_name,
        es_if_exists="append",
        es_refresh=True,
    )

# def create_indices():
#     """Elasticsearch 인덱스를 생성합니다."""
#     try:
#         es.indices.create(index='항목별_개인신용카드_소비현황')
#         # es.indices.create(index='소비자물가지수')
#     except Exception as e:
#         print(f"인덱스 생성 중 오류 발생: {e}")

def run_data_pipeline():
    """데이터를 수집, 예측, 그리고 Elasticsearch에 업로드합니다."""
    pce_df = fetch_data_from_api()
    cpi_df = fetch_kosis_data()

    # 예측 수행
    pce_forecast = forecast_future(pce_df, '식료품')
    cpi_forecast = forecast_future(cpi_df, '농축수산물')

    # Elasticsearch 업로드
    upload_to_elasticsearch(pce_forecast, '항목별_개인신용카드_소비현황')
    upload_to_elasticsearch(cpi_forecast, '소비자물가지수')

# 기본 DAG 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    'pce_uploader_elasticsearch',
    default_args=default_args,
    description="우리조장 신호섭",
    schedule_interval='@daily',
    start_date=datetime.now(),
    catchup=False,
    tags=['elasticsearch', 'api', 'forecast'],
    dagrun_timeout=timedelta(minutes=20)
) as dag:

    # 인덱스 생성 태스크
    # create_indices_task = PythonOperator(
    #     task_id='create_indices',
    #     python_callable=create_indices,
    #     execution_timeout=timedelta(minutes=30)
    # )

    # 데이터 파이프라인 실행 태스크
    run_pipeline_task = PythonOperator(
        task_id='run_data_pipeline',
        python_callable=run_data_pipeline,
        execution_timeout=timedelta(hours=1)
    )

    # 태스크 간의 의존성 설정
    run_pipeline_task