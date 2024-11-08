from answering_service import *
import re
from datetime import datetime


# 질문에 날짜가 포함된 경우 해당 날짜로 필터링하여 답변 생성
def query_with_date(question):
    index_name = "raw_data"
    start_date = if_date(question)  # 질문에서 시작 날짜 추출
    end_date = if_date(question)  # 종료 날짜를 시작 날짜와 동일하게 설정 (단일 날짜)
    response_text = generate_answer_plus_date(question, index_name, pre_msgs=None, start_date=start_date, end_date=end_date)
    return response_text

# # 테스트 질문 예제
# question = "2024년 10월 28일 전자금융감독규정 일부개정고시안 규정변경예고에 관하여 알려줘"
# print(query_with_date(question))  # 결과는 단순 내용을 출력하는 형식
