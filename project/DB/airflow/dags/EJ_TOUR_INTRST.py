from datetime import datetime, timedelta
import json
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    # http_auth=auth,
    use_ssl=False,
    verify_certs=False
)

INDEX_NAME = "tour_area_intrst_20240930"
DATA_FILE_PATH = "./dags/package/CI_OVSEA_TOUR_AREA_INTRST_DGREE_INFO_20240930.json"

# OpenSearch 인덱스를 생성 또는 갱신하는 함수 정의
def create_or_update_index():
    # 인덱스가 이미 존재하면 삭제
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
        print(f"기존 인덱스 '{INDEX_NAME}' 삭제 완료")

    # 새로운 인덱스 생성 (필드 타입 설정 포함)
    index_settings = {
        "mappings": {
            "properties": {
                "RESPOND_ID": {"type": "keyword"},
                "EXAMIN_BEGIN_DE": {"type": "date"},
                "SEXDSTN_FLAG_CD": {"type": "keyword"},
                "AGRDE_FLAG_NM": {"type": "keyword"},
                "ANSWRR_OC_AREA_NM": {"type": "keyword"},
                "HSHLD_INCOME_DGREE_NM": {"type": "keyword"},
                # 각 관광 관심 필드에 대한 추가 설정
                "CHINA_TOUR_INTRST_VALUE": {"type": "keyword"},
                "JP_TOUR_INTRST_VALUE": {"type": "keyword"},
                "HONGKONG_MACAU_TOUR_INTRST_VALUE": {"type": "keyword"},
                "SEASIA_TOUR_INTRST_VALUE": {"type": "keyword"},
                "MDLEST_SWASIA_TOUR_INTRST_VALUE": {"type": "keyword"},
                "USA_CANADA_TOUR_INTRST_VALUE": {"type": "keyword"},
                "SAMRC_LAMRC_TOUR_INTRST_VALUE": {"type": "keyword"},
                "WEURP_NEURP_TOUR_INTRST_VALUE": {"type": "keyword"},
                "EEURP_TOUR_INTRST_VALUE": {"type": "keyword"},
                "SEURP_TOUR_INTRST_VALUE": {"type": "keyword"},
                "SPCPC_TOUR_INTRST_VALUE": {"type": "keyword"},
                "AFRICA_TOUR_INTRST_VALUE": {"type": "keyword"}
            }
        }
    }
    client.indices.create(index=INDEX_NAME, body=index_settings)
    print(f"새 인덱스 '{INDEX_NAME}' 생성 완료")

# OpenSearch에 데이터를 업로드하는 함수 정의
def upload_to_opensearch():
    # JSON 파일에서 데이터 읽기
    with open(DATA_FILE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 업로드할 데이터 준비
    actions = [
        {
            "_op_type": "index",
            "_index": INDEX_NAME,
            "_source": entry
        }
        for entry in data
    ]

    # 데이터가 있을 경우, OpenSearch에 업로드
    if actions:
        helpers.bulk(client, actions)
        print(f"{len(actions)}개의 데이터가 '{INDEX_NAME}'에 업로드되었습니다.")
    else:
        print("업로드할 데이터가 없습니다")

# 기본 인자를 설정하여 Airflow DAG 정의
default_args = {
    'depends_on_past': False,  # 이전 작업의 성공 여부에 관계없이 실행
    'retries': 1,  # 실패 시 재시도 횟수
    'retry_delay': timedelta(minutes=5)  # 재시도 간격 (5분)
}

# DAG 정의
with DAG(
    'EJ_TOUR_INTRST',  # DAG 이름
    default_args=default_args,  # 기본 인자 설정
    description="관광 관심 데이터를 OpenSearch에 업로드하는 DAG",  # 설명
    schedule_interval=None,  # 수동 실행
    start_date=datetime.now(),  # 현재 시점에서 실행
    catchup=False,  # 과거 날짜의 작업은 무시
    tags=['opensearch', 'tour', 'data_upload']  # 태그 설정 (DAG 분류에 사용)
) as dag:

    # OpenSearch 인덱스 생성 또는 초기화 작업
    clear_data = PythonOperator(
        task_id="create_or_update_index",  # 작업 ID
        python_callable=create_or_update_index,  # 실행할 함수
    )

    # 데이터를 OpenSearch에 업로드하는 작업 정의
    upload_data = PythonOperator(
        task_id="upload_data",  # 작업 ID
        python_callable=upload_to_opensearch,  # 실행할 함수
    )

    # 작업 순서 정의 (인덱스 생성 후 데이터 업로드)
    clear_data >> upload_data
