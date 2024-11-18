from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_plotly_dash import *

from dashboards.watching_word import app 
from dashboards.D_02_visualization_origin import app
from dashboards.answering_service import generate_answer_plus_date, if_date

from opensearchpy import OpenSearch
import json
import openai
from dotenv import load_dotenv
import os

load_dotenv()


def index(request):
    return render(request, 'index.html') 

# def dash_app(request):
#     # Dash 앱을 HTML로 변환
#     plot_div = pio.to_html(dash_app_instance, full_html=False)
    
#     return render(request, 'dash_app_template.html', context={'plot_div': plot_div})

# 질문에 날짜가 포함된 경우 해당 날짜로 필터링하여 답변 생성
def query_with_date(question):
    index_name = "raw_data"
    start_date = if_date(question)  # 질문에서 시작 날짜 추출
    end_date = if_date(question)  # 종료 날짜를 시작 날짜와 동일하게 설정 (단일 날짜)
    response_text = generate_answer_plus_date(question, index_name, pre_msgs=None, start_date=start_date, end_date=end_date)
    return response_text


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        # 날짜 관련 질문인지 확인
        if any(date_keyword in user_message for date_keyword in ['언제', '날짜', '일자', '년', '월', '일']):
            # 날짜 기반 검색 함수 호출
            ai_message = query_with_date(user_message)
        else:
            # OpenAI API를 사용한 일반 응답
            response = openai.ChatCompletion.create(
                model="gpt-4",  # 또는 사용 가능한 모델
                messages=[
                    {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다. 한국어로 응답해주세요."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            ai_message = response.choices[0].message['content']
        
        return JsonResponse({
            'status': 'success',
            'message': ai_message
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'오류가 발생했습니다: {str(e)}'
        }, status=500)


# chart 4
def recent_posts(request):
    # 인증 정보를 사용하여 OpenSearch 클라이언트 생성
    host = os.getenv("OPENSEARCH_HOST")
    port = os.getenv("OPENSEARCH_PORT")
    auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

    client = OpenSearch(
        hosts = [{'host': host, 'port': port}],
        http_auth = auth,
        use_ssl = True,
        verify_certs = False
    )
    # Elasticsearch 쿼리 작성
    query = {
        "sort": [
            {"날짜": {"order": "desc"}}
        ],
        "size": 10,
        "_source": ["날짜", "제목"]
    }

    # 'raw_data' 인덱스에서 검색
    response = client.search(index="raw_data", body=query)
    posts = [
        {
            "date": hit["_source"].get("날짜"),
            "title": hit["_source"].get("제목")
        }
        for hit in response["hits"]["hits"]
    ]

    # posts 데이터를 템플릿으로 전달
    return render(request, "index.html", {"posts": posts})


def dashboard1(request):
    return render(request, 'dashboard1.html')

def dashboard2(request):
    return render(request, 'dashboard2.html')

def dashboard3(request):
    return render(request, 'dashboard3.html')

def dashboard4(request):
    return render(request, 'dashboard4.html')
