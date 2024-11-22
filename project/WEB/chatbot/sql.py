from django.conf import settings
from sqlalchemy import create_engine

def get_db_engine():
    # MySQL 연결 문자열 생성
    db_settings = settings.DATABASES['default']
    connection_string = f"mysql+pymysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
    
    # SQLAlchemy 엔진 생성 및 반환
    return create_engine(connection_string)

# 전역 엔진 인스턴스 생성
engine = get_db_engine()

# 외부에서 사용할 수 있도록 export
__all__ = ['engine', 'get_db_engine']
