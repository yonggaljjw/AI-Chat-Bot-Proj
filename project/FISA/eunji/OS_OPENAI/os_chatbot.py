def search_embedding(query_embedding):
    """
    주어진 임베딩에 가장 유사한 문서 검색.
    """
    index = 'korean_law_data'
    num_results=10
    field_name = "embedding_vector"  # 검색할 임베딩 필드
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
    
def os_output_text(index, query_embedding):
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