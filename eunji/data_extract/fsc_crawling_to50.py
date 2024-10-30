import requests
from bs4 import BeautifulSoup
import pandas as pd

# 금융위원회 입법예고 페이지의 기본 URL
base_url = "https://www.fsc.go.kr/po040301"

# 데이터 저장을 위한 리스트 초기화
data = []

# 1~30페이지까지 반복 크롤링
for page in range(1, 51):  # 30 페이지로 확장
    # 페이지별 URL 생성
    url = f"{base_url}?curPage={page}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 공고 목록에서 제목과 링크 추출
    subjects = soup.select('div.subject a')

    for subject in subjects:
        title = subject.text.strip()
        link = subject['href']

        # 링크 값에서 불필요한 부분을 정리
        if link.startswith('./'):
            link = link.replace('./', '/')
        detail_url = f"https://www.fsc.go.kr{link}"

        # 각 공고의 상세 페이지 요청
        detail_response = requests.get(detail_url)
        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

        # 상세 내용 파싱 (예: <div class="cont">)
        content_tag = detail_soup.select_one('div.cont')
        content = content_tag.text.strip() if content_tag else "내용 없음"

        # 날짜 정보 파싱
        date_span = detail_soup.select_one('div.day span')
        announcement_date = date_span.text.strip() if date_span else "날짜 정보 없음"

        # 데이터 리스트에 추가
        data.append({
            "제목": title,
            "날짜": announcement_date,
            "URL": detail_url,
            "내용": content
        })

# 데이터프레임으로 변환
df = pd.DataFrame(data)

# 데이터프레임 출력
print(df)

# CSV 파일로 저장 (옵션)
df.to_csv('fsc_announcements.csv', index=False, encoding='utf-8')