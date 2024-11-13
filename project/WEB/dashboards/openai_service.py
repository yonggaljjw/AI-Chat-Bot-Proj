import os
import openai
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

gpt_model = "gpt-4o-mini"
embedding_model = "text-embedding-3-small"

def generate_embedding(text):
    """
    주어진 텍스트에 대한 임베딩을 생성.
    """
    print("Generating embedding for text: " + text)
    # OpenAI 모델을 사용하여 임베딩 생성
    res = openai.Embedding.create(input=text, model=embedding_model)
    embedding = res['data'][0]['embedding']
    return embedding

def generate_chat_response(messages):
    """
    주어진 메시지 리스트를 바탕으로 ChatGPT 모델 응답을 생성.
    """
    parameters = {
        "model": gpt_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None
    }

    # OpenAI API를 사용하여 채팅 응답 생성
    response = openai.ChatCompletion.create(**parameters)

    # 불필요한 텍스트 제거
    response_text = response['choices'][0]['message']['content']
    response_text = response_text.replace("As an AI language model, ", "")
    response_text = response_text.replace("I am not capable of understanding emotions, but ", "")

    return response_text
