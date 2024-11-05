
from elasticsearch import Elasticsearch
import pandas as pd

# Elasticsearch에서 특정 지표 데이터를 가져오는 함수
def fetch_data_from_elasticsearch(index_name='fred_data', fields=['FFTR', 'GDP Growth Rate', 'Unemployment Rate']):
    es = Elasticsearch('http://host.docker.internal:9200')
    query = {
        "query": {
            "match_all": {}
        }
    }
    
    result = es.search(index=index_name, body=query, size=10000)
    
    # Elasticsearch에서 가져온 결과를 DataFrame으로 변환
    hits = result['hits']['hits']
    data = [hit['_source'] for hit in hits]
    df = pd.DataFrame(data)
    
    # 필요한 지표만 선택
    df = df[['date'] + fields]
    df['date'] = pd.to_datetime(df['date'])
    return df
