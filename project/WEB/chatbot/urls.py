from django.urls import path
from . import views_eunji
from . import views_hoseop
from . import views_chatbot

urlpatterns = [
    path('index/', views_hoseop.dashboard_view, name='index'),
    path('chatbot/send/', views_chatbot.chatbot_response, name='chatbot_send'),
]