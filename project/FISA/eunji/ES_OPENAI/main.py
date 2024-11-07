from answering_service import *
import re
from datetime import datetime

def if_date(query):
    ###### 만약 데이터 정보가 있다면 다음 코드를 사용해야 함...
    # 날짜 추출 (예: 2024년 10월 28일을 추출하고 날짜 형식으로 변환)
    date_match = re.search(r"(\d{4})년 (\d{1,2})월 (\d{1,2})일", query)
    if date_match:
        year, month, day = date_match.groups()
        query_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"  # 날짜를 YYYY-MM-DD 형식으로 변환
    else:
        query_date = None

    # 내용 추출 (날짜 부분 제거)
    # query_content = re.sub(r"\d{4}년 \d{1,2}월 \d{1,2}일의 ", "", query).replace("에 대해 알려줘.", "")
    return query_date


# 단순하게 질문에 대한 답변
def query(question):
    index_name = "raw_data"
    pre_msgs = None
    response_text = generate_answer(question, index_name, pre_msgs)
    return response_text


# 질문에 날짜와 관련된 내용있으면 날짜로 필터링한 데이터를 이용하여 답변
def query2(question):
    index_name = "raw_data"
    pre_msgs = None
    start_date=if_date(question) ### 일단 날짜 하루만 
    end_date=if_date(question)
    response_text = generate_answer_plus_date(question, index_name, pre_msgs, start_date, end_date)
    return response_text


question = "2024년 10월 28일 전자금융감독규정 일부개정고시안 규정변경예고에 관하여 알려줘"

print(query2(question))
# 결과가 그냥 내용을 출력하는 형식임