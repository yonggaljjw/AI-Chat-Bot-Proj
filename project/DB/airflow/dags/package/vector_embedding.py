from openai import OpenAI
import os


# OpenAI API 키 설정
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

gpt_model = "gpt-4o-mini"
embedding_model = "text-embedding-ada-002"

def generate_embedding(text):
    text = str(text).replace("\n", "")
    res = client.embeddings.create(input=[text], model=embedding_model)
    embedding = res.data[0].embedding
    return embedding

