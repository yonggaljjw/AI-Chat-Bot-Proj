import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import re

# .env 파일에서 환경 변수 로드
load_dotenv()

# 인증 정보를 사용하여 OpenSearch 클라이언트 생성
host = os.getenv("OPENSEARCH_HOST")
port = os.getenv("OPENSEARCH_PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False
)

def index(index, id, body, hard_refresh=False):
    """
    문서를 인덱스에 추가. 이미 인덱싱된 문서의 경우 hard_refresh 옵션으로 재인덱싱 가능.
    """
    if hard_refresh:
        # 문서 인덱싱
        client.indices(index=index, id=id, body=body)
        print("hard indexed - ", id)
    else:
        if not already_indexed(id, index):
            client.indices(index=index, id=id, body=body)
            print("indexed - ", id)
        else:
            print("already indexed - ", id)

def already_indexed(id, index):
    """
    문서가 이미 인덱스에 존재하는지 확인.
    """
    body = {
        "size": 1,
        "query": {
            "match": {
                "_id": id
            }
        }
    }

    # 검색 실행
    res = client.search(index=index, body=body)
    return res['hits']['total']['value'] > 0

def search_embedding(index, query_embedding, num_results=10):
    """
    주어진 임베딩에 가장 유사한 문서 검색.
    """
    field_name = "제목_vector"  # 검색할 임베딩 필드
    try:
        body = {
            "size": num_results,
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": f"cosineSimilarity(params.query_vector, '{field_name}') + 1.0",
                        "params": {
                            "query_vector": query_embedding
                        }
                    }
                }
            }
        }

        # 검색 실행
        res = client.search(index=index, body=body)
        return res
    except Exception as e:
        print(f"Error executing search: {e}")
        return None

def search_embedding_plus_date(index, query_embedding, num_results=10, start_date=None, end_date=None):
    """
    날짜 범위와 임베딩을 사용하여 문서 검색.
    """
    field_name = "제목_vector"  # 검색할 임베딩 필드
    try:
        body = {
            "size": num_results,
            "query": {
                "bool": {
                    "must": {
                        "script_score": {
                            "query": {
                                "match_all": {}
                            },
                            "script": {
                                "source": f"cosineSimilarity(params.query_vector, '{field_name}') + 1.0",
                                "params": {
                                    "query_vector": query_embedding
                                }
                            }
                        }
                    },
                    "filter": []
                }
            }
        }

        # 날짜 필터 추가
        if start_date and end_date:
            body["query"]["bool"]["filter"].append({
                "range": {
                    "date": {  # 실제 날짜 필드명으로 수정 필요
                        "gte": start_date,
                        "lte": end_date
                    }
                }
            })

        # 검색 실행
        res = client.search(index=index, body=body)
        return res
    except Exception as e:
        print(f"Error executing search: {e}")
        return None
