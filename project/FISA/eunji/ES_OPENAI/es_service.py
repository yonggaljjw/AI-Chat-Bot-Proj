import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Load environment variables from .env file
load_dotenv()

# Set ES properties
es_host_url = os.environ.get('ES_HOST_URL')
es_username = os.environ.get('ES_USERNAME')
es_password = os.environ.get('ES_PASSWORD')

# Initialize Elasticsearch with authentication
es = Elasticsearch(
    [es_host_url],
    http_auth=(es_username, es_password)
)


def index(index, id, body, hard_refresh=False):
    if hard_refresh:
        # Index the document
        es.index(index=index, id=id, body=body)
        print("hard indexed - ", id)
    else:
        indexed = already_indexed(id, index)
        if not indexed:
            # Index the document
            es.index(index=index, id=id, body=body)
            print("indexed - ", id)
        else:
            print("already indexed - ", id)


def already_indexed(id, index):
    # Define Elasticsearch script score query
    body = {
        "size": 1,
        "query": {
            "match": {
                "_id": id
            }
        }
    }

    # Execute the query
    res = es.search(index=index, body=body)
    if res['hits']['total']['value'] > 0:
        return True
    return False


def search_embedding(index, query_embedding, num_results=10):
    field_name="제목_vector"                 ################################### 검색 필드 설정
    try:
        # Define Elasticsearch script score query
        body = {
            "size": num_results,
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": f"cosineSimilarity(params.query_vector, '{field_name}') + 1.0", # 특정 임베딩 필드로 수정
                        "params": {
                            "query_vector": query_embedding
                        }
                    }
                }
            }
        }

        # Execute the query
        res = es.search(index=index, body=body)
        return res
    except Exception as e:
        print(f"Error executing search: {e}")
        return None

def search_embedding_plus_date(index, query_embedding, num_results=10, start_date=None, end_date=None):
    field_name = "제목_vector"  # 검색 필드 설정
    try:
        # Define Elasticsearch script score query with date range filter
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
                                "source": f"cosineSimilarity(params.query_vector, '{field_name}') + 1.0",  # 특정 임베딩 필드로 수정
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
                    "date": {  # 날짜 필드명은 실제 인덱스의 필드명으로 변경
                        "gte": start_date,
                        "lte": end_date
                    }
                }
            })

        # Execute the query
        res = es.search(index=index, body=body)
        return res
    except Exception as e:
        print(f"Error executing search: {e}")
        return None
