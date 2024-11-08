import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI()


# Elasticsearch 설정
es_host_url = os.environ.get('ES_HOST_URL')
es_username = os.environ.get('ES_USERNAME')
es_password = os.environ.get('ES_PASSWORD')

# 인증 정보를 사용하여 Elasticsearch 초기화
# es = Elasticsearch(
#     [es_host_url],
#     http_auth=(es_username, es_password), timeout=30
# )


es = Elasticsearch(
    hosts=[{"host": "192.168.0.101", "port": 9200}],  # IP 주소와 포트
    basic_auth=("user", "password")  # 사용자 인증 정보
)

###########################################################################################################
###################### main.py
import re
from datetime import datetime
# 질문에 날짜가 포함된 경우 해당 날짜로 필터링하여 답변 생성
def query_with_date(question):
    index_name = "raw_data"
    start_date = if_date(question)  # 질문에서 시작 날짜 추출
    end_date = if_date(question)  # 종료 날짜를 시작 날짜와 동일하게 설정 (단일 날짜)
    response_text = generate_answer_plus_date(question, index_name, pre_msgs=None, start_date=start_date, end_date=end_date)
    return response_text


###########################################################################################################
###################### es_service.py


def index(index, id, body, hard_refresh=False):
    """
    문서를 인덱스에 추가. 이미 인덱싱된 문서의 경우 hard_refresh 옵션으로 재인덱싱 가능.
    """
    if hard_refresh:
        # 문서 인덱싱
        es.index(index=index, id=id, body=body)
        print("hard indexed - ", id)
    else:
        if not already_indexed(id, index):
            es.index(index=index, id=id, body=body)
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
    res = es.search(index=index, body=body)
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
        res = es.search(index=index, body=body)
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
        res = es.search(index=index, body=body)
        return res
    except Exception as e:
        print(f"Error executing search: {e}")
        return None

###########################################################################################################
###################### openai_service.py

# 기본적으로 OPENAI_API_KEY 환경 변수에서 API 키를 가져옴
# 다른 환경 변수 이름을 사용하고 싶다면 다음과 같이 설정 가능:
# client = OpenAI(api_key=os.environ.get("CUSTOM_ENV_NAME"))

gpt_model = "gpt-4o-mini"
embedding_model = "text-embedding-3-small"

def generate_embedding(text):
    """
    주어진 텍스트에 대한 임베딩을 생성.
    """
    print("Generating embedding for text: " + text)
    # OpenAI 모델을 사용하여 임베딩 생성
    res = client.embeddings.create(input=text, model=embedding_model)
    embedding = res.data[0].embedding
    return embedding

def generate_chat_response(messages):
    """
    주어진 메시지 리스트를 바탕으로 ChatGPT 모델 응답을 생성.
    """
    parameters = {
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None,
        "model": gpt_model
    }

    # OpenAI API를 사용하여 채팅 응답 생성
    response = client.chat.completions.create(**parameters)

    # 불필요한 텍스트 제거
    response_text = response.choices[0].message.content
    response_text = response_text.replace("As an AI language model, ", "")
    response_text = response_text.replace("I am not capable of understanding emotions, but ", "")

    return response_text

###########################################################################################################
###################### anserwing_service.py
"""
이 파일은 사용자 질문에 대한 답변을 생성하는 주요 로직을 포함하고 있습니다.
generate_answer 함수는 질문, 인덱스, 이전 메시지 목록을 입력으로 받아 응답을 반환합니다.
이 함수는 먼저 OpenAI API를 사용하여 질문의 임베딩을 생성합니다.
그 후, Elasticsearch에서 지정된 인덱스 내 유사한 임베딩을 검색합니다.
가까운 유사 항목이 발견되면 일치하는 텍스트와 사용자 질문을 바탕으로 응답 메시지를 생성합니다.
가까운 유사 항목이 없을 경우, 사용자 질문만을 바탕으로 응답 메시지를 구성합니다.
"""


BEST_SCORE_THRESHOLD = 1.71  # 일치 항목으로 간주하기 위한 점수 임계값

def generate_answer(query, index=None, pre_msgs=None):
    """
    질문에 대해 가장 유사한 텍스트를 바탕으로 응답을 생성합니다.
    가까운 유사 항목이 없을 경우 질문만을 바탕으로 응답을 생성합니다.
    """
    if pre_msgs is None:
        pre_msgs = []

    matched_texts = ""
    best_score = 0

    # 인덱스가 지정된 경우 유사한 임베딩 검색 수행
    if index:
        query_embedding = generate_embedding(query)
        res = search_embedding(index, query_embedding, 10)
        if res:
            i = 0
            for hit in res['hits']['hits']:
                score = hit['_score']
                text0 = hit['_source'].get('제목') 
                text1 = hit['_source'].get('개정이유')  
                text2 = hit['_source'].get('주요내용')
                text = text0 + "\n" + text1 + text2

                # 임계값 이상의 점수를 가진 텍스트를 최대 5개까지 추가
                if score >= BEST_SCORE_THRESHOLD and len(text) > 30 and i < 5:
                    matched_texts += text + "\n"
                    i += 1
            best_score = res['hits']['hits'][0]['_score']
        else:
            print('유사 항목 없음')
    else:
        print("인덱스가 지정되지 않음")

    messages = []
    if best_score >= BEST_SCORE_THRESHOLD:  # 유사 항목이 있을 경우 일치하는 텍스트 포함
        if len(matched_texts) > 0:
            messages.append({
                "role": "system",
                "content": "기준 텍스트를 참고하여 아래의 사용자 질문에 한국어로 답변을 만드세요."
                           + "\n\n" + matched_texts
            })
    else:
        print('Generating response using OpenAI API without retrieval-augmented generation (RAG)')

    for pre_msg in pre_msgs:
        messages.append({"role": "user", "content": pre_msg})
    messages.append({"role": "user", "content": query})

    return generate_chat_response(messages)

def if_date(query):
    """
    질문에 날짜가 포함되어 있으면 추출하여 YYYY-MM-DD 형식으로 반환합니다.
    """
    date_match = re.search(r"(\d{4})년 (\d{1,2})월 (\d{1,2})일", query)
    if date_match:
        year, month, day = date_match.groups()
        query_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"  # 날짜 형식 변환
    else:
        query_date = None
    return query_date

def generate_answer_plus_date(query, index=None, pre_msgs=None, start_date=None, end_date=None):
    """
    날짜 필터링된 데이터를 바탕으로 질문에 대한 응답을 생성합니다.
    """
    if pre_msgs is None:
        pre_msgs = []

    matched_texts = ""
    best_score = 0

    # 인덱스가 지정된 경우 날짜 필터링을 적용하여 유사한 임베딩 검색
    if index:
        query_embedding = generate_embedding(query)
        res = search_embedding_plus_date(index, query_embedding, 10, start_date, end_date)
        
        # 검색 결과가 있을 때만 처리
        if res and 'hits' in res and 'hits' in res['hits'] and res['hits']['hits']:
            i = 0
            for hit in res['hits']['hits']:
                score = hit['_score']
                text0 = hit['_source'].get('제목') 
                text1 = hit['_source'].get('개정이유')  
                text2 = hit['_source'].get('주요내용')
                text = text0 + '\n' + text1 + text2

                # 임계값 이상의 점수를 가진 텍스트를 최대 5개까지 추가
                if score >= BEST_SCORE_THRESHOLD and len(text) > 30 and i < 5:
                    matched_texts += text + "\n"
                    i += 1
            best_score = res['hits']['hits'][0]['_score']
        else:
            print('유사 항목 없음')
    else:
        print("인덱스가 지정되지 않음")

    messages = []
    if best_score >= BEST_SCORE_THRESHOLD:  # 유사 항목이 있을 경우 일치하는 텍스트 포함
        if len(matched_texts) > 0:
            messages.append({
                "role": "system",
                "content": "Summarize the content below and answer the following question from the user in Korean."
                           + "\n\n" + matched_texts
            })
    
    for pre_msg in pre_msgs:
        messages.append({"role": "user", "content": pre_msg})
    messages.append({"role": "user", "content": query})

    return generate_chat_response(messages)