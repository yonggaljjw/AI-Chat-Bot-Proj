import requests
from bs4 import BeautifulSoup
import pandas as pd

# 페이지 URL
url = "https://www.0404.go.kr/dev/country.mofa?idx=&hash=&chkvalue=no1&stext=&group_idx="

# 페이지 요청
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# 데이터 수집
data = []
countries = soup.select("ul.country_list > li")

for country in countries:
    country_name = country.select_one("a").text.strip()
    img_tags = country.select("img")
    travel_advice = [img["alt"].strip() for img in img_tags if img.get("alt")]  # alt 속성이 있는 경우에만 추가
    travel_advice = ", ".join(travel_advice) if travel_advice else "정보 없음"  # alt 속성이 없으면 "정보 없음"
    data.append([country_name, travel_advice])

# 데이터프레임 생성
df = pd.DataFrame(data, columns=["Country", "Travel_Advice"])

# 데이터프레임 출력
print(df)
