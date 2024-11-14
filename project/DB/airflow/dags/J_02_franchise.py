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
    hosts=[{'host': host, 'port': port}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=False
)

# API 설정
BASE_URL = "http://apis.data.go.kr/1130000/FftcBrandFrcsStatsService/getBrandFrcsStats"
API_KEY = os.getenv("FRANCHISE_KEY_DECODED")

def ensure_index_exists():
    """인덱스가 없을 경우에만 생성"""
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
                        "yr": {"type": "keyword"},
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
        print("Index 'franchise_stats' created successfully.")

def fetch_franchise_data(year):
    """특정 연도의 데이터를 API에서 가져와 DataFrame으로 반환하는 함수"""
    def fetch_page(page_no):
        params = {
            'serviceKey': API_KEY,
            'pageNo': str(page_no),
            'numOfRows': '1000',
            'yr': str(year)
        }
        return requests.get(BASE_URL, params=params, verify=False)

    all_data = []
    first_response = fetch_page(1)
    root = ET.fromstring(first_response.content)

    # 총 데이터 수 확인
    total_count = int(root.find('.//totalCount').text)
    total_pages = (total_count + 999) // 1000  # 페이지 수 계산

    for page in range(1, total_pages + 1):
        response = fetch_page(page)
        page_root = ET.fromstring(response.content)

        for item in page_root.findall('.//item'):
            data_dict = {child.tag: int(child.text) if child.tag in ['frcsCnt', 'newFrcsRgsCnt', 'ctrtEndCnt', 'ctrtCncltnCnt', 'nmChgCnt'] 
                         else float(child.text) if child.tag in ['avrgSlsAmt', 'arUnitAvrgSlsAmt'] 
                         else child.text for child in item}
            data_dict['date'] = f"{year}-01-01"
            all_data.append(data_dict)

    return pd.DataFrame(all_data)

def concat_and_upload_data(**context):
    """신규 연도의 데이터를 가져와 기존 데이터와 concat하여 OpenSearch에 업로드하는 함수"""
    ensure_index_exists()

    # OpenSearch에서 기존 데이터 가져오기
    existing_data_query = {"query": {"match_all": {}}}
    existing_data = oml.opensearch_to_pandas(
        os_client=client,
        os_index="franchise_stats",
        os_query=existing_data_query
    )

    # 새 연도 데이터 가져오기
    current_year = datetime.now().year - 1  # 전년도 데이터 가져오기
    new_data = fetch_franchise_data(current_year)
    if new_data.empty:
        print(f"No data available for year {current_year}.")
        return f"No data available for year {current_year}."

    # 데이터 합치기
    franchise_data_all = pd.concat([existing_data, new_data], ignore_index=True)

    # 날짜 형식 변환 (YYYY-MM-01)
    franchise_data_all['date'] = pd.to_datetime(franchise_data_all['date']).dt.strftime('%Y-%m-01')

    # 기존 데이터 삭제 후 새로운 데이터 업로드
    client.indices.delete(index='franchise_stats', ignore=[400, 404])  # 인덱스 삭제 후 다시 생성
    ensure_index_exists()
    
    oml.pandas_to_opensearch(
        pd_df=franchise_data_all,
        os_client=client,
        os_dest_index="franchise_stats",
        os_if_exists="append",
        os_refresh=True
    )
    print(f"Data for year {current_year} concatenated and uploaded successfully.")

# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
with DAG(
    'franchise_stats_etl_concat',
    default_args=default_args,
    description='신규 연도 데이터 수집 및 기존 데이터와 합쳐 OpenSearch에 업로드',
    schedule_interval='@yearly',
    catchup=False,
    tags=['opensearch', 'franchise', 'data']
) as dag:
    
    # 데이터를 새로 추가하고 기존 데이터와 concat하여 업로드
    upload_task = PythonOperator(
        task_id='concat_and_upload_data',
        python_callable=concat_and_upload_data,
    )
=======
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
        
        # # 첫 페이지 호출하여 전체 데이터 수 확인
        # first_response = fetch_page(1)
        # root = ET.fromstring(first_response.content)
        
        # # 결과 코드 확인
        # result_code = root.find('.//resultCode')
        # if result_code is not None and result_code.text != '00':
        #     print(f"Error in API response. Result code: {result_code.text}")
        #     result_msg = root.find('.//resultMsg')
        #     if result_msg is not None:
        #         print(f"Result message: {result_msg.text}")
        #     return f"Error in API response for year {year}"
        
        # 전체 데이터 수 확인
        total_count = int(root.find('.//totalCount').text)
        print(f"Total records for year {year}: {total_count}")
        
        # 필요한 총 페이지 수 계산
        page_size = 1000
        total_pages = (total_count + page_size - 1) // page_size
        print(f"Total pages to fetch: {total_pages}")
        
        # 모든 페이지의 데이터 수집
        all_data = []
        for page in range(1, total_pages + 1):
            print(f"Fetching page {page} of {total_pages} for year {year}")
            response = fetch_page(page)
            root = ET.fromstring(response.content)
            
            for item in root.findall('.//item'):
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
        
        # DataFrame 생성
        df = pd.DataFrame(all_data)
        
        if df.empty:
            print(f"No data found for year {year}")
            return f"No data found for year {year}"
            
        print(f"Total records collected for year {year}: {len(df)}")
        print("\nSample data:")
        print(df.head())
        print("\nData shape:", df.shape)
        
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
