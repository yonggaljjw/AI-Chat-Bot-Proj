from elasticsearch import Elasticsearch
import json

# Elasticsearch 연결
es = Elasticsearch(['http://localhost:9200'])

# JSON 파일 읽기
with open('topic_modeling_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 데이터 인덱싱
for topic_id, topic in data['topics'].items():
    doc = {
        'topic_id': topic_id,
        'topic_words': topic['words'],  # 토픽의 단어 리스트
        'topic_links': topic['links']   # 링크 추가
    }
    es.index(index='topic_modeling', id=topic_id, document=doc)

# top_words 인덱싱
for i, (word, count) in enumerate(data['top_words']):
    doc = {
        'word': word,
        'count': count
    }
    es.index(index='top_words', id=str(i), document=doc)
