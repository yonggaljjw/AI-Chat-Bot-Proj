import os
import json
import time
import requests
import datetime
from collections import Counter
from konlpy.tag import Okt
from dotenv import load_dotenv
from opensearchpy import OpenSearch
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import timedelta
from transformers import pipeline

# 환경 변수 로드
load_dotenv()

# 네이버 API 설정
NAVER_CLIENT_ID = os.getenv("NAVER_API_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_API_SECRET")

# OpenSearch 설정
host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=False
)

# 텍스트 요약을 위한 Hugging Face 모델 로드
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# 네이버 API 요청 함수
def fetch_naver_search_volume(query, retries=3, delay=5):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "User-Agent": "Mozilla/5.0"
    }
    params = {"query": query, "display": 100}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()['total']
            elif response.status_code == 429:
                time.sleep(delay)
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}. Retrying in {delay} seconds...")
            time.sleep(5)
    return 0

# 텍스트 전처리 함수
def preprocess_text(text, stop_words):
    okt = Okt()
    tokens = okt.nouns(text)
    return [word for word in tokens if len(word) > 1 and word not in stop_words]

# 카테고리 데이터 처리 함수
def process_category_data(data, category):
    two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
    stop_words = set(['것', '등', '및', '약', '또', '를', '을', '이', '가', '은', '는', category])
    filtered_data = []
    word_counter = Counter()

    for item in data:
        if 'pubDate' in item:
            pDate = datetime.datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
            if pDate > two_days_ago:
                processed_text = preprocess_text(item['description'], stop_words)
                word_counter.update(processed_text)

    for word, count in word_counter.items():
        current_volume = fetch_naver_search_volume(word)
        trend_growth = calculate_trend_growth(current_volume, 0)  # 이전 검색량이 0인 경우
        article_links = [item['link'] for item in data if word in item['description']]

        # 요약된 기사 내용 추가
        article_contents = " ".join([item['description'] for item in data if word in item['description']])
        summary = summarize_text(article_contents)  # 기사 요약

        filtered_data.append({
            'word': word,
            'count': count,
            'trend_growth': trend_growth,
            'links': article_links,
            'summary': summary,  # 요약된 내용 추가
            'category': category
        })
    return filtered_data

# 트렌드 성장률 계산
def calculate_trend_growth(current_volume, previous_volume):
    if previous_volume == 0:
        return 100.0
    growth_rate = ((current_volume - previous_volume) / previous_volume) * 100
    return growth_rate

# 텍스트 요약 함수
def summarize_text(text, max_length=200):
    try:
        # 요약을 생성합니다.
        summary = summarizer(text, max_length=max_length, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return "Summary not available"

# OpenSearch 업로드 함수
def upload_to_opensearch(data):
    index_name = "trend_data"
    for category, items in data.items():
        for item in items:
            client.index(
                index=index_name,
                body={
                    'word': item['word'],
                    'count': item['count'],
                    'trend_growth': item['trend_growth'],
                    'links': item['links'],
                    'summary': item['summary'],
                    'category': category,
                    'date': datetime.datetime.now().strftime('%Y-%m-%d')
                }
            )

# 데이터 저장 및 업로드 파이프라인 실행
def run_pipeline():
    categories = ['경제', '스포츠', '사회', '정치']
    results = {}
    for category in categories:
        data = []
        for i in range(1, 100, 100):
            url = f"https://openapi.naver.com/v1/search/news.json?query={category}&start={i}&display=100"
            headers = {
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data.extend(response.json()['items'])
            time.sleep(3)
        results[category] = process_category_data(data, category)
    upload_to_opensearch(results)

# Airflow DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'trend_analysis',
    default_args=default_args,
    schedule_interval='0 7 * * *',  # 매일 아침 7시에 실행
    catchup=False,
) as dag:
    t1 = PythonOperator(
        task_id='run_pipeline',
        python_callable=run_pipeline
    )

    t1
