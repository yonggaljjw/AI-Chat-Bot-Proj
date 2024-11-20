from datetime import datetime, timedelta
import json
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine

# 환경 변수 로드
load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")

DATA_FILE_PATH = "./dags/package/CI_OVSEA_TOUR_AREA_INTRST_DGREE_INFO_20240930.json"
TABLE_NAME = "tour_area_intrst_20240930"

# MySQL 테이블을 생성 또는 갱신하는 함수 정의
def create_or_update_table():
    # 테이블 생성 쿼리
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        RESPOND_ID VARCHAR(255),
        EXAMIN_BEGIN_DE DATE,
        SEXDSTN_FLAG_CD VARCHAR(255),
        AGRDE_FLAG_NM VARCHAR(255),
        ANSWRR_OC_AREA_NM VARCHAR(255),
        HSHLD_INCOME_DGREE_NM VARCHAR(255),
        CHINA_TOUR_INTRST_VALUE VARCHAR(255),
        JP_TOUR_INTRST_VALUE VARCHAR(255),
        HONGKONG_MACAU_TOUR_INTRST_VALUE VARCHAR(255),
        SEASIA_TOUR_INTRST_VALUE VARCHAR(255),
        MDLEST_SWASIA_TOUR_INTRST_VALUE VARCHAR(255),
        USA_CANADA_TOUR_INTRST_VALUE VARCHAR(255),
        SAMRC_LAMRC_TOUR_INTRST_VALUE VARCHAR(255),
        WEURP_NEURP_TOUR_INTRST_VALUE VARCHAR(255),
        EEURP_TOUR_INTRST_VALUE VARCHAR(255),
        SEURP_TOUR_INTRST_VALUE VARCHAR(255),
        SPCPC_TOUR_INTRST_VALUE VARCHAR(255),
        AFRICA_TOUR_INTRST_VALUE VARCHAR(255)
    );
    """
    
    with engine.connect() as connection:
        connection.execute(create_table_query)
        print(f"테이블 '{TABLE_NAME}' 생성 또는 갱신 완료")

# MySQL에 데이터를 업로드하는 함수 정의
def upload_to_mysql():
    # JSON 파일에서 데이터 읽기
    with open(DATA_FILE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 데이터프레임으로 변환
    df = pd.DataFrame(data)

    # 데이터프레임을 MySQL에 업로드
    df.to_sql(TABLE_NAME, con=engine, if_exists='replace', index=False)
    print(f"{len(df)}개의 데이터가 테이블 '{TABLE_NAME}'에 업로드되었습니다.")

# 기본 인자를 설정하여 Airflow DAG 정의
default_args = {
    'depends_on_past': False,  # 이전 작업의 성공 여부에 관계없이 실행
    'retries': 1,  # 실패 시 재시도 횟수
    'retry_delay': timedelta(minutes=5)  # 재시도 간격 (5분)
}

# DAG 정의
with DAG(
    '06_TOUR_INTRST',  # DAG 이름
    default_args=default_args,  # 기본 인자 설정
    description="관광 관심 데이터를 MySQL에 업로드하는 DAG",  # 설명
    schedule_interval=None,  # 수동 실행
    start_date=datetime.now(),  # 현재 시점에서 실행
    catchup=False,  # 과거 날짜의 작업은 무시
    tags=['mysql', 'tour', 'data_upload']  # 태그 설정 (DAG 분류에 사용)
) as dag:

    # MySQL 테이블 생성 또는 초기화 작업
    clear_data = PythonOperator(
        task_id="create_or_update_table",  # 작업 ID
        python_callable=create_or_update_table,  # 실행할 함수
    )

    # 데이터를 MySQL에 업로드하는 작업 정의
    upload_data = PythonOperator(
        task_id="upload_data",  # 작업 ID
        python_callable=upload_to_mysql,  # 실행할 함수
    )

    # 작업 순서 정의 (테이블 생성 후 데이터 업로드)
    clear_data >> upload_data
