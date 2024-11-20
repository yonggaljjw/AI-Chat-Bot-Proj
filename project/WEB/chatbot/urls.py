from django.urls import path
from . import views_main
from . import views_chatbot
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('index/', views_main.dashboard_view, name='index'),
    path('chatbot/send/', views_chatbot.chatbot_response, name='chatbot_send'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
