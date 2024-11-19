import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import opensearch_py_ml as oml
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import openai

load_dotenv()
gpt_model = "gpt-4o-mini"
embedding_model = "text-embedding-3-small"
openai.api_key = os.getenv('OPENAI_API_KEY')

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}]
)

def generate_embedding(data):
    text = "```" + str(data).replace("\n", "") + "```"
    res = openai.embeddings.create(input=[text], model=embedding_model)
    embedding = res.data[0].embedding
    return embedding


# Get All indices of the cluster, excepts starts with .
indices = [key for key in client.indices.get_alias("*").keys() if not key.startswith(".")]

def add_embeddings_to_index(index):
    fields = client.indices.get(index)
    index_name = index
    # index 이름과 필드 내용으로 메타데이터를 생성합니다.
    metadata = "This is a metadata for " + index_name + " index. It contains the following fields: " + str(fields)
    # 메타데이터로 임베딩을 생성합니다.
    
    for doc in documents:
        doc_id = doc['_id']
        data = doc['_source']  
        embedding = openai.embeddings.create(input=[metadata], model=embedding_model).data[0].embedding

        update_body = {
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1536
                    }
                }
            },
            "settings": {
                "index": {
                "knn.space_type": "cosinesimil",
                "knn": "true"
                }
            }
        }

        client.update(index=index_name, id=doc_id, body=update_body)

# Airflow DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

# Airflow DAG 정의
with DAG(
    '00.Embedding',
    default_args=default_args,
    description='Add embeddings to OpenSearch index',
    schedule_interval='@daily',
) as dag:
    
    for index in indices:
        if index[0] != ".":
            add_embeddings_task = PythonOperator(
                task_id='add_embeddings_' + index,
                python_callable=add_embeddings_to_index,
                op_args=[index],
            )

        add_embeddings_task