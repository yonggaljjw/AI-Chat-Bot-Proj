from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_plotly_dash import *

from dashboards.watching_word import app 
from dashboards.D_02_visualization_origin import app
from dashboards.answering_service import generate_answer_plus_date, if_date

import json
import openai
from dotenv import load_dotenv
import os


load_dotenv()

### 채팅창 ###

# OpenAI API 키 설정


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
    data = json.loads(request.body)
    user_message = data.get('message', '')
    ai_message = query_with_date(user_message)
    return JsonResponse({'message': ai_message})
    '''
    # OpenAI API를 사용하여 응답 생성
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Your name is 우대리, You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ]
    )

    ai_message = response.choices[0].message['content']
    return JsonResponse({'message': ai_message})
    '''
######




