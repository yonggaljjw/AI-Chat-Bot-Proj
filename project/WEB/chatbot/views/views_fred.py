from django.shortcuts import render
import plotly.graph_objs as go
from plotly.io import to_json, to_html
import pandas as pd
from chatbot.sql import engine


def load_fred_data_from_sql():
    try:
        # 정확히 최근 5년치 데이터만 가져오기
        query = """
        WITH MaxDate AS (
            SELECT MAX(date) as latest_date 
            FROM fred_data
        )
        SELECT * 
        FROM fred_data 
        WHERE date >= DATE_SUB((SELECT latest_date FROM MaxDate), INTERVAL 5 YEAR)
        AND date <= (SELECT latest_date FROM MaxDate)
        ORDER BY date ASC
        """
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

    return to_json(fig)

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
        xaxis_title='날짜',
        yaxis_title='변화율 (%)',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        showlegend=True,
        legend=dict(x=0, y=1)
    )

    return to_json(fig)

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

    return to_json(fig)

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

    return to_json(fig)

def economic_indicators_table_view():    
    try:
        # 정확히 최근 5년치 데이터만 가져오기
        query = """   
        WITH LatestValues AS (
            SELECT 
                date,
                FIRST_VALUE(`FFTR`) OVER (ORDER BY CASE WHEN `FFTR` IS NOT NULL THEN date END DESC) as FFTR,
                FIRST_VALUE(`GDP`) OVER (ORDER BY CASE WHEN `GDP` IS NOT NULL THEN date END DESC) as GDP,
                FIRST_VALUE(`GDP Growth Rate`) OVER (ORDER BY CASE WHEN `GDP Growth Rate` IS NOT NULL THEN date END DESC) as `GDP Growth Rate`,
                FIRST_VALUE(`PCE`) OVER (ORDER BY CASE WHEN `PCE` IS NOT NULL THEN date END DESC) as PCE,
                FIRST_VALUE(`Core PCE`) OVER (ORDER BY CASE WHEN `Core PCE` IS NOT NULL THEN date END DESC) as `Core PCE`,
                FIRST_VALUE(`CPI`) OVER (ORDER BY CASE WHEN `CPI` IS NOT NULL THEN date END DESC) as CPI,
                FIRST_VALUE(`Core CPI`) OVER (ORDER BY CASE WHEN `Core CPI` IS NOT NULL THEN date END DESC) as `Core CPI`,
                FIRST_VALUE(`Personal Income`) OVER (ORDER BY CASE WHEN `Personal Income` IS NOT NULL THEN date END DESC) as `Personal Income`,
                FIRST_VALUE(`Unemployment Rate`) OVER (ORDER BY CASE WHEN `Unemployment Rate` IS NOT NULL THEN date END DESC) as `Unemployment Rate`,
                FIRST_VALUE(`ISM Manufacturing`) OVER (ORDER BY CASE WHEN `ISM Manufacturing` IS NOT NULL THEN date END DESC) as `ISM Manufacturing`,
                FIRST_VALUE(`Durable Goods Orders`) OVER (ORDER BY CASE WHEN `Durable Goods Orders` IS NOT NULL THEN date END DESC) as `Durable Goods Orders`,
                FIRST_VALUE(`Building Permits`) OVER (ORDER BY CASE WHEN `Building Permits` IS NOT NULL THEN date END DESC) as `Building Permits`,
                FIRST_VALUE(`Retail Sales`) OVER (ORDER BY CASE WHEN `Retail Sales` IS NOT NULL THEN date END DESC) as `Retail Sales`,
                FIRST_VALUE(`Consumer Sentiment`) OVER (ORDER BY CASE WHEN `Consumer Sentiment` IS NOT NULL THEN date END DESC) as `Consumer Sentiment`,
                FIRST_VALUE(`Nonfarm Payrolls`) OVER (ORDER BY CASE WHEN `Nonfarm Payrolls` IS NOT NULL THEN date END DESC) as `Nonfarm Payrolls`,
                FIRST_VALUE(`JOLTS Hires`) OVER (ORDER BY CASE WHEN `JOLTS Hires` IS NOT NULL THEN date END DESC) as `JOLTS Hires`
            FROM team5.fred_data
            WHERE date IS NOT NULL
        ),
        SecondValues AS (
            SELECT 
                date,
                FIRST_VALUE(`FFTR`) OVER (ORDER BY CASE WHEN `FFTR` IS NOT NULL AND `FFTR` != (SELECT FFTR FROM LatestValues LIMIT 1) THEN date END DESC) as FFTR,
                FIRST_VALUE(`GDP`) OVER (ORDER BY CASE WHEN `GDP` IS NOT NULL AND `GDP` != (SELECT GDP FROM LatestValues LIMIT 1) THEN date END DESC) as GDP,
                FIRST_VALUE(`GDP Growth Rate`) OVER (ORDER BY CASE WHEN `GDP Growth Rate` IS NOT NULL AND `GDP Growth Rate` != (SELECT `GDP Growth Rate` FROM LatestValues LIMIT 1) THEN date END DESC) as `GDP Growth Rate`,
                FIRST_VALUE(`PCE`) OVER (ORDER BY CASE WHEN `PCE` IS NOT NULL AND `PCE` != (SELECT PCE FROM LatestValues LIMIT 1) THEN date END DESC) as PCE,
                FIRST_VALUE(`Core PCE`) OVER (ORDER BY CASE WHEN `Core PCE` IS NOT NULL AND `Core PCE` != (SELECT `Core PCE` FROM LatestValues LIMIT 1) THEN date END DESC) as `Core PCE`,
                FIRST_VALUE(`CPI`) OVER (ORDER BY CASE WHEN `CPI` IS NOT NULL AND `CPI` != (SELECT CPI FROM LatestValues LIMIT 1) THEN date END DESC) as CPI,
                FIRST_VALUE(`Core CPI`) OVER (ORDER BY CASE WHEN `Core CPI` IS NOT NULL AND `Core CPI` != (SELECT `Core CPI` FROM LatestValues LIMIT 1) THEN date END DESC) as `Core CPI`,
                FIRST_VALUE(`Personal Income`) OVER (ORDER BY CASE WHEN `Personal Income` IS NOT NULL AND `Personal Income` != (SELECT `Personal Income` FROM LatestValues LIMIT 1) THEN date END DESC) as `Personal Income`,
                FIRST_VALUE(`Unemployment Rate`) OVER (ORDER BY CASE WHEN `Unemployment Rate` IS NOT NULL AND `Unemployment Rate` != (SELECT `Unemployment Rate` FROM LatestValues LIMIT 1) THEN date END DESC) as `Unemployment Rate`,
                FIRST_VALUE(`ISM Manufacturing`) OVER (ORDER BY CASE WHEN `ISM Manufacturing` IS NOT NULL AND `ISM Manufacturing` != (SELECT `ISM Manufacturing` FROM LatestValues LIMIT 1) THEN date END DESC) as `ISM Manufacturing`,
                FIRST_VALUE(`Durable Goods Orders`) OVER (ORDER BY CASE WHEN `Durable Goods Orders` IS NOT NULL AND `Durable Goods Orders` != (SELECT `Durable Goods Orders` FROM LatestValues LIMIT 1) THEN date END DESC) as `Durable Goods Orders`,
                FIRST_VALUE(`Building Permits`) OVER (ORDER BY CASE WHEN `Building Permits` IS NOT NULL AND `Building Permits` != (SELECT `Building Permits` FROM LatestValues LIMIT 1) THEN date END DESC) as `Building Permits`,
                FIRST_VALUE(`Retail Sales`) OVER (ORDER BY CASE WHEN `Retail Sales` IS NOT NULL AND `Retail Sales` != (SELECT `Retail Sales` FROM LatestValues LIMIT 1) THEN date END DESC) as `Retail Sales`,
                FIRST_VALUE(`Consumer Sentiment`) OVER (ORDER BY CASE WHEN `Consumer Sentiment` IS NOT NULL AND `Consumer Sentiment` != (SELECT `Consumer Sentiment` FROM LatestValues LIMIT 1) THEN date END DESC) as `Consumer Sentiment`,
                FIRST_VALUE(`Nonfarm Payrolls`) OVER (ORDER BY CASE WHEN `Nonfarm Payrolls` IS NOT NULL AND `Nonfarm Payrolls` != (SELECT `Nonfarm Payrolls` FROM LatestValues LIMIT 1) THEN date END DESC) as `Nonfarm Payrolls`,
                FIRST_VALUE(`JOLTS Hires`) OVER (ORDER BY CASE WHEN `JOLTS Hires` IS NOT NULL AND `JOLTS Hires` != (SELECT `JOLTS Hires` FROM LatestValues LIMIT 1) THEN date END DESC) as `JOLTS Hires`
            FROM team5.fred_data
            WHERE date IS NOT NULL
        ),
        UniqueRankedData AS (
            (SELECT * FROM LatestValues LIMIT 1)
            UNION ALL
            (SELECT * FROM SecondValues LIMIT 1)
        )
        SELECT * FROM UniqueRankedData
        ORDER BY date ASC;
        """
        fred_table_data = pd.read_sql(query, engine)
        
    except Exception as e:
        print(f"데이터베이스에서 데이터를 불러오는 중 오류 발생: {str(e)}")
    
    if not fred_table_data.empty:
        """경제 지표 현황 테이블"""
        # SQL 컬럼명 -> 영문 지표명 매핑
        sql_to_eng = {
            'fftr': 'FFTR',
            'gdp': 'GDP',
            'gdp_growth_rate': 'GDP Growth Rate',
            'pce': 'PCE',
            'core_pce': 'Core PCE',
            'cpi': 'CPI',
            'core_cpi': 'Core CPI',
            'personal_income': 'Personal Income',
            'unemployment_rate': 'Unemployment Rate',
            'ism_manufacturing': 'ISM Manufacturing',
            'durable_goods_orders': 'Durable Goods Orders',
            'building_permits': 'Building Permits',
            'retail_sales': 'Retail Sales',
            'consumer_sentiment': 'Consumer Sentiment',
            'nonfarm_payrolls': 'Nonfarm Payrolls',
            'jolts_hires': 'JOLTS Hires'
        }

        # 영문 지표명 -> 한글 지표명 매핑
        eng_to_kor = {
            'FFTR': '연방기금금리',
            'GDP': '국내총생산',
            'GDP Growth Rate': 'GDP 성장률',
            'PCE': '개인소비지출',
            'Core PCE': '근원 개인소비지출',
            'CPI': '소비자물가지수',
            'Core CPI': '근원 소비자물가지수',
            'Personal Income': '개인소득',
            'Unemployment Rate': '실업률',
            'ISM Manufacturing': '제조업 고용',
            'Durable Goods Orders': '내구재 주문',
            'Building Permits': '건축허가',
            'Retail Sales': '소매판매',
            'Consumer Sentiment': '소비자심리지수',
            'Nonfarm Payrolls': '비농업부문 고용',
            'JOLTS Hires': '신규채용'
        }

        # 발표 일정 매핑
        release_schedule = {
            'FFTR': "FOMC 정례회의 후 (연 8회)",
            'GDP': "매달 마지막 주",
            'GDP Growth Rate': "GDP와 동시 발표",
            'PCE': "매월 둘째 주 금요일",
            'Core PCE': "PCE와 동시 발표",
            'CPI': "매월 15일경",
            'Core CPI': "CPI와 동시 발표",
            'Personal Income': "매월 말경",
            'Unemployment Rate': "매월 첫째 주 금요일",
            'ISM Manufacturing': "매월 2~3일경",
            'Durable Goods Orders': "매월 마지막 주",
            'Building Permits': "매월 중순경",
            'Retail Sales': "매월 중순경",
            'Consumer Sentiment': "매월 중순(잠정치)/말(확정치)",
            'Nonfarm Payrolls': "매월 첫째 주 금요일",
            'JOLTS Hires': "매월 첫째주"
        }

        # 중요도 매핑
        importance_levels = {
            'GDP': "★★★",
            'GDP Growth Rate': "★★★",
            'FFTR': "★★★",
            'CPI': "★★★",
            'Core CPI': "★★★",
            'Core PCE': "★★★",
            'PCE': "★★★",
            'Unemployment Rate': "★★★",
            'Nonfarm Payrolls': "★★★",
            'Personal Income': "★★",
            'ISM Manufacturing': "★★",
            'Durable Goods Orders': "★★",
            'Building Permits': "★★",
            'Retail Sales': "★★",
            'Consumer Sentiment': "★★",
            'JOLTS Hires': "★★"
        }

        # 숫자 포맷팅 함수
        def format_value(value, indicator):
            if pd.isna(value):
                return "N/A"
                
            if indicator in ['GDP Growth Rate', 'FFTR', 'Unemployment Rate', 'CPI', 'Core CPI', 'Core PCE']:
                return f"{value:.2f}%"
            elif indicator in ['GDP', 'PCE', 'Personal Income', 'Retail Sales']:
                return f"${value:.2f}B"
            elif indicator in ['Nonfarm Payrolls', 'ISM Manufacturing', 'Building Permits', 'JOLTS Hires']:
                return f"{value:.2f}K"
            else:
                return f"{value:.2f}"

        # 테이블 데이터 준비
        events_data = []
        
        print("DB Columns:", fred_table_data.columns.tolist())  # 디버깅용

        for col in fred_table_data.columns:
            if col != 'date':
                # SQL 컬럼명 -> 영문 지표명 -> 한글 지표명 변환
                eng_name = sql_to_eng.get(col, col)
                kor_name = eng_to_kor.get(eng_name, eng_name)
                
                if not fred_table_data[col].empty:
                    latest_val = fred_table_data[col].iloc[-1]
                    prev_val = fred_table_data[col].iloc[-2] if len(fred_table_data[col]) > 1 else None

                    # 값 포맷팅
                    latest_formatted = format_value(latest_val, eng_name)
                    prev_formatted = format_value(prev_val, eng_name)

                    events_data.append([
                        kor_name,                           # 한글 지표명
                        latest_formatted,                   # 현재 값 (포맷팅됨)
                        prev_formatted,                     # 이전 값 (포맷팅됨)
                        release_schedule.get(eng_name, ""),  # 발표 일정
                        importance_levels.get(eng_name, "★")  # 중요도
                    ])

        # 중요도 순으로 정렬
        events_data.sort(key=lambda x: (len(x[4]), x[0]), reverse=True)

        # 테이블 생성
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['지표명', '현재', '이전', '발표 일정', '중요도'],
                fill_color='rgb(0, 70, 180)',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=list(zip(*events_data)),
                fill_color=[['white', '#f5f8ff'] * len(events_data)],
                align=['left'] * 5,
                font=dict(color='black', size=11),
                height=35
            )
        )])

        fig.update_layout(
            paper_bgcolor='white',
            margin=dict(l=0, r=0, t=0, b=0)
        )

        return to_json(fig)


def fred_dashboard_view(request):
    """메인 대시보드 뷰"""
    if fred_data.empty:
        return render(request, "main.html", {"error_message": "데이터를 불러올 수 없습니다."})

    gdp_rates_json = gdp_and_rates_view()
    price_indicators_json = price_indicators_view()
    consumer_trends_json = consumer_trends_view()
    employment_trends_json = employment_trends_view()
    economic_table_json = economic_indicators_table_view()


    # 템플릿에 전달
    return render(request, "main.html", {
        "gdp_rates_json": gdp_rates_json,
        "price_indicators_json": price_indicators_json,
        "consumer_trends_json": consumer_trends_json,
        "employment_trends_json": employment_trends_json,
        "economic_table_json": economic_table_json
        })

