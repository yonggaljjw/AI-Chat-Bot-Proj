from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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



@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    data = json.loads(request.body)
    user_message = data.get('message', '')

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

######




