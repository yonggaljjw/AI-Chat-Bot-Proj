import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 금융위원회 입법예고 페이지의 기본 URL
base_url = "https://www.fsc.go.kr/po040301"

# 데이터 저장을 위한 리스트 초기화
data = []

# 1~50페이지까지 반복 크롤링
for page in range(1, 10):  
    # 페이지별 URL 생성
    url = f"{base_url}?curPage={page}"
    
    try:
        response = requests.get(url, timeout=10)  # 페이지 요청에 시간 초과 설정
        response.raise_for_status()  # HTTP 오류가 발생하면 예외 발생
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        continue  # 오류 발생 시 다음 페이지로 넘어감

    # 공고 목록에서 제목과 링크 추출
    subjects = soup.select('div.subject a')

    for subject in subjects:
        title = subject.text.strip()
        link = subject['href']

        # 링크 값에서 불필요한 부분을 정리
        if link.startswith('./'):
            link = link.replace('./', '/')
        detail_url = f"https://www.fsc.go.kr{link}"

        try:
            # 각 공고의 상세 페이지 요청
            detail_response = requests.get(detail_url, timeout=10)  # 상세 페이지 요청에 시간 초과 설정
            detail_response.raise_for_status()
            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching detail page {detail_url}: {e}")
            continue  # 오류 발생 시 다음 항목으로 넘어감

        # 예고기간 파싱
        notice_period_span = detail_soup.select_one('div.info.type2 span:-soup-contains("예고기간")')
        if notice_period_span:
            notice_period = notice_period_span.text.split("예고기간")[1].strip()
            start_date, end_date = notice_period.split(" ~ ")
            print(start_date, end_date)
        else:
            start_date, end_date = "날짜 정보 없음", "날짜 정보 없음"

        # 상세 내용 파싱 (예: <div class="cont">)
        content_tag = detail_soup.select_one('div.cont')
        content = "제목" + title + "\n시작날짜: " + start_date + " 종료날짜: " + end_date + "\n내용: " + content_tag.text.strip() if content_tag else title + "내용 없음"


        # 데이터 리스트에 추가
        data.append({
            "title": title,
            "start_date": start_date,
            "end_date": end_date,
            "URL": detail_url,
            "content": content
        })

        # 간격 두기 (서버에 부담을 주지 않기 위해)
        time.sleep(1)

# 데이터프레임으로 변환
df = pd.DataFrame(data)

# 데이터프레임 출력
print(df)

# CSV 파일로 저장 (옵션)
df.to_csv('fsc_announcements.csv', index=False, encoding='utf-8')
