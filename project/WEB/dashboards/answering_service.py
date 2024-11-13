"""
이 파일은 사용자 질문에 대한 답변을 생성하는 주요 로직을 포함하고 있습니다.
generate_answer 함수는 질문, 인덱스, 이전 메시지 목록을 입력으로 받아 응답을 반환합니다.
이 함수는 먼저 OpenAI API를 사용하여 질문의 임베딩을 생성합니다.
그 후, Elasticsearch에서 지정된 인덱스 내 유사한 임베딩을 검색합니다.
가까운 유사 항목이 발견되면 일치하는 텍스트와 사용자 질문을 바탕으로 응답 메시지를 생성합니다.
가까운 유사 항목이 없을 경우, 사용자 질문만을 바탕으로 응답 메시지를 구성합니다.
"""
from dashboards.es_service import *
from dashboards.openai_service import *

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