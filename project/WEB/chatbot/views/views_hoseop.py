# Create your views here.
import plotly.graph_objs as go
from plotly.io import to_json
import pandas as pd
from django.conf import settings  # settings.py의 경로 설정 사용
from sqlalchemy import create_engine


def load_wooricard_data():
    try:
        # MySQL 연결 문자열 생성
        db_settings = settings.DATABASES['default']
        connection_string = f"mysql+pymysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        
        # SQLAlchemy 엔진 생성
        engine = create_engine(connection_string)
        
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM wooricard_data"
        data = pd.read_sql(query, engine)
        
        return data
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()  # 오류 발생 시 빈 DataFrame 반환

data = load_wooricard_data()

def load_cpi_card_data():
    try:
        # MySQL 연결 문자열 생성
        db_settings = settings.DATABASES['default']
        connection_string = f"mysql+pymysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        
        # SQLAlchemy 엔진 생성
        engine = create_engine(connection_string)
        
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM cpi_card_data"
        data = pd.read_sql(query, engine)
        
        return data
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()  # 오류 발생 시 빈 DataFrame 반환

def gender_view():

    # 전체, 남성, 여성의 소비 카테고리 합계를 각각 계산
    total_expense = data.set_index('index').전체.nlargest(10)
    male_expense = data.set_index('index').남성.nlargest(10)
    female_expense = data.set_index('index').여성.nlargest(10)

    # Figure 생성
    fig = go.Figure()

    # 전체 소비 카테고리 파이 차트 (초기 보이는 상태)
    fig.add_trace(go.Pie(
        labels=total_expense.index,
        values=total_expense.values,
        name='전체 소비 유형',
        hole=0.3,
        visible=True,
        hoverinfo='label+percent',
        textinfo='none'  # 텍스트 표시 제거
    ))

    # 남성 소비 카테고리 파이 차트 (초기 숨김 상태)
    fig.add_trace(go.Pie(
        labels=male_expense.index,
        values=male_expense.values,
        name='남성 소비 유형',
        hole=0.3,
        visible=False,
        hoverinfo='label+percent',
        textinfo='none'  # 텍스트 표시 제거
    ))

    # 여성 소비 카테고리 파이 차트 (초기 숨김 상태)
    fig.add_trace(go.Pie(
        labels=female_expense.index,
        values=female_expense.values,
        name='여성 소비 유형',
        hole=0.3,
        visible=False,
        hoverinfo='label+percent',
        textinfo='none'  # 텍스트 표시 제거
    ))

    # 버튼 생성
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.5,
                y=1.5,
                showactive=True,
                buttons=list([
                    dict(label="전체",
                         method="update",
                         args=[{"visible": [True, False, False]}],
                         ),
                    dict(label="남성",
                         method="update",
                         args=[{"visible": [False, True, False]}],
                         ),
                    dict(label="여성",
                         method="update",
                         args=[{"visible": [False, False, True]}]
                         )
                ]),
            )
        ]
    )

    # 레이아웃 설정
    fig.update_layout(
        showlegend=True,
        template="plotly_white",
        # height=400,
        legend=dict(
            x=0,        
            y=0,        
            xanchor='left',
            yanchor='top',
            orientation='h',
        )
    )

    return to_json(fig)


def cpi_card_predict_view():

    """
    드롭다운으로 카테고리를 선택하여 PCE 및 CPI 데이터를 시각화하는 Plotly 그래프 생성 함수.
    오른쪽 y축에 CPI 값을 표시하고, 신뢰구간 내부를 옅은 색으로 채웁니다.
    """

    data = load_cpi_card_data()

    try:
        # 카테고리 정의
        categories = [
            '합계', '식료품', '의류/잡화', '연료', '가구/가전', '의료/보건', '여행/교통',
            '오락/문화', '교육', '숙박/음식', '공과금/개인 및 전문 서비스'
        ]

        # 기본 그래프 객체 생성
        fig = go.Figure()

        # 드롭다운 버튼 데이터 생성
        buttons = []
        for i, category in enumerate(categories):
            # 컬럼명 설정
            pce_pred = f"{category}_PCE_pred"
            pce_lower = f"{category}_PCE_lower"
            pce_upper = f"{category}_PCE_upper"
            cpi_pred = f"{category}_CPI_pred"
            cpi_lower = f"{category}_CPI_lower"
            cpi_upper = f"{category}_CPI_upper"

            # PCE 신뢰구간 및 예측값 trace 추가
            fig.add_trace(go.Scatter(
                x=data['TIME'], y=data[pce_upper],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                visible=(i == 0)  # 첫 번째 카테고리만 표시
            ))
            fig.add_trace(go.Scatter(
                x=data['TIME'], y=data[pce_lower],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(0, 0, 255, 0.2)',  # 옅은 파란색
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                visible=(i == 0)
            ))
            fig.add_trace(go.Scatter(
                x=data['TIME'], y=data[pce_pred],
                mode='lines',
                name=f"{category} PCE",
                line=dict(color='blue'),
                visible=(i == 0)
            ))

            # CPI 신뢰구간 및 예측값 trace 추가
            fig.add_trace(go.Scatter(
                x=data['TIME'], y=data[cpi_upper],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                visible=(i == 0),
                yaxis="y2"  # 오른쪽 y축 사용
            ))
            fig.add_trace(go.Scatter(
                x=data['TIME'], y=data[cpi_lower],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(255, 165, 0, 0.2)',  # 옅은 주황색
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                visible=(i == 0),
                yaxis="y2"  # 오른쪽 y축 사용
            ))
            fig.add_trace(go.Scatter(
                x=data['TIME'], y=data[cpi_pred],
                mode='lines',
                name=f"{category} CPI",
                line=dict(color='orange'),
                visible=(i == 0),
                yaxis="y2"  # 오른쪽 y축 사용
            ))

            # 버튼 생성
            visibility = [False] * len(categories) * 6  # 총 trace 수
            for j in range(i * 6, (i + 1) * 6):
                visibility[j] = True  # 해당 카테고리 trace만 활성화
            buttons.append(dict(
                label=category,
                method="update",
                args=[{"visible": visibility}, {"title": f"{category} PCE 및 CPI 예측 시계열 데이터"}]
            ))

        # 레이아웃 설정
        fig.update_layout(
            # title=f"{categories[0]} PCE 및 CPI 예측 시계열 데이터",
            xaxis=dict(title="시간"),
            yaxis=dict(title="PCE 지출", titlefont=dict(color="blue"), tickfont=dict(color="blue")),
            yaxis2=dict(
                title="CPI 지수",
                titlefont=dict(color="orange"),
                tickfont=dict(color="orange"),
                overlaying="y",
                side="right"
            ),
            updatemenus=[{
                "buttons": buttons,
                "direction": "down",
                "showactive": True,
                "x": 1.15,
                "y": 1.15,
            }],
            legend=dict(x=0.5, y=1.2, orientation="h"),
            template="plotly_white",
        )

        # HTML로 변환
        return to_json(fig)
    
    except Exception as e:
        print(f"그래프 생성 중 오류 발생: {e}")
        return None