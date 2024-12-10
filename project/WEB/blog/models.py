# blog/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Board(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)  # 게시글 제목
    content = models.TextField()  # 게시글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 생성일
    updated_at = models.DateTimeField(auto_now=True)  # 수정일
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # 작성자

    class Meta:
        db_table = "blog_board"
    def __str__(self):
        return self.title  # 게시글 제목 반환
    
    def get_absolute_url(self):
        return reverse('blog:blog_detail', kwargs={'pk': self.pk})


class Comment(models.Model):
    id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Board, related_name='comments', on_delete=models.CASCADE)  # 댓글이 속한 게시글
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # 댓글 작성자
    content = models.TextField()  # 댓글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 생성일

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'  # 댓글 정보 반환
    

