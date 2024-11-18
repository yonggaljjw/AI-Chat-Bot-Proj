from django.urls import path
from . import views_eunji
from . import views_hoseop
from . import views_chatbot

urlpatterns = [
    # path('dynamic-graph/', views.dynamic_graph, name='dynamic_graph'),
    path('dashboard_hoseop/', views_hoseop.dashboard_view, name='dashboard_hoseop'),
    path('chatbot/send/', views_chatbot.chatbot_response, name='chatbot_send'),
]