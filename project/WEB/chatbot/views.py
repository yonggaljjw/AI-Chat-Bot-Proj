from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_plotly_dash import *
from eunchai.watching_word import app 
from jiyeon.D_02_visualization_origin import app

import json
import openai
from dotenv import load_dotenv
import os


load_dotenv()

### 채팅창 ###

# OpenAI API 키 설정
openai.api_key = os.getenv('openaikey')

def index(request):
    return render(request, 'index.html') 

# def dash_app(request):
#     # Dash 앱을 HTML로 변환
#     plot_div = pio.to_html(dash_app_instance, full_html=False)
    
#     return render(request, 'dash_app_template.html', context={'plot_div': plot_div})

@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')

        # GPT 모델을 사용하여 응답 생성
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant named 우대리."},
                {"role": "user", "content": user_message}
            ]
        )

        bot_response = response.choices[0].message['content']

        return JsonResponse({'message': f" {bot_response}"})
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)