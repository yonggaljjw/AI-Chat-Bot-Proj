from django.apps import AppConfig

class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # 기본 자동 필드 유형 설정
    name = "blog"  # 애플리케이션 이름 설정