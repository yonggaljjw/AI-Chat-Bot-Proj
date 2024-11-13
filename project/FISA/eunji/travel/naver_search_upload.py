import os
import json
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)

# 인덱스 이름
index_name = "naver_travel"

# 인덱스가 없는 경우 생성하고 매핑 설정
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

# JSON 파일이 저장된 폴더 경로
folder_path = "naver_country"

# JSON 파일을 읽어 문서 생성
def load_json_data(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                documents.append({
                    "_index": index_name,
                    "_source": data
                })
    return documents

# 문서를 일괄 업로드
documents = load_json_data(folder_path)
if documents:
    helpers.bulk(client, documents)
    print(f"Uploaded {len(documents)} documents to index '{index_name}'.")
else:
    print("No JSON files found to upload.")
