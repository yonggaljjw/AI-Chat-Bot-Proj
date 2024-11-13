import os
import urllib.request
import json
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenSearch connection details
host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))  # For testing only. Don't store credentials in code.

naver_client_id = os.getenv("eunji_naver_api")
naver_client_secret = os.getenv("eunji_naver_api_key")

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=False
)

# travel_info 생성 함수
def create_travel_info(df):
    travel_info = []
    for _, row in df.iterrows():
        country = row['나라']
        city = row['도시명']
        group_name = f"{city} 여행"
        keywords = [country, f"{country} 여행", city, "여행", "해외여행"]
        
        travel_info.append({
            "group_name": group_name,
            "keywords": keywords
        })
    return travel_info

# 네이버 API 데이터 요청 및 저장 함수
def fetch_data_from_naver_api(group_name, keywords, start_date, end_date, time_unit, client_id, client_secret, url):
    # JSON body 생성
    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [{"groupName": group_name, "keywords": keywords}]
    })

    # Request 구성 및 전송
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    request.add_header("Content-Type", "application/json")
    
    try:
        response = urllib.request.urlopen(request, data=body.encode("utf-8"))
        rescode = response.getcode()
        
        if rescode == 200:
            response_body = response.read()
            # 응답이 비어있지 않으면 반환
            if response_body:
                result = response_body.decode('utf-8')
                return json.loads(result)  # JSON 파싱해서 반환
            else:
                print(f"Empty response for {group_name}")
                return None
        else:
            print(f"Error Code: {rescode} for group {group_name}")
            return None
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason} for group {group_name}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e} for group {group_name}")
        return None

# 결과 리스트에 데이터를 추가하는 함수
def append_to_results(group_name, result, all_results):
    if result:
        all_results.append({
            "group_name": group_name,
            "result": result
        })
        print(f"Added result for {group_name}")
    else:
        print(f"No result to add for {group_name}")



# 최종 결과를 하나의 JSON 파일로 저장하는 함수
# def save_results_to_json(all_results, output_folder, file_name="all_travel_data.json"):
#     os.makedirs(output_folder, exist_ok=True)  # 폴더가 없으면 생성
#     final_file_name = os.path.join(output_folder, file_name)
#     with open(final_file_name, "w", encoding="utf-8") as f:
#         json.dump(all_results, f, ensure_ascii=False, indent=4)
#     print(f"Saved all results to {final_file_name}")

# Define index name and setup
index_name = "travel_naver_search_all"
def setup_index():
    if not client.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "startDate": {"type": "date"},
                    "endDate": {"type": "date"},
                    "timeUnit": {"type": "keyword"},
                    "device": {"type": "keyword"},
                    "ages": {"type": "keyword"},
                    "gender": {"type": "keyword"},
                    "keywordGroups": {
                        "type": "nested",
                        "properties": {
                            "groupName": {"type": "keyword"},
                            "keywords": {"type": "keyword"}
                        }
                    }
                }
            }
        }
        client.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created with mapping.")
    else:
        print(f"Index '{index_name}' already exists.")



def upload_to_opensearch(documents):
    # 문서를 일괄 업로드
    if documents:
        helpers.bulk(client, documents, index={index_name})
        print(f"Uploaded {len(documents)} documents to index '{index_name}'.")
    else:
        print("No JSON files found to upload.")



# 전체 프로세스를 실행하는 함수
def main():
    # 데이터 로드
    df_country = pd.read_csv("./dags/package/국토연구원 세계도시정보 자료(2019년).csv", encoding="EUC-KR")
    
    # 네이버 API 인증 정보 및 요청 URL
    client_id = naver_client_id
    client_secret = naver_client_secret
    url = "https://openapi.naver.com/v1/datalab/search"
    
    # 기본 요청 변수 설정
    start_date = "2024-01-01"
    end_date = "2024-11-10"
    time_unit = "week"
    
    # 결과 저장을 위한 리스트
    all_results = []
    
    # 여행 정보 생성
    travel_info = create_travel_info(df_country)
    
    # 각 여행 정보를 사용해 네이버 API 요청 및 결과 저장
    for info in travel_info:
        group_name = info["group_name"]
        keywords = info["keywords"]
        result = fetch_data_from_naver_api(group_name, keywords, start_date, end_date, time_unit, client_id, client_secret, url)
        append_to_results(group_name, result, all_results)
    
    # 모든 결과를 하나의 JSON 파일로 저장
    upload_to_opensearch(all_results)


# Airflow DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 10),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'travel_naver_search_all',
    default_args=default_args,
    description='Fetch and upload travel data to OpenSearch',
    schedule_interval=None,  
    catchup=False,
) as dag:

    setup_index_task = PythonOperator(
        task_id="setup_index",
        python_callable=setup_index
    )

    # Airflow Operator로 함수 실행
    task = PythonOperator(
        task_id='fetch_and_upload_travel_data',
        python_callable=main,
        dag=dag,
    )
    setup_index_task >> task