# Create your views here.
from django.shortcuts import render
import plotly.graph_objs as go
from plotly.io import to_html
import pandas as pd
from django.conf import settings  # settings.py의 경로 설정 사용
import mysql.connector
from sqlalchemy import create_engine

def load_csv_data():
    try:
        # MySQL 연결 문자열 생성
        db_settings = settings.DATABASES['default']
        connection_string = f"mysql+mysqlconnector://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        
        # SQLAlchemy 엔진 생성
        engine = create_engine(connection_string)
        
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM edu_data_f_cleaned"
        data = pd.read_sql(query, engine)
        
        return data
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()  # 오류 발생 시 빈 DataFrame 반환

data = load_csv_data()

def top10_level_view():
    
    # if data.empty:  # 데이터가 비었을 경우
    #     return render(request, "dashboard_hoseop.html", {"error_message": "CSV 데이터를 불러올 수 없습니다."})
    
    # 각 회원 등급별로 이용 금액이 높은 항목 상위 10개 선택
    top10_level_categories = data.groupby('회원등급')[data.columns[9:]].mean().apply(lambda x: x.nlargest(10), axis=1)

    # Plotly 그래프 생성
    fig = go.Figure()

    # 각 회원 등급별로 데이터 추가
    for level in data['회원등급'].unique():
        fig.add_trace(
            go.Scatter(
                x=top10_level_categories.columns,  # 카테고리 (x축)
                y=top10_level_categories.loc[level],  # 평균 소비 금액 (y축)
                mode="lines+markers",
                name=f'Level {level}',  # 회원 등급 이름
                text=top10_level_categories.loc[level],  # Hover 텍스트
                hoverinfo="text+name+x+y",  # Hover 정보 표시
                marker=dict(size=10),  # 점 크기 설정
                line=dict(width=2),  # 선 두께 설정
            )
        )

    # 레이아웃 설정
    fig.update_layout(
        xaxis=dict(title="Categories", tickangle=45),  # x축 제목 및 각도 설정
        yaxis=dict(title="Average Spending"),  # y축 제목
        legend=dict(title="Membership Level"),  # 범례 제목
        template="plotly_white",  # 그래프 스타일
        margin=dict(l=50, r=50, t=50, b=100),  # 여백 설정
    )

    # 그래프를 HTML로 변환
    return to_html(fig, full_html=False)

def lifestage_distribution_view():

    # if data.empty:  # 데이터가 비었을 경우
    #     return render(request, "dashboard_hoseop.html", {"error_message": "CSV 데이터를 불러올 수 없습니다."})

    # 회원등급 및 라이프스테이지 분포 카운트
    life_stage_distribution = data.groupby(['회원등급', '라이프스테이지']).size().unstack(fill_value=0)

    # Plotly 그래프 생성
    fig = go.Figure()

    # 각 라이프스테이지별로 데이터 추가
    for life_stage in life_stage_distribution.columns:
        fig.add_trace(
            go.Bar(
                x=life_stage_distribution.index,  # 회원 등급 (x축)
                y=life_stage_distribution[life_stage],  # 각 회원 등급에 따른 라이프스테이지 수 (y축)
                name=life_stage,  # 라이프스테이지 이름
                hoverinfo="name+x+y",  # Hover 정보 표시
            )
        )

    # 레이아웃 설정
    fig.update_layout(
        barmode='group',  # 막대 그래프를 쌓아 표시
        xaxis=dict(title="Membership Level"),  # x축 제목 설정
        yaxis=dict(title="Count"),  # y축 제목 설정
        legend=dict(title="Life Stage"),  # 범례 제목 설정
        template="plotly_white",  # 그래프 스타일
        margin=dict(l=50, r=50, t=50, b=100),  # 여백 설정
    )

    # 그래프를 HTML로 변환
    return to_html(fig, full_html=False)

def age_and_life_stage_distribution_view():

    # if data.empty:  # 데이터가 비었을 경우
    #     return render(request, "dashboard_hoseop.html", {"error_message": "CSV 데이터를 불러올 수 없습니다."})

    # 거주 지역별 연령대 분포 카운트
    age_distribution = data.groupby(['거주지역_1', '연령대']).size().unstack(fill_value=0)

    # Plotly 그래프 생성 (연령대 분포)
    fig_age = go.Figure()

    # 각 연령대별로 데이터 추가
    for age_group in age_distribution.columns:
        fig_age.add_trace(
            go.Bar(
                x=age_distribution.index,  # 거주 지역 (x축)
                y=age_distribution[age_group],  # 각 거주 지역에 따른 연령대 수 (y축)
                name=str(age_group),  # 연령대 이름
                hoverinfo="name+x+y",  # Hover 정보 표시
            )
        )

    # 연령대 분포 그래프 레이아웃 설정
    fig_age.update_layout(
        barmode='group',  # 막대 그래프를 나란히 표시
        xaxis=dict(title="Residence Area", tickangle=-45),  # x축 제목 및 각도 설정
        yaxis=dict(title="Count"),  # y축 제목 설정
        legend=dict(title="Age Group", x=1.05),  # 범례 제목 및 위치 설정
        template="plotly_white",  # 그래프 스타일
        margin=dict(l=50, r=150, t=50, b=100),  # 여백 설정
    )

    # 거주 지역별 라이프 스테이지 분포 카운트
    life_stage_distribution = data.groupby(['거주지역_1', '라이프스테이지']).size().unstack(fill_value=0)

    # Plotly 그래프 생성 (라이프 스테이지 분포)
    fig_life_stage = go.Figure()

    # 각 라이프 스테이지별로 데이터 추가
    for life_stage in life_stage_distribution.columns:
        fig_life_stage.add_trace(
            go.Bar(
                x=life_stage_distribution.index,  # 거주 지역 (x축)
                y=life_stage_distribution[life_stage],  # 각 거주 지역에 따른 라이프 스테이지 수 (y축)
                name=life_stage,  # 라이프 스테이지 이름
                text=life_stage_distribution[life_stage],  # Hover 텍스트
                hoverinfo="text+name+x+y",  # Hover 정보 표시
            )
        )

    # 라이프 스테이지 분포 그래프 레이아웃 설정
    fig_life_stage.update_layout(
        barmode='group',  # 막대 그래프를 나란히 표시
        xaxis=dict(title="Residence Area", tickangle=-45),  # x축 제목 및 각도 설정
        yaxis=dict(title="Count"),  # y축 제목 설정
        legend=dict(title="Life Stage", x=1.05),  # 범례 제목 및 위치 설정
        template="plotly_white",  # 그래프 스타일
        margin=dict(l=50, r=150, t=50, b=100),  # 여백 설정
    )

    # 두 개의 그래프를 HTML로 변환 및 리턴
    return to_html(fig_age, full_html=False), to_html(fig_life_stage, full_html=False)

def gender_expense_distribution_view():
    
    # if data.empty:  # 데이터가 비었을 경우
    #     return render(request, "dashboard_hoseop.html", {"error_message": "CSV 데이터를 불러올 수 없습니다."})

    # 남성과 여성의 소비 카테고리 합계를 각각 계산
    male_expense = data[data['성별'] == '남자'].loc[:, '가전/가구/주방용품':'학원'].sum().nlargest(10)
    female_expense = data[data['성별'] == '여자'].loc[:, '가전/가구/주방용품':'학원'].sum().nlargest(10)

    # Plotly 그래프 생성 (두 개의 파이 차트)
    fig_male = go.Figure()
    fig_female = go.Figure()

    # 남성 소비 카테고리 파이 차트 추가
    fig_male.add_trace(go.Pie(
        labels=male_expense.index,
        values=male_expense.values,
        name='남성 소비 유형',
        hole=0.3,  # 도넛형 파이 차트
        hoverinfo='label+value',
    ))

    # 여성 소비 카테고리 파이 차트 추가
    fig_female.add_trace(go.Pie(
        labels=female_expense.index,
        values=female_expense.values,
        name='여성 소비 유형',
        hole=0.3,
        hoverinfo='label+value',
    ))

    # 남성 차트 레이아웃 설정
    fig_male.update_layout(
        showlegend=True,
        template="plotly_white"  # 스타일 설정
    )

    # 여성 차트 레이아웃 설정
    fig_female.update_layout(
        showlegend=True,
        template="plotly_white"
    )

    # 그래프를 각각 HTML로 변환 후 리턴
    male_chart_html = to_html(fig_male, full_html=False)
    female_chart_html = to_html(fig_female, full_html=False)

    return male_chart_html, female_chart_html

def age_payment_distribution_view():

    # if data.empty:  # 데이터가 비었을 경우
    #     return render(request, "dashboard_hoseop.html", {"error_message": "CSV 데이터를 불러올 수 없습니다."})

    # 연령대별 신용카드 및 체크카드 사용 금액 합계 계산
    age_payment = data.groupby('연령대')[['신용카드이용금액', '체크카드이용금액']].sum().reset_index()

    # Plotly 그래프 생성
    fig = go.Figure()

    # 신용카드 이용금액 막대 추가
    fig.add_trace(go.Bar(
        x=age_payment['연령대'],
        y=age_payment['신용카드이용금액'],
        name='신용카드이용금액',
        marker_color='mediumseagreen',
        hoverinfo='x+y'  # 마우스 오버 시 x축, y축
    ))

    # 체크카드 이용금액 막대 추가
    fig.add_trace(go.Bar(
        x=age_payment['연령대'],
        y=age_payment['체크카드이용금액'],
        name='체크카드이용금액',
        marker_color='coral',
        hoverinfo='x+y'  # 마우스 오버 시 x축, y축
    ))

    # 레이아웃 설정
    fig.update_layout(
        barmode='group',  # 막대를 나란히 배치
        xaxis=dict(title='연령대'),
        yaxis=dict(title='이용 금액 (단위: 원)'),
        legend=dict(title='결제 방식'),
        template='plotly_white',  # 배경 스타일 설정
        margin=dict(l=50, r=150, t=50, b=100)
    )

    # 그래프를 HTML로 변환 후 리턴
    return to_html(fig, full_html=False)

def age_category_top5_view():

    # # if data.empty:  # 데이터가 비었을 경우
    # #     return render(request, "dashboard_hoseop.html", {"error_message": "CSV 데이터를 불러올 수 없습니다."})

    # # 연령대별 소비 카테고리 합계 계산
    # age_category = data.groupby('연령대').sum().loc[:, '가전/가구/주방용품':'학원']  # 소비 카테고리 컬럼 이름에 맞게 수정

    # # 상위 5개 카테고리를 선택하기 위해 melt 후 연령대별로 정렬
    # age_category_melted = age_category.reset_index().melt(id_vars='연령대', var_name='소비 카테고리', value_name='이용 금액')
    # top_categories = age_category_melted.groupby('연령대').apply(lambda x: x.nlargest(5, '이용 금액')).reset_index(drop=True)

    # Step 1: 연령대별 소비 카테고리 합계 계산
    category_columns = data.loc[:, '가전/가구/주방용품':'학원']
    age_category = data.groupby('연령대')[category_columns.columns].sum()

    # Step 2: 각 연령대별로 상위 5개의 카테고리 선택
    top_categories = pd.DataFrame()

    for age_group, row in age_category.iterrows():
        # 각 연령대에서 상위 5개의 카테고리 선택
        top_5 = row.nlargest(5).index.tolist()  # 상위 5개의 카테고리 이름
        top_5_values = row.nlargest(5).values.tolist()  # 상위 5개의 금액
        temp_df = pd.DataFrame({
            '연령대': [age_group] * 5,
            '소비 카테고리': top_5,
            '이용 금액': top_5_values
        })
        top_categories = pd.concat([top_categories, temp_df])

    # Plotly 그래프 생성
    fig = go.Figure()

    # 각 연령대별로 상위 5개 소비 카테고리의 데이터를 추가
    for category in top_categories['소비 카테고리'].unique():
        category_data = top_categories[top_categories['소비 카테고리'] == category]
        fig.add_trace(go.Bar(
            x=category_data['연령대'],
            y=category_data['이용 금액'],
            name=category,
            hoverinfo='x+y+name',  # 마우스 오버 시 값 표시
        ))

    # 레이아웃 설정
    fig.update_layout(
        barmode='group',  # 막대를 나란히 배치
        xaxis=dict(title='연령대'),
        yaxis=dict(title='총 이용 금액 (단위: 원)'),
        legend=dict(title='소비 카테고리'),
        template='plotly_white',  # 배경 스타일 설정
    )

    # 그래프를 HTML로 변환 후 리턴
    return to_html(fig, full_html=False)

def dashboard_view(request):

    top10_level_html = top10_level_view()
    lifestage_distribution_html = lifestage_distribution_view()
    age_dist_html, lifestage_dist_html = age_and_life_stage_distribution_view()
    male_chart_html, female_chart_html = gender_expense_distribution_view()
    age_payment_html = age_payment_distribution_view()
    age_category_html = age_category_top5_view()

    # 템플릿에 전달
    return render(request, "dashboard_hoseop.html", {
        "top10_level_html" : top10_level_html,
        "lifestage_distribution_html" : lifestage_distribution_html,
        "age_dist_html" : age_dist_html,
        "lifestage_dist_html" : lifestage_dist_html,
        "male_chart_html" : male_chart_html,
        "female_chart_html" : female_chart_html,
        "age_payment_html" : age_payment_html,
        "age_category_html" : age_category_html
        })