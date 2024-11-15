from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import re
import os

# LangChain 모델 설정
llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

prompt_template = PromptTemplate(
    input_variables=["html_content"],
    template="""
    Given the HTML content of a credit card detail page, please extract the following details:
    - Title of the card
    - Benefits provided by the card
    - Fees associated with the card

    HTML content: {html_content}
    """
)

# RunnableSequence로 프롬프트와 LLM을 연결
llm_chain = prompt_template | llm

# Selenium 설정
s = Service('C:/chromedriver-win64/chromedriver.exe')
driver = webdriver.Chrome(service=s)

# 카테고리와 키워드 매핑
categories = {
    "통신": ["통신", "전화", "휴대폰", "통신비", "요금제", "LTE", "5G"],
    "주유+차량정비": ["주유", "차량", "자동차", "정비", "세차", "주유소", "카센터", "차량정비"],
    "쇼핑": ["쇼핑", "백화점", "적립", "패션", "의류", "아울렛", "온라인쇼핑", "마켓", "상점", "스토어"],
    "항공마일리지": ["항공", "마일리지", "항공사", "적립", "포인트", "마일", "Mileage"],
    "공항라운지": ["공항", "라운지", "출국", "입국", "공항서비스", "Lounge"],
    "무실적+모든가맹점": ["모든 가맹점", "무실적", "제한없음", "조건없음", "No Limit", "All Stores"],
    "구독/스트리밍": ["구독", "스트리밍", "OTT", "넷플릭스", "유튜브", "음악", "멤버십", "Subscription", "Streaming"],
    "해외결제": ["해외", "결제", "외화", "달러", "유로", "국제결제", "FX", "USD", "EUR"],
    "배달앱+간편결제": ["배달", "앱", "간편결제", "배달의민족", "요기요", "페이", "전자결제", "Delivery", "Pay", "결제앱"],
    "교통+편의점": ["교통", "편의점", "버스", "지하철", "택시", "대중교통", "교통카드", "편의", "Transit"],
    "공과금": ["공과금", "세금", "수도", "전기", "가스", "요금", "세금납부"],
    "여행+바우처": ["여행", "호텔", "바우처", "숙박", "여행사", "관광", "투어", "Voucher"],
    "제휴/PLCC": ["제휴", "PLCC", "특화", "스타벅스", "파트너십", "제휴카드", "쿠팡", "배민", "이케아", "네이버", "아모레", "카카오뱅크", "무신사", "쏘카", "코스트코", "이마트", "SSG", "현대차", "기아차", "제네시스", "스마일카드", "위버스", "컬리", "크림", "이디야", "야놀자", "미래에셋"],
    "증권사CMA": ["증권사", "CMA", "금융", "자산관리", "증권", "Investment"],
    "레스토랑/음식": ["패밀리레스토랑", "식당", "레스토랑", "푸드", "외식", "레스토랑할인", "Dining", "Restaurant"],
    "놀이공원": ["놀이공원", "테마파크", "어드벤처", "놀이시설", "레저", "어트랙션", "Amusement Park", "Park"],
    "기타": ["기타", "Miscellaneous", "기타혜택", "기타서비스", "Other", "Extra"]
}

# 각 혜택에 대해 카테고리 지정
def categorize_benefits(benefits):
    assigned_categories = []
    for category, keywords in categories.items():
        if any(keyword in benefits for keyword in keywords):
            assigned_categories.append(category)
    return assigned_categories

# 데이터 저장을 위한 빈 리스트 생성
data = []

# 페이지 ID 범위 설정
for page_id in range(0, 20):  # 테스트 범위 설정
    try:
        url = f"https://www.card-gorilla.com/card/detail/{page_id}"
        driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기

        # HTML 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 필요한 정보 추출
        title = soup.select_one('h1').text if soup.select_one('h1') else "N/A"
        benefits = soup.select_one('.benefits-class').text if soup.select_one('.benefits-class') else "N/A"
        fees = soup.select_one('.fees-class').text if soup.select_one('.fees-class') else "N/A"

        # 필요한 정보만 LangChain에 전달
        html_content = f"""
        Title: {title}
        Benefits: {benefits}
        Fees: {fees}
        """

        # LangChain을 통해 정보 추출
        response = llm_chain.invoke({"html_content": html_content})
        
        # LangChain 응답을 문자열로 받아온 후 정규표현식을 사용해 필요한 정보 추출
        extracted_title = re.search(r"Title:\s*(.*)", response)
        extracted_benefits = re.search(r"Benefits:\s*(.*)", response)
        extracted_fees = re.search(r"Fees:\s*(.*)", response)

        title = extracted_title.group(1) if extracted_title else "N/A"
        benefits = extracted_benefits.group(1) if extracted_benefits else "N/A"
        fees = extracted_fees.group(1) if extracted_fees else "N/A"
        
        # 혜택을 카테고리화
        benefit_categories = categorize_benefits(benefits)

        # 데이터 리스트에 추가
        data.append({
            "page_id": page_id,
            "title": title,
            "benefits": benefits,
            "fees": fees,
            "benefit_categories": benefit_categories
        })

    except NoSuchElementException:
        print(f"Page ID {page_id} does not exist. Skipping to the next page.")
        continue
    except Exception as e:
        print(f"An error occurred on page {page_id}: {e}")
        continue

# 드라이버 종료
driver.quit()

# 데이터프레임 생성
df = pd.DataFrame(data)
print(df.head())  # 데이터 확인
