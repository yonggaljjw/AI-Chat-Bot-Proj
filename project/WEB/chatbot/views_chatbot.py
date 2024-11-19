from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from sqlalchemy import create_engine
import pymysql
import pandas as pd
from openai import OpenAI

import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('sql_username')
password = os.getenv('sql_password')
host = os.getenv('sql_host')
port = os.getenv('sql_port')
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/team5")


def execute_query_to_dataframe(query):
    try:
        # pandas의 read_sql 함수를 사용하여 쿼리 실행 및 DataFrame 생성
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

# 쿼리 정의
query = """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, TABLE_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'team5'
"""

# 쿼리 실행 및 DataFrame 생성
result_df = execute_query_to_dataframe(query)

# 연결 종료
engine.dispose()

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text):
    if not text:
        return None
    text = str(text).replace("\n", "")
    res = openai.embeddings.create(input=[text], model="text-embedding-3-small")
    embedding = res.data[0].embedding
    return embedding

def generate_query(query):
    # 필드 정보 추출
    table_info = result_df.groupby('TABLE_NAME').apply(
        lambda x: ", ".join(x['COLUMN_NAME'] + " (" + x['DATA_TYPE'] + ", 결측값: " + x['IS_NULLABLE'] + ")")
    ).to_dict()

    # 테이블 정보 포맷팅
    table_info_str = "\n".join([f"{table}: {columns}" for table, columns in table_info.items()])

    # 프롬프트 생성
    prompt = f"The database has the following tables and fields:\n{table_info_str}\nWrite an only MySQL query for the following question: {query}"

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an excellent MySQL query creator, Only Provide MySQL Query"},
            {"role": "user", "content": prompt}
        ]
    )
    
    generated_query = response.choices[0].message.content
    generated_query = generated_query.replace("```sql","").replace("```","").strip()
    return generated_query

def answer_question(query):
    # Search for relevant documents
    search_query = generate_query(query)
    relevant_docs = execute_query_to_dataframe(search_query)

    # Generate answer using OpenAI GPT model
    prompt = f"""
    
    The following is a table of data extracted from an OpenSearch query:\n\n{relevant_docs}\n\n
    Based on this data, provide an effective and detailed answer to the following natural language query: {query}"
    
    
    Please follow these guidelines when answering:
    1. Provide accurate and concise answers based on the data.
    2. Only mention data relevant to the question.
    3. If information is not available in the data, state that it's not available rather than speculating
    4. Write your answer in Korean an-d keep it under 800 characters.
    
    Answer: """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Using the latest model
        messages=[
            {"role": "system", "content": "Your name is 우대리, You are an excellent assistant proficient in data analysis"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800  # Limiting answer length
    )
    return response.choices[0].message.content


@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        # 여기에 실제 챗봇 로직 구현
        # 임시 응답
        bot_response = f"우대리: {answer_question(user_message)}"
        
        return JsonResponse({
            'status': 'success',
            'response': bot_response
        })
    return JsonResponse({'status': 'error'}, status=400)
