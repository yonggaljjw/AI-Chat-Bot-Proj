from django.shortcuts import render
import plotly.graph_objs as go
from plotly.io import to_html
import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine
import pymysql

def load_fred_data_from_sql():
    try:
        # MySQL 연결 문자열 생성
        db_settings = settings.DATABASES['default']
        connection_string = f"mysql+pymysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        
        # SQLAlchemy 엔진 생성
        engine = create_engine(connection_string)
        
        # MySQL 테이블을 DataFrame으로 읽어오기
        query = "SELECT * FROM fred_data"
        fred_data = pd.read_sql(query, engine)
        
        return fred_data
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
        return pd.DataFrame()

fred_data = load_fred_data_from_sql()

def gdp_and_rates_view():
    """GDP 성장률, 연방기금금리, 실업률 비교 그래프"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['GDP Growth Rate'],
        mode='lines',
        name='GDP 성장률',
        line=dict(color='blue', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['FFTR'],
        mode='lines',
        name='연방기금금리(FFTR)',
        line=dict(color='red'),
        yaxis='y2'
    ))

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['Unemployment Rate'],
        mode='lines',
        name='실업률',
        line=dict(color='green'),
        yaxis='y2'
    ))

    fig.update_layout(
        title='GDP 성장률과 연방기금금리, 실업률 비교',
        xaxis_title='날짜',
        yaxis=dict(
            title='GDP 성장률 (%)',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title='연방기금금리(FFTR) 및 실업률 (%)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        showlegend=True,
        legend=dict(x=0, y=1)
    )

    return to_html(fig, full_html=False)

def price_indicators_view():
    """물가지표 추이 그래프"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['CPI'],
        mode='lines',
        name='CPI',
        line=dict(color='blue', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['Core PCE'],
        mode='lines',
        name='Core PCE',
        line=dict(color='red', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['Core CPI'],
        mode='lines',
        name='Core CPI',
        line=dict(color='green', width=2)
    ))

    fig.update_layout(
        title='물가지표 추이',
        xaxis_title='날짜',
        yaxis_title='변화율 (%)',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        showlegend=True,
        legend=dict(x=0, y=1)
    )

    return to_html(fig, full_html=False)

def consumer_trends_view():
    """소비자 동향 그래프"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['Consumer Sentiment'],
        mode='lines',
        name='소비자심리지수',
        line=dict(color='purple', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['Retail Sales'],
        mode='lines',
        name='소매판매',
        line=dict(color='orange', width=2),
        yaxis='y2'
    ))

    fig.update_layout(
        title='소비자 심리 및 소매판매 동향',
        xaxis_title='날짜',
        yaxis=dict(
            title='소비자심리지수',
            titlefont=dict(color='purple'),
            tickfont=dict(color='purple')
        ),
        yaxis2=dict(
            title='소매판매 (십억 달러)',
            titlefont=dict(color='orange'),
            tickfont=dict(color='orange'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        showlegend=True,
        legend=dict(x=0, y=1)
    )

    return to_html(fig, full_html=False)

def employment_trends_view():
    """고용 시장 동향 그래프"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['Nonfarm Payrolls'],
        mode='lines',
        name='비농업부문 고용',
        line=dict(color='blue', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=fred_data['date'],
        y=fred_data['JOLTS Hires'],
        mode='lines',
        name='신규 채용',
        line=dict(color='red', width=2),
        yaxis='y2'
    ))

    fig.update_layout(
        title='고용 시장 동향',
        xaxis_title='날짜',
        yaxis=dict(
            title='비농업부문 고용 (천명)',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title='신규 채용 (천명)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        showlegend=True,
        legend=dict(x=0, y=1)
    )

    return to_html(fig, full_html=False)

def economic_indicators_table_view():
    """경제 지표 현황 테이블"""
    # 숫자 포맷팅 함수
    def format_value(value, indicator):
        if indicator in ['GDP Growth Rate', 'FFTR', 'Unemployment Rate']:
            return f"{value:.1f}%"
        elif indicator in ['GDP', 'PCE', 'Personal Income', 'Durable Goods Orders', 'Retail Sales']:
            return f"${value:.1f}B"
        elif indicator in ['Nonfarm Payrolls', 'ISM Manufacturing', 'Building Permits', 'JOLTS Hires']:
            return f"{value:.1f}K"
        else:
            return f"{value:.1f}"

    # # 테이블 데이터 준비
    # events_data = []
    # indicator_columns = [col for col in fred_data.columns if col != 'date']
    
    # for column in indicator_columns:
    #     latest = fred_data[column].iloc[-1]
    #     previous = fred_data[column].iloc[-2]
        
    #     formatted_latest = format_value(latest, column)
    #     formatted_previous = format_value(previous, column)
        
    #     events_data.append([
    #         indicator_descriptions.get(column, column),
    #         column,
    #         formatted_latest,
    #         formatted_previous,
    #         release_schedule.get(column, ""),
    #         importance_levels.get(column, "")
    #     ])

    # # 중요도 순으로 정렬
    # events_data.sort(key=lambda x: (len(x[5]), x[0]), reverse=True)

    # # 테이블 생성
    # fig = go.Figure(data=[go.Table(
    #     header=dict(
    #         values=['지표명', '코드', '현재', '이전', '발표 일정', '중요도'],
    #         fill_color='royalblue',
    #         align='left',
    #         font=dict(color='white', size=12)
    #     ),
    #     cells=dict(
    #         values=list(zip(*events_data)),
    #         fill_color=[['white', '#f9f9f9'] * len(events_data)],
    #         align='left',
    #         font=dict(color=['black'], size=11),
    #         height=30
    #     )
    # )])

    # fig.update_layout(
    #     title={
    #         'text': '주요 경제 지표 현황',
    #         'y': 0.9,
    #         'x': 0.5,
    #         'xanchor': 'center',
    #         'yanchor': 'top',
    #         'font': dict(size=20)
    #     },
    #     width=1200,
    #     height=800,
    #     margin=dict(t=100, l=50, r=50, b=50)
    # )

    # return to_html(fig, full_html=False)

 
def fred_dashboard_view(request):
    """메인 대시보드 뷰"""
    if fred_data.empty:
        return render(request, "dashboard_hoseop.html", {"error_message": "데이터를 불러올 수 없습니다."})

    gdp_rates_html = gdp_and_rates_view()
    price_indicators_html = price_indicators_view()
    consumer_trends_html = consumer_trends_view()
    employment_trends_html = employment_trends_view()
    # economic_table_html = economic_indicators_table_view()


    # 템플릿에 전달
    return render(request, "dashboard_hoseop.html", {
        "gdp_rates_html": gdp_rates_html,
        "price_indicators_html": price_indicators_html,
        "consumer_trends_html": consumer_trends_html,
        "employment_trends_html": employment_trends_html,
        # "economic_table_html": economic_table_html
        })

