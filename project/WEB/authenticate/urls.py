from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_user, name ='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('dashboard_hoseop/', views.dashboard_hoseop, name='dashboard_hoseop'),
    path("chatbot/send/", views.chat, name="chatbot_send"),
]