import json
from wordcloud import WordCloud
from django_plotly_dash import DjangoDash
from dash import dcc, html
from dash.dependencies import Input, Output
import base64
import os
from io import BytesIO
from django.conf import settings

# 절대 경로로 파일 경로 설정
file_path = os.path.join(os.path.dirname(__file__), 'topic_modeling_results.json')
font_path = os.path.join(os.path.dirname(__file__), 'NanumGothic.ttf')

# 경로 확인을 위해 출력
print("JSON file path:", file_path)
print("Font file path:", font_path)

# JSON 파일 읽기
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: JSON 파일이 존재하지 않습니다.")
    raise

# 카테고리 데이터 준비
categories = list(data.keys())

# DjangoDash 애플리케이션 생성
app = DjangoDash('wordcloud_app')

# 레이아웃 정의
app.layout = html.Div([
    html.H1("뉴스 카테고리 선택", style={'textAlign': 'center'}),
    html.Div(
        id="category-buttons",
        children=[
            html.Button(category, id={'type': 'category-button', 'index': category}, n_clicks=0, 
                        style={'padding': '10px', 'fontSize': '16px', 'margin': '5px'})
            for category in categories
        ]
    ),
    html.Div(id='wordcloud-container',style={'height':'800px','width':'100%'})  # 결과를 출력할 위치
])

# 콜백: 버튼 클릭 시 워드 클라우드 업데이트
@app.callback(
    Output('wordcloud-container', 'children'),
    [Input({'type': 'category-button', 'index': category}, 'n_clicks') for category in categories]
)
def update_wordcloud(*args):
    # 클릭된 카테고리 찾기
    clicked_category = [category for category, n_click in zip(categories, args) if n_click > 0]

    if not clicked_category:
        return html.Div("카테고리를 클릭하세요.")  # 아무 버튼도 클릭되지 않았을 때의 메시지
    
    # 마지막으로 클릭된 카테고리 사용
    category = clicked_category[-1]  
    top_words = data.get(category, {}).get('top_words', [])

    if not top_words:
        return html.Div("이 카테고리에는 단어가 없습니다.")
    
    # 워드 클라우드용 단어 빈도 계산
    word_freq = {item['word']: item['count'] for item in top_words}

    # 워드 클라우드 생성
    try:
        wordcloud = WordCloud(
            font_path=font_path,
            width=400,
            height=400,
            background_color='white'
        ).generate_from_frequencies(word_freq)
    except FileNotFoundError:
        print("Error: 폰트 파일을 찾을 수 없습니다.")
        raise

    # 이미지를 base64로 인코딩하여 클라이언트에 전달
    img = BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode()

    # 단어 링크 추가
    links = [
        html.A(word['word'], href=word['links'][0], target="_blank", style={'padding': '5px', 'fontSize': '16px'})
        for word in top_words if word.get('links')
    ]

    # 이미지와 링크를 반환
    return html.Div([
        html.Img(src='data:image/png;base64,{}'.format(encoded_img), style={'width': '80%', 'height': 'auto'}),
        html.Div(links, style={'marginTop': '20px'})
    ])
