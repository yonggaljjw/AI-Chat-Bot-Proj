from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
import pandas as pd

from elasticsearch import Elasticsearch, helpers
# Elasticsearch 인스턴스 생성 (Docker 내부에서 실행 중인 호스트에 연결)
es = Elasticsearch("http://localhost:9200", timeout=30)  # 타임아웃을 30초로 늘림

model_dir = "C:/ITStudy/final_project/AI-Chat-Bot-Proj/eunji/sum_models/t5-large-korean-text-summary/"


# 로컬에 저장된 모델과 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)

# 입력 텍스트와 모델 최대 입력 길이 설정
max_input_length = 2048 + 128

# 검색 쿼리 정의
query = {
    "sort": [
        {"날짜": {"order": "desc"}}
    ],
    "size": 10,
    "_source": ["제목", "날짜", "개정이유", "주요내용","내용"]
}


response = es.search(index="raw_data", body=query)  # size 제거


# 검색 결과를 데이터프레임으로 변환
data = [
    {
        "제목": hit["_source"].get("제목"),
        "날짜": hit["_source"].get("날짜"),  # 날짜가 없을 경우 None 반환
        "개정이유": hit["_source"].get("개정이유"),
        "내용": hit["_source"].get("내용"),
        "주요내용": hit["_source"].get("주요내용")
    }
    for hit in response["hits"]["hits"]
]
df = pd.DataFrame(data)
# print(df["날짜"])
# print(df)
# print(df["주요내용"][0])

# # text = df["내용"][1]
# text = "주요내용 : " + df["주요내용"][1] + "\n 개정이유 : "+ df["개정이유"][1]
# print(text)

# # 토크나이저를 사용해 입력을 모델이 처리할 수 있는 형식으로 변환
# inputs = ["summarize: " + text]
# inputs = tokenizer(inputs, max_length=max_input_length, truncation=True, return_tensors="pt")

# # 요약 생성
# output = model.generate(**inputs, num_beams=8, do_sample=True, min_length=10, max_length=100)
# decoded_output = tokenizer.batch_decode(output, skip_special_tokens=True)[0]

# # 첫 문장만 추출하여 요약 제목으로 사용
# predicted_title = nltk.sent_tokenize(decoded_output.strip())[0]
# print("------------------------------")
# print(predicted_title)

for i in range(5):
    text = df["개정이유"][i] + "\n" + df["주요내용"][i]
    # 토크나이저를 사용해 입력을 모델이 처리할 수 있는 형식으로 변환
    inputs = ["summarize: " + text]
    inputs = tokenizer(inputs, max_length=max_input_length, truncation=True, return_tensors="pt")

    # 요약 생성
    output = model.generate(**inputs, num_beams=8, do_sample=True, min_length=10, max_length=100)
    decoded_output = tokenizer.batch_decode(output, skip_special_tokens=True)[0]

    # 첫 문장만 추출하여 요약 제목으로 사용
    predicted_title = nltk.sent_tokenize(decoded_output.strip())[0]
    print("------------------------------------------------------------")
    print("제목 : ", df["제목"][i]) 
    print("축약내용: " , predicted_title)
    print("원문 : \n", text)

    
