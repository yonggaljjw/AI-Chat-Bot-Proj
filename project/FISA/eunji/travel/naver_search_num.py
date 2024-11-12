# -*- coding: utf-8 -*-
import os
import urllib.request
import json
import pandas as pd


# travel_info 
df_country = pd.read_csv("./국토연구원 세계도시정보 자료(2019년).csv", encoding="EUC-KR")

# group_name과 keywords 생성
def create_travel_info(df):
    travel_info = []
    
    for _, row in df.iterrows():
        country = row['나라']
        city = row['도시명']
        group_name = f"{city} 여행"
        keywords = [country, f"{country} 여행", city, "여행", "해외여행"]
        
        travel_info.append({
            "group_name": group_name,
            "keywords": keywords
        })
    
    return travel_info

# 결과 생성
travel_info = create_travel_info(df_country)


# 네이버 API 인증 정보
client_id = "naver_api"
client_secret = "naver_api_key"
url = "https://openapi.naver.com/v1/datalab/search"

# 기본 요청 변수 설정
start_date = "2024-01-01"
end_date = "2024-11-10"
time_unit = "week"
# device = ["pc", "mo"]
# ages = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
# gender = ["m","f"]


# 저장할 폴더 경로
output_folder = "naver_country"
os.makedirs(output_folder, exist_ok=True)  # 폴더가 없으면 생성

# API 요청 및 결과 저장 함수
def fetch_and_save_data(group_name, keywords):
    # JSON body 생성
    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [{"groupName": group_name, "keywords": keywords}]
        # "device": device,
        # "ages": ages,
        # "gender": gender
    })

    # Request 구성 및 전송
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    request.add_header("Content-Type", "application/json")
    
    # 응답 처리
    try:
        response = urllib.request.urlopen(request, data=body.encode("utf-8"))
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            result = response_body.decode('utf-8')
            
            # 결과를 폴더 내 파일에 저장 (group_name을 파일명으로 사용)
            file_name = os.path.join(output_folder, f"{group_name.replace(' ', '_')}_result.json")
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Saved result for {group_name} to {file_name}")
        else:
            print(f"Error Code: {rescode} for group {group_name}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason} for group {group_name}")

# travel_info를 반복하면서 각 group_name과 keywords로 데이터 요청 및 저장
for info in travel_info:
    group_name = info["group_name"]
    keywords = info["keywords"]
    fetch_and_save_data(group_name, keywords)
