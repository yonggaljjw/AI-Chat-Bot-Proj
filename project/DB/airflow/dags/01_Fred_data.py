import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, helpers
import opensearch_py_ml as oml
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import openai
from datetime import datetime, timedelta
import pandas as pd
from fredapi import Fred
from package.vector_embedding import generate_embedding

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.
FRED_API_KEY = os.getenv('FRED_API_KEY')

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)


fred = Fred(api_key=FRED_API_KEY)

# 현재 날짜를 end_date로 사용
end_date = datetime.today()

# 데이터 가져오기 함수
def fetch_data(series_id, start_date='2015-01-01', end_date=end_date):
    try:
        data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
        return data
    except ValueError as e:
        print(f"Error fetching data for {series_id}: {e}")
        return None

# 데이터프레임 생성 함수
def make_df():
    data_frames = {
        'FFTR': fetch_data('DFEDTARU'),
        'GDP': fetch_data('GDP'),
        'GDP Growth Rate': fetch_data('A191RL1Q225SBEA'),
        'PCE': fetch_data('PCE'),
        'Core PCE': fetch_data('PCEPILFE'),
        'CPI': fetch_data('CPIAUCSL'),
        'Core CPI': fetch_data('CPILFESL'),
        'Personal Income': fetch_data('PI'),
        'Unemployment Rate': fetch_data('UNRATE'),
        'ISM Manufacturing': fetch_data('MANEMP'),
        'Durable Goods Orders': fetch_data('DGORDER'),
        'Building Permits': fetch_data('PERMIT'),
        'Retail Sales': fetch_data('RSAFS'),
        'Consumer Sentiment': fetch_data('UMCSENT'),
        'Nonfarm Payrolls': fetch_data('PAYEMS'),
        'JOLTS Hires': fetch_data('JTSHIL')
    }

    df = pd.DataFrame()
    for key, value in data_frames.items():
        if value is not None:
            temp_df = value.reset_index()
            temp_df.columns = ['date', key]
            if df.empty:
                df = temp_df
            else:
                df = pd.merge(df, temp_df, on='date', how='outer')
    
    df.sort_values(by='date', inplace=True)
    df.fillna(method='ffill', inplace=True)

    df['description'] = df.apply(lambda row: 
    f"""
    Date: {row['date']}, FFTR: {row['FFTR']}, GDP: {row['GDP']}, 
    GDP Growth Rate: {row['GDP Growth Rate']}, PCE: {row['PCE']}, 
    Core PCE: {row['Core PCE']}, CPI: {row['CPI']}, Core CPI: {row['Core CPI']}, 
    Personal Income: {row['Personal Income']}, Unemployment Rate: {row['Unemployment Rate']}, 
    ISM Manufacturing: {row['ISM Manufacturing']}, Durable Goods Orders: {row['Durable Goods Orders']}, 
    Building Permits: {row['Building Permits']}, Retail Sales: {row['Retail Sales']}, 
    Consumer Sentiment: {row['Consumer Sentiment']}, Nonfarm Payrolls: {row['Nonfarm Payrolls']}, 
    JOLTS Hires: {row['JOLTS Hires']}
    """, axis=1)

    df['embedding_vector'] = df['description'].apply(generate_embedding)
    return df

# 인덱싱 하기
def create_index_and_mapping():
    index_body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                'date': {'type': 'date'},
                'embedding_vector': {
                    'type': 'knn_vector',
                    'dimension': 1536,
                },
                'FFTR': {'type': 'float'},
                'GDP': {'type': 'float'},
                'GDP Growth Rate': {'type': 'float'},
                'PCE': {'type': 'float'},
                'Core PCE': {'type': 'float'},
                'CPI': {'type': 'float'},
                'Core CPI': {'type': 'float'},
                'Personal Income': {'type': 'float'},
                'Unemployment Rate': {'type': 'float'},
                'ISM Manufacturing': {'type': 'float'},
                'Durable Goods Orders': {'type': 'float'},
                'Building Permits': {'type': 'float'},
                'Retail Sales': {'type': 'float'},
                'Consumer Sentiment': {'type': 'float'},
                'Nonfarm Payrolls': {'type': 'float'},
                'JOLTS Hires': {'type': 'float'}
            }
        }
    }

    if not client.indices.exists(index='fred_data'):
        client.indices.create(index='fred_data', body=index_body)
        print("새로운 인덱스 생성 완료")
    else :
        print("기존 인덱스가 존재합니다.")



## 데이터 적재를 위한 bulk_action 함수 생성
def create_bulk_actions(df, index_name):
    actions = []
    for num, (index, row) in enumerate(df.iterrows()):
        # Index action
        action = {
            "_index": index_name,
            "_source": row.to_dict()
        }
        actions.append(action)
    return actions


# Bulk API를 위한 작업 생성
def bulk_insert() :
    actions = create_bulk_actions(make_df(), 'fred_data')
    # Bulk API 호출
    if actions:
        # helpers.bulk(es, actions)
        helpers.bulk(client, actions)
        print(f"{len(actions)}개의 문서가 OpenSearch에 업로드되었습니다.")
    else:
        print("업로드할 문서가 없습니다.")



# Airflow DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    '01_Fred_Data',
    default_args=default_args,
    description="미 연준 데이터를 업로드 합니다.",
    schedule_interval='@daily',
    start_date=datetime(2015, 1, 1),
    catchup=False,
    tags=['Opensearch', 'fred', 'data']
) as dag :
    t1 = PythonOperator(
        task_id='create_index_and_mapping',
        python_callable=create_index_and_mapping
    )

    t2 = PythonOperator(
        task_id='bulk_insert',
        python_callable=bulk_insert,
    )
    
    t1 >> t2