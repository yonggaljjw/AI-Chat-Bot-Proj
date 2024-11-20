from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import os
import requests
import xml.etree.ElementTree as ET
import logging
from sqlalchemy import create_engine
import pymysql

# 환경 변수 로드
load_dotenv()

# MySQL 연결 설정
username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")

# API 설정
API_CONFIG = {
    'base_url': 'http://apis.data.go.kr/1130000/FftcBrandFrcsStatsService/getBrandFrcsStats',
    'api_key': os.getenv("FRANCHISE_KEY_DECODED")
}

def get_latest_year_in_mysql():
    """MySQL에서 가장 최근 연도 조회"""
    query = "SELECT MAX(yr) FROM franchise_data"
    result = engine.execute(query).fetchone()
    latest_year = result[0] if result[0] is not None else 2016  # 데이터가 없는 경우 시작 연도의 이전 해 반환
    return int(latest_year)  # 정수형으로 변환

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
    latest_year = get_latest_year_in_mysql()
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

def append_to_mysql(df):
    """신규 데이터를 MySQL에 추가"""
    if df is None or df.empty:
        logging.info("No data to append")
        return 0
        
    try:
        df.to_sql('franchise_data', con=engine, if_exists='append', index=False)
        logging.info(f"Successfully appended {len(df)} records to MySQL")
        return len(df)

    except Exception as e:
        logging.error(f"Error appending data to MySQL: {str(e)}")
        raise

def process_franchise_data(**context):
    """전체 프로세스를 처리하는 함수"""
    df = fetch_new_data(**context)
    return append_to_mysql(df)

# DAG 기본 설정
default_args = {
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG 정의
with DAG(
    '11_franchise_data_pipeline',
    default_args=default_args,
    description='Franchise data collection and MySQL upload pipeline',
    schedule_interval='@monthly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['franchise', 'mysql', 'data']
) as dag:

    process_task = PythonOperator(
        task_id='process_franchise_data',
        python_callable=process_franchise_data,
    )

    process_task
