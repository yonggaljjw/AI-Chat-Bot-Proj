from elasticsearch import Elasticsearch
import json

# Elasticsearch 연결
es = Elasticsearch(['http://localhost:9200'])

# JSON 파일 읽기
with open('topic_modeling_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 데이터 인덱싱
for i, topic in enumerate(data['topics']):
    doc = {
        'topic_id': i,
        'topic_words': topic[1]
    }
    es.index(index='topic_modeling', id=str(i), document=doc)

# top_words 인덱싱
for i, (word, count) in enumerate(data['top_words']):
    doc = {
        'word': word,
        'count': count
    }
    es.index(index='top_words', id=str(i), document=doc)