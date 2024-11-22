import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from plotly.io import to_html
from deep_translator import GoogleTranslator
import plotly.express as px
from django.conf import settings

from opensearchpy import OpenSearch
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("OPENSEARCH_HOST")
port = os.getenv("OPENSEARCH_PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}]
)


def korean_law_view():
    # 현재 시간 가져오기
    current_time = datetime.utcnow().isoformat()

    # OpenSearch 쿼리 정의
    query = {
        "size": 30,  # 최신 10개 데이터
        "sort": [
            {"start_date": {"order": "desc"}}  # 최신순 정렬
        ],
        "query": {
            "bool": {
                "must": [
                    {"range": {"start_date": {"lte": current_time}}},  # start_date <= 현재 시간
                    {"range": {"end_date": {"gte": current_time}}}  # end_date >= 현재 시간
                ]
            }
        }
    }

    # 데이터 검색
    response = client.search(
        index='korean_law_data',
        body=query
    )

    # 결과 처리
    results = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        results.append({
            "start_date": source.get("start_date"),
            "end_date": source.get("end_date"),
            "title": source.get("title"),
            "summary": source.get("summary"),
        })

    return results