import json
import pandas as pd
from konlpy.tag import Okt
import urllib.request
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter

client_id = "xaKw7jRi9oNo8orrCBYB"
client_secret = "TQtRJrhWU9"

def get_naver_news(keyword, start_date, end_date):
    base_url = "https://openapi.naver.com/v1/search/news.json"
    enc_keyword = urllib.parse.quote(keyword)
    
    start = start_date.strftime('%Y%m%d')
    end = end_date.strftime('%Y%m%d')
    
    url = f"{base_url}?query={enc_keyword}&start=1&display=100&sort=date"
    
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)

    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            response_body = response.read()
            return json.loads(response_body.decode('utf-8'))['items']
        else:
            print(f"Error Code: {response.getcode()}")
            return None
    except Exception as e:
        print(e)
        return None

def preprocess_text(text):
    okt = Okt()
    tokens = okt.nouns(text)
    stop_words = set(['것', '등', '및', '약', '또', '를', '을', '이', '가', '은', '는'])
    return [word for word in tokens if len(word) > 1 and word not in stop_words]

def analyze_keywords(news_data):
    df = pd.DataFrame(news_data)
    df['pDate'] = pd.to_datetime(df['pubDate'])
    
    # 텍스트 전처리
    df['processed_text'] = df['description'].apply(preprocess_text)
    
    # 월별로 그룹화하여 키워드 빈도수 계산
    df['month'] = df['pDate'].dt.to_period('M')
    monthly_keywords = df.groupby('month')['processed_text'].apply(lambda x: sum(x, []))
    
    return monthly_keywords

def visualize_keywords(monthly_keywords, top_n=10):
    # 월별 키워드 빈도를 계산하고, 상위 키워드를 시각화
    keyword_trends = {}
    
    for month, keywords in monthly_keywords.items():
        keyword_counts = Counter(keywords)
        top_keywords = keyword_counts.most_common(top_n)
        
        for keyword, count in top_keywords:
            if keyword not in keyword_trends:
                keyword_trends[keyword] = []
            keyword_trends[keyword].append((month.strftime('%Y-%m'), count))
    
    # 각 키워드의 빈도를 시각화
    plt.figure(figsize=(12, 8))
    for keyword, values in keyword_trends.items():
        months, counts = zip(*values)
        plt.plot(months, counts, marker='o', label=keyword)
    
    plt.title('Monthly Keyword Trends')
    plt.xlabel('Month')
    plt.ylabel('Frequency')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    keyword = input("검색어를 입력하세요: ")
    
    # 원하는 날짜 범위 설정 (예: 2023년 1월부터 2023년 12월까지)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)

    news_data = get_naver_news(keyword, start_date, end_date)
    
    if news_data is None:
        print("뉴스 데이터를 가져오지 못했습니다.")
        return
    
    # 키워드 분석
    monthly_keywords = analyze_keywords(news_data)
    
    # 키워드 시각화
    visualize_keywords(monthly_keywords)

if __name__ == '__main__':
    main()
