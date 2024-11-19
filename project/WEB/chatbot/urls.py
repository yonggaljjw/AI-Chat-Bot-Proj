from django.urls import path
from . import views_hoseop
from . import views_chatbot
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('index/', views_hoseop.dashboard_view, name='index'),
    path('chatbot/send/', views_chatbot.chatbot_response, name='chatbot_send'),
    # path('dashboard1/', views.dashboard1, name='dashboard1'),
    # path('dashboard2/', views.dashboard2, name='dashboard2'),
    # path('dashboard3/', views.dashboard3, name='dashboard3'),
    # path('dashboard4/', views.dashboard4, name='dashboard4'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)