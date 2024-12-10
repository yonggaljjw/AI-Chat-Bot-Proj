# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BoardHomeView.as_view(), name='blog_home'),  # 게시판 홈
    path('create/', views.BoardCreateView.as_view(), name='blog_create'),  # 게시글 작성
    path('<int:pk>/', views.BoardDetailView.as_view(), name='blog_detail'),  # 게시글 상세 보기
    path('<int:pk>/update/', views.BoardUpdateView.as_view(), name='blog_update'),  # 게시글 수정
    path('<int:pk>/delete/', views.BoardDeleteView.as_view(), name='blog_delete'),  # 게시글 삭제
    # path('<int:pk>/create-comment/', views.create_comment, name='create_comment'),  # 댓글 작성
    # path('comment/<int:pk>/update/', views.CommentUpdateView.as_view(), name='update_comment'),  # 댓글 수정
    # path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),  # 댓글 삭제
    path('about_me/', views.BoardAboutMeView.as_view(), name='about_me'),  # About me 수정
]