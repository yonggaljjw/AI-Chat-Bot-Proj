# blog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Board, Comment  # BoardPost와 Comment 모델을 가져옵니다.
from .forms import CommentForm, BoardPostForm  # BoardPostForm도 가져옵니다.
from django.http import HttpResponseRedirect
# 블로그 소개 페이지 뷰
class BoardAboutMeView(TemplateView):
    template_name = 'blog/about_me.html'



# 댓글 수정 뷰
class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment_form.html'

    def get_success_url(self):
        return reverse_lazy('blog:blog_detail', kwargs={'pk': self.object.post.pk})  # 수정 후 게시글 상세 페이지로 리다이렉트

# 댓글 삭제 뷰
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk  # 댓글이 속한 게시글의 pk를 가져옴
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:blog_detail', pk=post_pk)  # 댓글 삭제 후 게시글 상세 페이지로 리다이렉트
    return render(request, 'blog/comment_confirm_delete.html', {'comment': comment})

# 게시판 홈 뷰 (게시글 리스트)
class BoardHomeView(ListView):
    model = Board # 모델 이름을 BoardPost로 변경
    template_name = 'blog/blog_home.html'  # 템플릿 경로 수정
    context_object_name = 'posts'  # 컨텍스트 이름을 posts로 변경
    ordering = '-created_at'  # 최근 게시글 순으로 정렬

# 게시판 상세 뷰
class BoardDetailView(DetailView):
    model = Board  # 모델 이름을 BoardPost로 변경
    template_name = 'blog/blog_detail.html'  # 템플릿 경로 수정
    context_object_name = 'post'  # 컨텍스트 이름을 post로 변경

# 게시판 생성 뷰
class BoardCreateView(LoginRequiredMixin, CreateView):
    model = Board # 모델 이름을 BoardPost로 변경
    form_class = BoardPostForm  # 게시글 폼 클래스 설정 (BoardPostForm이 정의되어 있어야 함)
    template_name = 'blog/board_form.html'  # 템플릿 경로 수정

    def form_valid(self, form):
        form.instance.author = self.request.user  # 게시글 작성자를 현재 로그인한 사용자로 설정
        return super().form_valid(form)
    


# 게시판 수정 뷰
class BoardUpdateView(LoginRequiredMixin, UpdateView):
    model = Board # 모델 이름을 BoardPost로 변경
    form_class = BoardPostForm  # 게시글 폼 클래스 설정 (BoardPostForm이 정의되어 있어야 함)
    template_name = 'blog/board_form.html'  # 템플릿 경로 수정

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()  # 게시글 객체 가져오기
        if request.user != post.author:  # 작성자가 아닌 경우 권한 체크
            return redirect('blog:blog_home')  # 권한이 없으면 홈으로 리다이렉트
        return super().dispatch(request, *args, **kwargs)

# 게시판 삭제 뷰
class BoardDeleteView(LoginRequiredMixin, DeleteView):
    model = Board  # 모델 이름을 BoardPost로 변경
    template_name = 'blog/board_confirm_delete.html'  # 템플릿 경로 수정
    success_url = reverse_lazy('blog:blog_home')  # 삭제 후 블로그 홈으로 리다이렉트

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()  # 게시글 객체 가져오기
        if request.user != post.author:  # 작성자가 아닌 경우 권한 체크
            return redirect('blog:blog_home')  # 권한이 없으면 홈으로 리다이렉트
        return super().dispatch(request, *args, **kwargs)