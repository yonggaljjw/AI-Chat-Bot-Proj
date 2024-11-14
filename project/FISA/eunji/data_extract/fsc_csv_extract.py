import re
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk

# 주요 내용 추출 함수
def extract_main_content(text):
    """
    '주요 내용' 부분을 추출하는 함수
    3번 항목 유무에 따라 정규식을 사용하여 주요 내용을 찾는다.
    """
    pattern_with_opinion = r"2\.\s*주요\s*내용\s*(.*?)\s*3\.\s*의견제출"
    pattern_to_end = r"2\.\s*주요\s*내용\s*(.*?)\s*3\."

    # 3번 항목이 있는 경우 추출
    match = re.search(pattern_with_opinion, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 3번 항목이 없는 경우 추출
    match = re.search(pattern_to_end, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 주요 내용이 없을 경우 메시지 반환
    return "주요내용을 찾을 수 없습니다."


# 개정 이유 추출 함수
def extract_reason(text):
    """
    '개정 이유' 또는 '제정 이유' 부분을 추출하는 함수
    다양한 패턴에 따라 매칭하여 이유를 추출한다.
    """
    patterns = [
        r"1\.\s*개정\s*이유\s*(.*?)\s*2\.",
        r"1\.\s*제정\s*이유\s*(.*?)\s*2\.",
        r"1\.\s*개정\s*이유\s*및\s*주요내용\s*(.*?)\s*2\.",
        r"1\.\s*제정\s*이유\s*및\s*주요내용\s*(.*?)\s*2\."
    ]

    # 각 패턴을 순회하며 매칭 시도
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()  # 매칭된 이유 내용 반환

    # 이유 패턴이 없는 경우 메시지 반환
    return "개정이유를 찾을 수 없습니다."


# 데이터 전처리 함수
def preprocess_data(file_path):
    """
    CSV 파일에서 데이터를 로드하고, 결측치 처리 및 주요 내용과 개정 이유 추출
    """
    df = pd.read_csv(file_path)
    df['content'] = df['content'].fillna('')  # 결측치를 빈 문자열로 대체
    df['revision_reason'] = df['content'].apply(extract_reason)
    df['main_content'] = df['content'].apply(extract_main_content)
    return df


# 요약 생성 함수
def generate_summary(df, tokenizer, model, max_input_length=512):
    """
    모델을 사용하여 'main_content'와 'revision_reason'을 결합한 요약을 생성
    """
    summaries = []  # 결과를 저장할 리스트 초기화

    # 각 행에 대해 요약 생성
    for _, row in df.iterrows():
        combined_input = f"{row['main_content']} {row['revision_reason']}"
        inputs = tokenizer(combined_input, max_length=max_input_length, truncation=True, return_tensors="pt")
        
        # 요약 생성
        output = model.generate(**inputs, num_beams=8, do_sample=True, min_length=10, max_length=100)
        decoded_output = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
        
        # 첫 문장만 추출하여 요약 제목으로 사용
        predicted_title = nltk.sent_tokenize(decoded_output.strip())[0]
        summaries.append(predicted_title)
        print("성공")

    df['summary'] = summaries  # 요약 결과를 데이터프레임에 추가
    return df


# 최종 CSV 저장 함수
def save_to_csv(df, output_file):
    """
    데이터프레임을 CSV 파일로 저장하는 함수
    """
    df.to_csv(output_file, index=False, encoding='utf-8')
    print("파일 저장 완료:", output_file)


# 실행 함수 (전체 코드 실행 흐름 관리)
def main():
    input_file = "./fsc_announcements.csv"
    model_directory = "./t5-large-korean-text-summary/"
    output_file = "fsc_announcements_summary.csv"
    tokenizer = AutoTokenizer.from_pretrained(model_directory)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_directory)

    # 데이터 전처리
    df = preprocess_data(input_file)
    
    # 요약 생성
    df = generate_summary(df, tokenizer, model)
    
    # 결과 저장
    save_to_csv(df, output_file)


# 메인 함수 실행
if __name__ == "__main__":
    main()
