import requests
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from prophet import Prophet
import eland as ed
from opensearchpy import OpenSearch
from package.vector_embedding import generate_embedding
import opensearch_py_ml as oml
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
BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch/" + os.getenv("CARD_API") + "/json/kr/1/100000/601Y002/M/200001/202409/X/{}/DAV"
CODES = 1300

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
        "apiKey": os.getenv("KOSIS_API"),
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

def upload_to_opensearch(df, index_name):
    """ 인덱스가 이미 존재하면 삭제"""
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        print("기존 인덱스 삭제 완료")

    # Embedding vector 생성 
    # metadata -> field_name : value
    list_fields = df.columns.tolist()
    for index, row in df.iterrows():
        metadata = ""
        for field in list_fields:
            metadata += f"{field}: {row[field]}\n"
        df['embedding_vector'] = df.apply(metadata, axis=1)
        df['embedding_vector'] = df['embedding_vector'].apply(generate_embedding)    
    
    """데이터를 OpenSearch에 업로드합니다."""
    oml.pandas_to_opensearch(
        pd_df=df,
        os_client=client,
        os_dest_index=index_name,
        os_if_exists="append",
        os_refresh=True,
    )

def run_data_pipeline():
    """데이터를 수집, 예측, 그리고 OpenSearch에 업로드합니다."""
    pce_df = fetch_data_from_api()
    cpi_df = fetch_kosis_data()

    # 예측 수행
    pce_forecast = forecast_future(pce_df, '식료품')
    cpi_forecast = forecast_future(cpi_df, '농축수산물')

    # OpenSearch 업로드
    upload_to_opensearch(pce_forecast, 'Credit_card_usage')
    upload_to_opensearch(cpi_forecast, 'Consumer_Index')

# 기본 DAG 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    '06_PCE_data',
    default_args=default_args,
    description="소비자물가, 개인신용카드 소비현황 예측 데이터를 업로드합니다.",
    schedule_interval='@daily',
    start_date=datetime.now(),
    catchup=False,
    tags=['OpenSearch', 'api', 'forecast'],
    dagrun_timeout=timedelta(minutes=20)
) as dag:

    # 데이터 파이프라인 실행 태스크
    run_pipeline_task = PythonOperator(
        task_id='run_data_pipeline',
        python_callable=run_data_pipeline,
        execution_timeout=timedelta(hours=1)
    )

    # 태스크 간의 의존성 설정
    run_pipeline_task