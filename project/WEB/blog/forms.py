# blog/forms.py
from django import forms
from .models import Board, Comment  # BoardPost와 Comment 모델을 가져옵니다.

class BoardPostForm(forms.ModelForm):
    class Meta:
        model = Board # 모델을 BoardPost로 설정
        fields = ['title', 'content']  # 제목과 내용만 입력받기

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment  # 모델을 Comment로 설정
        fields = ['content']  # 댓글 내용만 입력받기