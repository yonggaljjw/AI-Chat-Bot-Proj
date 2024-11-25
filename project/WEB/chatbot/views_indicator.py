from django.shortcuts import render
import plotly.graph_objs as go
from plotly.io import to_json
from plotly.subplots import make_subplots
import pandas as pd
from chatbot.sql import engine


def bankrate_indicator() :
    # 데이터 불러오기
    query = """
    SELECT 
        bor 
    FROM 
        korea_base_rate
    ORDER BY time DESC 
    LIMIT 2;
    """
    recent_two_rates = pd.read_sql(query, engine)

    # 현재값과 직전값 할당
    current_value = float(recent_two_rates.iloc[0].values[0])
    previous_value = float(recent_two_rates.iloc[1].values[0])

    # 변동값 색상 결정
    change_value = current_value - previous_value
    if change_value >= 0:
        delta_color = 'red'
    else:
        delta_color = 'blue'

    # 서브플롯 생성
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])


    # 인디케이터 추가
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current_value,
        delta={'reference': previous_value, 'relative': True, 'valueformat' : '.2f', 'font' : {'color': delta_color}},
        # title={'text': variable_name, 'font': {'size': 20}, 'align': 'center'},
        number={'font': {'size': 50}},
        domain={'x': [0, 1], 'y': [0.6, 0.6]}
    ))


    # 레이아웃 설정 추가
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),  # 마진 축소
        height=180  # 전체 높이 설정
    )

    return to_json(fig)


def K_GDP_indicator() :
    # 데이터 불러오기
    query = """
    SELECT 
        GDP 
    FROM korea_index
    ORDER BY TIME desc
    LIMIT 2;
    """
    recent_two_rates = pd.read_sql(query, engine)

    # 현재값과 직전값 할당
    current_value = float(recent_two_rates.iloc[0].values[0])
    previous_value = float(recent_two_rates.iloc[1].values[0])

    # 변동값 색상 결정
    change_value = float(recent_two_rates.iloc[0].values[0])
    if change_value >= 0:
        delta_color = 'red'
    else:
        delta_color = 'blue'

    # 서브플롯 생성
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])


    # 인디케이터 추가
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current_value,
        delta={'reference': previous_value, 'relative': True, 'valueformat' : '.2f', 'font' : {'color': delta_color}},
        # title={'text': variable_name, 'font': {'size': 20}, 'align': 'center'},
        number={'font': {'size': 50}},
        domain={'x': [0, 1], 'y': [0.6, 0.6]}
    ))

    # 레이아웃 설정 추가
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),  # 마진 축소
        height=180  # 전체 높이 설정
    )

    return to_json(fig)


def K_growth_indicator() :
    # 데이터 불러오기
    query = """
    SELECT 
        경제성장률
    FROM korea_index
    ORDER BY TIME desc
    LIMIT 2;
    """
    recent_two_rates = pd.read_sql(query, engine)

    # 현재값과 직전값 할당
    current_value = float(recent_two_rates.iloc[0].values[0])
    previous_value = float(recent_two_rates.iloc[1].values[0])

    # 변동값 색상 결정
    change_value = float(recent_two_rates.iloc[0].values[0])
    if change_value >= 0:
        delta_color = 'red'
    else:
        delta_color = 'blue'

    # 서브플롯 생성
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])


    # 인디케이터 추가
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current_value,
        delta={'reference': previous_value, 'relative': True, 'valueformat' : '.2f', 'font' : {'color': delta_color}},
        # title={'text': variable_name, 'font': {'size': 20}, 'align': 'center'},
        number={'font': {'size': 50}},
        domain={'x': [0, 1], 'y': [0.6, 0.6]}
    ))

    # 레이아웃 설정 추가
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),  # 마진 축소
        height=180  # 전체 높이 설정
    )

    return to_json(fig)


def K__indicator() :
    # 데이터 불러오기
    query = """
    SELECT 
        경제성장률
    FROM korea_index
    ORDER BY TIME desc
    LIMIT 2;
    """
    recent_two_rates = pd.read_sql(query, engine)

    # 현재값과 직전값 할당
    current_value = float(recent_two_rates.iloc[0].values[0])
    previous_value = float(recent_two_rates.iloc[1].values[0])

    # 변동값 색상 결정
    change_value = float(recent_two_rates.iloc[0].values[0])
    if change_value >= 0:
        delta_color = 'red'
    else:
        delta_color = 'blue'

    # 서브플롯 생성
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])


    # 인디케이터 추가
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current_value,
        delta={'reference': previous_value, 'relative': True, 'valueformat' : '.2f', 'font' : {'color': delta_color}},
        # title={'text': variable_name, 'font': {'size': 20}, 'align': 'center'},
        number={'font': {'size': 40}},
        domain={'x': [0, 1], 'y': [0.6, 0.6]}
    ))

    # 레이아웃 설정 추가
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),  # 마진 축소
        height=180  # 전체 높이 설정
    )

    return to_json(fig)


def K_USD_indicator() :

    # 데이터 불러오기
    query = """
    SELECT 
        USD
    FROM currency_rate
    ORDER BY TIME desc
    LIMIT 2;
    """
    recent_two_rates = pd.read_sql(query, engine)

    # 현재값과 직전값 할당
    current_value = float(recent_two_rates.iloc[0].values[0])
    previous_value = float(recent_two_rates.iloc[1].values[0])

    # 변동값 색상 결정
    change_value = float(recent_two_rates.iloc[0].values[0])
    if change_value >= 0:
        delta_color = 'red'
    else:
        delta_color = 'blue'

    # 서브플롯 생성
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])


    # 인디케이터 추가
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current_value,
        delta={'reference': previous_value, 'relative': True, 'valueformat' : '.2f', 'font' : {'color': delta_color}},
        # title={'text': variable_name, 'font': {'size': 20}, 'align': 'center'},
        number={'font': {'size': 50}},
        domain={'x': [0, 1], 'y': [0.6, 0.6]}
    ))

    # 레이아웃 설정 추가
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),  # 마진 축소
        height=180  # 전체 높이 설정
    )
    
    return to_json(fig)

def K_cpi_indicator() :

    # 데이터 불러오기
    query = """
    SELECT TOTAL FROM cpi_data ORDER BY TIME DESC LIMIT 2;
    """
    recent_two_rates = pd.read_sql(query, engine)

    # 현재값과 직전값 할당
    current_value = float(recent_two_rates.iloc[0].values[0])
    previous_value = float(recent_two_rates.iloc[1].values[0])

    # 변동값 색상 결정
    change_value = float(recent_two_rates.iloc[0].values[0])
    if change_value >= 0:
        delta_color = 'red'
    else:
        delta_color = 'blue'

    # 서브플롯 생성
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])


    # 인디케이터 추가
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current_value,
        delta={'reference': previous_value, 'relative': True, 'valueformat' : '.2f', 'font' : {'color': delta_color}},
        # title={'text': variable_name, 'font': {'size': 20}, 'align': 'center'},
        number={'font': {'size': 50}},
        domain={'x': [0, 1], 'y': [0.6, 0.6]}
    ))

    # 레이아웃 설정 추가
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),  # 마진 축소
        height=180  # 전체 높이 설정
    )
    
    return to_json(fig)

def K_pce_indicator() :

    # 데이터 불러오기
    query = """
    SELECT DATA_VALUE FROM pce_data ORDER BY TIME DESC LIMIT 2;
    """
    recent_two_rates = pd.read_sql(query, engine)

    # 현재값과 직전값 할당
    current_value = float(recent_two_rates.iloc[0].values[0])
    previous_value = float(recent_two_rates.iloc[1].values[0])

    # 변동값 색상 결정
    change_value = float(recent_two_rates.iloc[0].values[0])
    if change_value >= 0:
        delta_color = 'red'
    else:
        delta_color = 'blue'

    # 서브플롯 생성
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])


    # 인디케이터 추가
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current_value,
        delta={'reference': previous_value, 'relative': True, 'valueformat' : '.2f', 'font' : {'color': delta_color}},
        # title={'text': variable_name, 'font': {'size': 20}, 'align': 'center'},
        number={'font': {'size': 50}},
        domain={'x': [0, 1], 'y': [0.6, 0.6]}
    ))

    # 레이아웃 설정 추가
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),  # 마진 축소
        height=180  # 전체 높이 설정
    )
    
    return to_json(fig)
