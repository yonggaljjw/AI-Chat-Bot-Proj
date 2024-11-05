from datetime import datetime, timedelta
import pandas as pd
import eland as ed  # Pandas와 Elasticsearch 연동 라이브러리
from airflow import DAG  # Airflow에서 DAG을 정의하기 위한 모듈
from airflow.operators.python_operator import PythonOperator  # Python 작업 정의용 Operator
from elasticsearch import Elasticsearch  # Elasticsearch 클라이언트

# Elasticsearch 인스턴스 생성 (Docker 내부에서 실행 중인 호스트에 연결)
es = Elasticsearch('http://192.168.0.101:9200')

# Elasticsearch 인덱스 생성 또는 재설정 함수
def create_or_update_index():
    """Elasticsearch 인덱스를 생성 또는 갱신하여 '날짜' 필드를 date 타입으로 설정"""
    # 인덱스가 이미 존재하면 삭제
    if es.indices.exists(index='raw_data'):
        es.indices.delete(index='raw_data')
        print("기존 인덱스 삭제 완료")

    # 새로운 인덱스 생성 (날짜 필드를 date 타입으로 설정)
    index_settings = {
        "mappings": {
            "properties": {
                "제목": {"type": "text"},
                "날짜": {"type": "date"},
                "URL": {"type": "text"},
                "내용": {"type": "text"},
                "개정이유": {"type": "text"},
                "주요내용": {"type": "text"}
            }
        }
    }
    es.indices.create(index='raw_data', body=index_settings)
    print("새로운 인덱스 생성 완료")

# Elasticsearch 인덱스 데이터 초기화 작업
def clear_elasticsearch_data():
    """기존 Elasticsearch 데이터 초기화 및 인덱스 재설정"""
    create_or_update_index()
    print("인덱스 초기화 및 재설정 완료")

# CSV 데이터를 Elasticsearch로 업로드하는 함수 정의
def dataframe_to_elasticsearch_first():
    """CSV 데이터를 Elasticsearch에 저장"""
    # CSV 파일 로드 및 결측치 제거
    df = pd.read_csv("./dags/fsc_announcements_extract.csv")
    df['내용'] = df['내용'].fillna('내용 없음')

    # '날짜' 열을 datetime 형식으로 변환
    df['날짜'] = pd.to_datetime(df['날짜'], format='%Y-%m-%d')  # 날짜 형식에 맞게 수정

    # DataFrame 데이터를 Elasticsearch로 전송
    ed.pandas_to_eland(
        pd_df=df,
        es_client=es,
        es_dest_index="raw_data",
        es_if_exists="append",  # 기존 데이터에 추가
        es_refresh=True  # 인덱스 즉시 새로고침
    )
    print("데이터 업로드 완료")

# 기본 인자 설정 (Airflow에서 공통으로 사용하는 인자들)
default_args = {
    'depends_on_past': False,  # 이전 작업의 성공 여부와 상관없이 실행
    'retries': 1,  # 실패 시 재시도 횟수
    'retry_delay': timedelta(minutes=5)  # 재시도 간격 (5분)
}


# DAG 정의 (Airflow에서 작업 흐름을 구성하는 단위)
with DAG(
    'fsc_csv',  # DAG 이름
    default_args=default_args,  # 기본 인자 설정
    description="입법예고/규정변경예고 데이터를 Elasticsearch에 저장합니다.",  # 설명
    schedule_interval='@monthly',  # DAG이 한 번만 실행되도록 설정
    start_date=datetime.now(),  # 현재 시점에서 실행
    catchup=False,  # 과거 날짜의 작업은 무시
    tags=['elasticsearch', 'crawl', 'finance']  # 태그 설정 (DAG 분류에 사용)
) as dag:

    # Elasticsearch 데이터 초기화 작업
    clear_data = PythonOperator(
        task_id="clear_raw_data_in_elasticsearch",  # 작업 ID
        python_callable=clear_elasticsearch_data,  # 실행할 함수
    )

    # Elasticsearch로 데이터 업로드 작업 정의
    upload_data = PythonOperator(
        task_id="csv_upload_raw_data_to_elasticsearch",  # 작업 ID
        python_callable=dataframe_to_elasticsearch_first,  # 실행할 함수
    )

    # 작업 순서 정의 (데이터 초기화 후 데이터 업로드)
    clear_data >> upload_data
