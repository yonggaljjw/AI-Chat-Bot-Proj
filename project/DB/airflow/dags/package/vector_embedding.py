import openai

from dotenv import load_dotenv
import os

load_dotenv()
# OpenAI API 키 설정

openai.api_key = os.getenv('OPENAI_API_KEY')

gpt_model = "gpt-4o-mini"
embedding_model = "text-embedding-3-small"

def generate_embedding(text):
    if not text :
        return None
    text = str(text).replace("\n", "")
    res = openai.embeddings.create(input=[text], model=embedding_model)
    embedding = res.data[0].embedding
    return embedding