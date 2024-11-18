from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        # 여기에 실제 챗봇 로직 구현
        # 임시 응답
        bot_response = f"받은 메시지: {user_message}"
        
        return JsonResponse({
            'status': 'success',
            'response': bot_response
        })
    return JsonResponse({'status': 'error'}, status=400)
