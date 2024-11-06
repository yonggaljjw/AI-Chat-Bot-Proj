# watching_word.py
import json
from wordcloud import WordCloud
from django_plotly_dash import DjangoDash  # DjangoDash로 변경
from dash import Dash,dcc, html
from dash.dependencies import Input, Output
import base64
import os
from io import BytesIO


# 절대 경로로 파일 경로 설정
file_path = os.path.join(os.path.dirname(__file__), 'topic_modeling_results.json')

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)


# 카테고리 데이터 준비
categories = list(data.keys())

# DjangoDash 애플리케이션 생성
app = Dash(__name__)

app.layout = html.Div([
    html.H1("뉴스 카테고리 선택", style={'textAlign': 'center'}),
    html.Div([
        html.Button(category, id=category, n_clicks=0, style={'margin': '5px', 'fontSize': '18px'}) for category in categories
    ], style={'textAlign': 'center'}),
    html.Div(id='wordcloud-container', style={'textAlign': 'center', 'marginTop': '20px'}),
])

# 콜백 함수
@app.callback(
    Output('wordcloud-container', 'children'),
    [Input(category, 'n_clicks') for category in categories]
)
def update_wordcloud(*args):
    clicked_category = [category for category, n_click in zip(categories, args) if n_click]
    
    if not clicked_category:
        return html.Div("카테고리를 클릭하세요.")

    category = clicked_category[-1]
    top_words = data[category]['top_words']
    word_freq = {item['word']: item['count'] for item in top_words}

    wordcloud = WordCloud(
        font_path='./NanumGothic.ttf',
        width=800,
        height=600,
        background_color='white'
    ).generate_from_frequencies(word_freq)

    img = BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode()

    links = [
        html.A(word['word'], href=word['links'][0], target="_blank", style={'padding': '5px', 'fontSize': '16px'})
        for word in top_words
    ]

    return html.Div([
        html.Img(src='data:image/png;base64,{}'.format(encoded_img), style={'width': '80%', 'height': 'auto'}),
        html.Div(links, style={'marginTop': '20px'})
    ])
