from answering_service import *

def query():
    index_name = "raw_data"
    question = "전자금융감독규정 일부개정고시안 규정변경예고의 내용을 알려줘?"
    pre_msgs = None
    response_text = generate_answer(question, index_name, pre_msgs)

    return response_text

print(query())