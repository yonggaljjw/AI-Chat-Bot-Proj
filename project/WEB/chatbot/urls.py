from django.urls import path
from .views import views_main
from .views import views_chatbot
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('main/', views_main.dashboard_view, name='main'),
    path('chatbot/send/', views_chatbot.chatbot_response, name='chatbot_send'),
    path('chatbot/initialize-session/', views_chatbot.initialize_chat_session, name='initialize_chat_session'),
    path('chatbot/sessions/', views_chatbot.get_chat_sessions, name='chat_sessions'),
    path('chatbot/sessions/<str:session_id>/messages/', views_chatbot.get_session_messages, name='session_messages'),
    path('chatbot/clear-session/', views_chatbot.clear_chat_session, name='clear_chat_session'),
    path('chatbot/like/', views_chatbot.update_message_like, name='update_message_like'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
