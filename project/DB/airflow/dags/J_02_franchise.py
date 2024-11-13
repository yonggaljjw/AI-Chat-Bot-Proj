from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import opensearch_py_ml as oml
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# .env 파일 로드
load_dotenv()

# OpenSearch 설정
host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))

# OpenSearch 클라이언트 설정
client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)

# API 설정
BASE_URL = "http://apis.data.go.kr/1130000/FftcBrandFrcsStatsService/getBrandFrcsStats"
API_KEY = os.getenv("FRANCHISE_KEY_DECODED")  # 디코딩된 키 사용

def ensure_index_exists():
    """인덱스가 없을 경우에만 생성"""
    try:
        if not client.indices.exists(index='franchise_stats'):
            client.indices.create(
                index='franchise_stats',
                body={
                    "settings": {
                        "index": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1
                        }
                    },
                    "mappings": {
                        "properties": {
                            "yr": {"type": "keyword"},                    # 년도
                            "indutyLclasNm": {"type": "keyword"},        # 업종 대분류명
                            "indutyMlsfcNm": {"type": "keyword"},        # 업종 중분류명
                            "corpNm": {"type": "keyword"},               # 법인명
                            "brandNm": {"type": "keyword"},              # 브랜드명
                            "frcsCnt": {"type": "integer"},              # 가맹점 수
                            "newFrcsRgsCnt": {"type": "integer"},        # 신규가맹점 등록 수
                            "ctrtEndCnt": {"type": "integer"},           # 계약종료 수
                            "ctrtCncltnCnt": {"type": "integer"},        # 계약취소 수
                            "nmChgCnt": {"type": "integer"},             # 명칭변경 수
                            "avrgSlsAmt": {"type": "float"},             # 평균매출액
                            "arUnitAvrgSlsAmt": {"type": "float"},       # 면적당 평균매출액
                            "timestamp": {"type": "date"}                # 데이터 수집 시점
                        }
                    }
                }
            )
            print("Index 'franchise_stats' created successfully.")
    except Exception as e:
        print(f"Error checking/creating index: {e}")

def fetch_and_upload_franchise_data(year, **context):
    """특정 연도의 가맹점 현황 데이터를 가져와서 OpenSearch에 업로드하는 함수"""
    
    def fetch_page(page_no):
        """특정 페이지의 데이터를 가져오는 함수"""
        params = {
            'serviceKey': API_KEY,
            'pageNo': str(page_no),
            'numOfRows': '1000',
            'yr': str(year)
        }
        
        response = requests.get(
            BASE_URL, 
            params=params, 
            verify=False,
            headers={'accept': '*/*'}
        )
        print(f"\nAPI Response for page {page_no}:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text[:500]}")  # 응답 내용 출력
        return response
    
    try:
        # 인덱스 존재 확인 및 생성
        ensure_index_exists()
        
        # 해당 연도의 기존 데이터 삭제
        query = {
            "query": {
                "term": {
                    "yr": str(year)
                }
            }
        }
        try:
            client.delete_by_query(
                index='franchise_stats',
                body=query,
                refresh=True
            )
            print(f"Deleted existing data for year {year}")
        except Exception as e:
            print(f"No existing data found for year {year} or error occurred: {e}")
        
        # 첫 페이지 호출하여 전체 데이터 수 확인
        first_response = fetch_page(1)
        root = ET.fromstring(first_response.content)
        
        # 결과 코드 확인 및 에러 처리
        result_code = root.find('.//resultCode')
        result_msg = root.find('.//resultMsg')
        
        if result_code is None or result_msg is None:
            error_msg = f"Invalid API response format for year {year}"
            print(error_msg)
            print("API Response:", first_response.text)
            raise ValueError(error_msg)
            
        if result_code.text != '00':
            error_msg = f"API error for year {year}: {result_msg.text}"
            print(error_msg)
            raise ValueError(error_msg)
        
        # 전체 데이터 수 확인
        total_count_elem = root.find('.//totalCount')
        if total_count_elem is None or not total_count_elem.text:
            error_msg = f"Could not find total count in API response for year {year}"
            print(error_msg)
            print("API Response:", first_response.text)
            raise ValueError(error_msg)
            
        total_count = int(total_count_elem.text)
        print(f"Total records for year {year}: {total_count}")
        
        if total_count == 0:
            print(f"No data available for year {year}")
            return f"No data available for year {year}"
        
        # 필요한 총 페이지 수 계산
        page_size = 1000
        total_pages = (total_count + page_size - 1) // page_size
        print(f"Total pages to fetch: {total_pages}")
        
        # 모든 페이지의 데이터 수집
        all_data = []
        
        for page in range(1, total_pages + 1):
            print(f"Fetching page {page} of {total_pages} for year {year}")
            response = fetch_page(page)
            page_root = ET.fromstring(response.content)
            
            # 각 페이지의 아이템 처리
            items = page_root.findall('.//item')
            if not items:
                print(f"No items found in page {page}")
                continue
                
            for item in items:
                data_dict = {}
                for child in item:
                    if child.tag in ['frcsCnt', 'newFrcsRgsCnt', 'ctrtEndCnt', 'ctrtCncltnCnt', 'nmChgCnt']:
                        try:
                            data_dict[child.tag] = int(child.text) if child.text else None
                        except (ValueError, TypeError):
                            data_dict[child.tag] = None
                    elif child.tag in ['avrgSlsAmt', 'arUnitAvrgSlsAmt']:
                        try:
                            data_dict[child.tag] = float(child.text) if child.text else None
                        except (ValueError, TypeError):
                            data_dict[child.tag] = None
                    else:
                        data_dict[child.tag] = child.text
                
                data_dict['timestamp'] = datetime.now().isoformat()
                all_data.append(data_dict)
            
            print(f"Collected {len(all_data)} records so far...")
        
        if not all_data:
            print(f"No data collected for year {year}")
            return f"No data collected for year {year}"
        
        # DataFrame 생성
        df = pd.DataFrame(all_data)
        print(f"\nTotal records collected for year {year}: {len(df)}")
        print("Sample data:")
        print(df.head())
        print("Data shape:", df.shape)
        
        # OpenSearch에 데이터 업로드
        oml.pandas_to_opensearch(
            pd_df=df,
            os_client=client,
            os_dest_index="franchise_stats",
            os_if_exists="append",
            os_refresh=True
        )
        
        return f"Successfully uploaded {len(df)} records for year {year} to OpenSearch"
    
    except Exception as e:
        print(f"Error processing data for year {year}: {str(e)}")
        raise


# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
with DAG(
    'franchise_stats_etl',
    default_args=default_args,
    description='연도별 가맹점 현황 데이터 수집 및 OpenSearch 적재',
    schedule_interval='@yearly',
    catchup=False,
    tags=['opensearch', 'franchise', 'data']
) as dag:
    
    # 2015년부터 현재까지의 데이터를 수집하는 태스크 생성
    tasks = []
    start_year = 2015
    current_year = datetime.now().year
    
    for year in range(start_year, current_year + 1):
        task = PythonOperator(
            task_id=f'fetch_and_upload_data_{year}',
            python_callable=fetch_and_upload_franchise_data,
            op_kwargs={'year': year},
            dag=dag
        )
        tasks.append(task)
    
    # 태스크 의존성 설정: 순차적으로 실행
    for i in range(len(tasks)-1):
        tasks[i] >> tasks[i+1]

# DAG 파일 직접 실행 시 테스트를 위한 코드
if __name__ == "__main__":
    # 특정 연도의 데이터를 테스트로 가져오기
    test_year = 2023
    print(f"\nTesting API call and OpenSearch upload for year {test_year}")
    fetch_and_upload_franchise_data(test_year)
