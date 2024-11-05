import re
import pandas as pd


# 주요 내용 추출
def extract_main_content(text):
    # 주요 내용 추출 정규식 패턴 (3번 항목 유무에 따른 처리)
    pattern_with_opinion = r"2\.\s*주요\s*내용\s*(.*?)\s*3\.\s*의견제출"
    pattern_to_end = r"2\.\s*주요\s*내용\s*(.*?)\s*3\."  # 문서 끝까지 추출하는 패턴

    # 3번 항목이 있는 경우
    match = re.search(pattern_with_opinion, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 3번 항목이 없을 경우
    match = re.search(pattern_to_end, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 주요 내용이 없을 경우
    return "주요내용을 찾을 수 없습니다."

def extract_reason(text):
    # 다양한 이유 패턴 정의
    patterns = [
        r"1\.\s*개정\s*이유\s*(.*?)\s*2\.",
        r"1\.\s*제정\s*이유\s*(.*?)\s*2\.",
        r"1\.\s*개정\s*이유\s*및\s*주요내용\s*(.*?)\s*2\.",
        r"1\.\s*제정\s*이유\s*및\s*주요내용\s*(.*?)\s*2\.",
        r"1\.\s*개정\s*이유\s*(.*?)\s*2\.",
        r"1\.\s*제정\s*이유\s*(.*?)\s*2\."
    ]

    # 각 패턴을 순회하며 매칭 시도
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()  # 매칭된 이유 내용 반환

    # 이유 패턴이 없는 경우
    return "개정이유를 찾을 수 없습니다."