from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import os
from opensearchpy import OpenSearch, helpers
import requests
import xml.etree.ElementTree as ET
import logging

# 환경 변수 로드
load_dotenv()

# OpenSearch 연결 설정
host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=False
)

# API 설정
API_CONFIG = {
    'base_url': 'http://apis.data.go.kr/1130000/FftcBrandFrcsStatsService/getBrandFrcsStats',
    'api_key': os.getenv("FRANCHISE_KEY_DECODED")
}

def create_index_if_not_exists():
    """OpenSearch 인덱스가 없으면 생성"""
    index_name = 'franchise_data'
    
    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "yr": {"type": "integer"},
                        "indutyLclasNm": {"type": "keyword"},
                        "indutyMlsfcNm": {"type": "keyword"},
                        "corpNm": {"type": "keyword"},
                        "brandNm": {"type": "keyword"},
                        "frcsCnt": {"type": "integer"},
                        "newFrcsRgsCnt": {"type": "integer"},
                        "ctrtEndCnt": {"type": "integer"},
                        "ctrtCncltnCnt": {"type": "integer"},
                        "nmChgCnt": {"type": "integer"},
                        "avrgSlsAmt": {"type": "float"},
                        "arUnitAvrgSlsAmt": {"type": "float"},
                        "date": {"type": "date"}
                    }
                }
            }
        )
        logging.info(f"Created new index: {index_name}")
    return index_name

def get_latest_year_in_opensearch():
    """OpenSearch에서 가장 최근 연도 조회"""
    index_name = 'franchise_data'
    
    if not client.indices.exists(index=index_name):
        return 2016  # 데이터가 없는 경우 시작 연도의 이전 해 반환
    
    query = {
        "size": 0,
        "aggs": {
            "max_year": {
                "max": {
                    "field": "yr"
                }
            }
        }
    }
    
    try:
        response = client.search(
            body=query,
            index=index_name
        )
        latest_year = int(response['aggregations']['max_year']['value'])
        logging.info(f"Latest year in OpenSearch: {latest_year}")
        return latest_year
    except Exception as e:
        logging.error(f"Error fetching latest year: {e}")
        return 2016

def fetch_new_data(**context):
    """신규 연도의 데이터만 가져와서 DataFrame으로 변환"""
    logging.info("Starting to fetch new franchise data")
    
    def fetch_year_data(year):
        logging.info(f"Fetching data for year {year}")
        
        def fetch_page(page_no):
            params = {
                'serviceKey': API_CONFIG['api_key'],
                'pageNo': str(page_no),
                'numOfRows': '1000',
                'yr': str(year)
            }
            
            response = requests.get(
                API_CONFIG['base_url'], 
                params=params, 
                verify=False, 
                headers={'accept': '*/*'}
            )
            return response

        try:
            first_response = fetch_page(1)
            root = ET.fromstring(first_response.content)
            
            result_code = root.find('.//resultCode')
            if result_code is not None and result_code.text != '00':
                logging.info(f"No data available for year {year}")
                return None

            total_count = int(root.find('.//totalCount').text)
            if total_count == 0:
                logging.info(f"No records found for year {year}")
                return None
                
            page_size = 1000
            total_pages = (total_count + page_size - 1) // page_size
            logging.info(f"Found {total_count} records for year {year}")

            year_data = []
            for page in range(1, total_pages + 1):
                response = fetch_page(page)
                root = ET.fromstring(response.content)

                for item in root.findall('.//item'):
                    data_dict = {}
                    for child in item:
                        if child.tag in ['frcsCnt', 'newFrcsRgsCnt', 'ctrtEndCnt', 'ctrtCncltnCnt', 'nmChgCnt']:
                            data_dict[child.tag] = int(child.text) if child.text else None
                        elif child.tag in ['avrgSlsAmt', 'arUnitAvrgSlsAmt']:
                            data_dict[child.tag] = float(child.text) if child.text else None
                        else:
                            data_dict[child.tag] = child.text

                    data_dict['date'] = context['execution_date'].strftime('%Y-%m-01')
                    year_data.append(data_dict)

            return year_data

        except Exception as e:
            logging.error(f"Error fetching data for year {year}: {str(e)}")
            raise

    # 최신 연도 확인 및 신규 데이터 수집
    latest_year = get_latest_year_in_opensearch()
    current_year = datetime.now().year
    
    new_data = []
    for year in range(latest_year + 1, current_year + 1):
        year_data = fetch_year_data(year)
        if year_data:
            new_data.extend(year_data)
            logging.info(f"Successfully fetched data for year {year}")
    
    if not new_data:
        logging.info("No new data to append")
        return None
    
    df = pd.DataFrame(new_data)
    df['date'] = pd.to_datetime(df['date'])
    logging.info(f"Created DataFrame with {len(df)} new records")
    
    return df

def append_to_opensearch(df):
    """신규 데이터를 OpenSearch에 추가"""
    if df is None or df.empty:
        logging.info("No data to append")
        return 0
        
    try:
        index_name = create_index_if_not_exists()
        
        actions = [
            {
                "_index": index_name,
                "_source": doc
            }
            for doc in df.to_dict('records')
        ]
        
        success, failed = helpers.bulk(client, actions, stats_only=True)
        logging.info(f"Successfully appended {success} documents to OpenSearch")
        
        if failed > 0:
            logging.warning(f"Failed to append {failed} documents")
            
        return success

    except Exception as e:
        logging.error(f"Error appending data to OpenSearch: {str(e)}")
        raise

def process_franchise_data(**context):
    """전체 프로세스를 처리하는 함수"""
    df = fetch_new_data(**context)
    return append_to_opensearch(df)

# DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG 정의
with DAG(
    'franchise_data_pipeline',
    default_args=default_args,
    description='Franchise data collection and OpenSearch upload pipeline',
    schedule_interval='@monthly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['franchise', 'opensearch', 'data']
) as dag:

    process_task = PythonOperator(
        task_id='process_franchise_data',
        python_callable=process_franchise_data,
    )
    