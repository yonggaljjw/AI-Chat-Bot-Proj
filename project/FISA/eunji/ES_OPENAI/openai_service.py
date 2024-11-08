import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI()
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
