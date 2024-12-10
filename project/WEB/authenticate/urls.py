from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.login_user, name ='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('main/', views.main, name=',main'),
    path('blog/', include('blog.urls')),  # blog 앱의 URL을 포함시킴
]