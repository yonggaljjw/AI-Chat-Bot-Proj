"""
This file contains the main logic for generating an answer to a user query.
The generate_answer function takes in a query, an index, and a list of previous messages and returns a response.
The function first generates an embedding for the query using the OpenAI API.
It then searches for similar embeddings in the specified index using Elasticsearch.
If a close match is found, the function constructs a response message based on the matched text and the user query.
If no close match is found, the function constructs a response message based on the user query alone.
"""

from es_service import *
from openai_service import *

BEST_SCORE_THRESHOLD = 1.71  # Threshold for considering a match as close; Adjust as needed


def generate_answer(query, index=None, pre_msgs=None):
    # Generate embeddings for the query
    if pre_msgs is None:
        pre_msgs = []

    # Execute the query
    matched_texts = ""
    best_score = 0
    if index:
        query_embedding = generate_embedding(query)
        res = search_embedding(index, query_embedding, 10)
        if res:
            i = 0
            for hit in res['hits']['hits']:
                score = hit['_score']
                score = hit['_score']
                text0 = hit['_source'].get('제목') 
                text1 = hit['_source'].get('개정이유')   ########################################################### raw_data에 맞는 검색 필드
                text2 = hit['_source'].get('주요내용')
                text = text0 + "\n" + text1 + text2
                # print(score, text)
                if score >= BEST_SCORE_THRESHOLD and len(text) > 30 and i < 5:  # Close match found
                    matched_texts += text + "\n"
                    i += 1
            best_score = res['hits']['hits'][0]['_score']
        else:
            print('No close match found')
    else:
        print("No index provided")
        best_score = 0

    messages = []
    if best_score >= BEST_SCORE_THRESHOLD:  # Close match found
        if len(matched_texts) > 0:
            messages.append({
                "role": "system",
                "content": "Based on the text below, answer the following question asked by the user."
                           + "\n\n"
                           + matched_texts
            })
        for pre_msg in pre_msgs:
            messages.append({
                "role": "user",
                "content": pre_msg
            })
        messages.append({
            "role": "user",
            "content": query
        })
    else:
        print('No close match found or no index provided')
        print('Generating response using OpenAI API...without any RAG')
        for pre_msg in pre_msgs:
            messages.append({
                "role": "user",
                "content": pre_msg
            })
        messages.append({
            "role": "user",
            "content": query
        })

    return generate_chat_response(messages)


def generate_answer_plus_date(query, index=None, pre_msgs=None, start_date=None, end_date=None):
    # Generate embeddings for the query
    if pre_msgs is None:
        pre_msgs = []

    # Execute the query
    matched_texts = ""
    best_score = 0
    if index:
        query_embedding = generate_embedding(query)
        res = search_embedding_plus_date(index, query_embedding, 10, start_date=None, end_date=None)
        if res:
            i = 0
            for hit in res['hits']['hits']:
                score = hit['_score']
                text0 = hit['_source'].get('제목') 
                text1 = hit['_source'].get('개정이유')   ########################################################### raw_data에 맞는 검색 필드
                text2 = hit['_source'].get('주요내용')
                text = text0 + '\n' + text1 + text2
                # print(score, text)
                if score >= BEST_SCORE_THRESHOLD and len(text) > 30 and i < 5:  # Close match found
                    matched_texts += text + "\n"
                    i += 1
            best_score = res['hits']['hits'][0]['_score']
        else:
            print('No close match found')
    else:
        print("No index provided")
        best_score = 0

    messages = []
    if best_score >= BEST_SCORE_THRESHOLD:  # Close match found
        if len(matched_texts) > 0:
            messages.append({
                "role": "system",
                "content": "아래 내용을 요약하여 사용자가 묻는 다음 질문에 답하세요. "
                           + "\n\n"
                           + matched_texts
            })
            # print(messages)
        for pre_msg in pre_msgs:
            messages.append({
                "role": "user",
                "content": pre_msg
            })
        messages.append({
            "role": "user",
            "content": query
        })
    else:
        print('No close match found or no index provided')
        print('Generating response using OpenAI API...without any RAG')
        for pre_msg in pre_msgs:
            messages.append({
                "role": "user",
                "content": pre_msg
            })
        messages.append({
            "role": "user",
            "content": query
        })
    print(messages)
    return generate_chat_response(messages)
