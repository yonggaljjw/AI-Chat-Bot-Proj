import json
from wordcloud import WordCloud
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import base64
from io import BytesIO

# JSON 파일에서 결과 로드
with open('topic_modeling_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# 카테고리 데이터 준비
categories = list(results.keys())

# Dash 애플리케이션 생성
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("뉴스 카테고리 선택", style={'textAlign': 'center'}),
    html.Div([
        html.Button(category, id=category, n_clicks=0, style={'margin': '5px', 'fontSize': '18px'}) for category in categories
    ], style={'textAlign': 'center'}),
    html.Div(id='wordcloud-container', style={'textAlign': 'center', 'marginTop': '20px'}),
])

# 콜백 함수: 클릭된 카테고리의 워드 클라우드와 링크 키워드 표시
@app.callback(
    Output('wordcloud-container', 'children'),
    [Input(category, 'n_clicks') for category in categories]
)
def update_wordcloud(*args):
    # 클릭된 카테고리 찾기
    clicked_category = [category for category, n_click in zip(categories, args) if n_click]
    
    if not clicked_category:
        return html.Div("카테고리를 클릭하세요.")

    category = clicked_category[-1]  # 마지막으로 클릭된 카테고리 선택
    top_words = results[category]['top_words']
    word_freq = {item['word']: item['count'] for item in top_words}

    # 워드 클라우드 생성 (한글 폰트 설정)
    wordcloud = WordCloud(
        font_path='C:\\ITStudy\\Final_Project\\NanumGothic.ttf',  # 올바른 경로로 수정
        width=800,
        height=600,
        background_color='white'
    ).generate_from_frequencies(word_freq)

    # 워드 클라우드를 이미지로 변환
    img = BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode()

    # URL 링크 목록 생성
    links = [
        html.A(word['word'], href=word['links'][0], target="_blank", style={'padding': '5px', 'fontSize': '16px'})
        for word in top_words
    ]

    return html.Div([
        html.Img(src='data:image/png;base64,{}'.format(encoded_img), style={'width': '80%', 'height': 'auto'}),
        html.Div(links, style={'marginTop': '20px'})
    ])

if __name__ == '__main__':
    app.run_server(debug=True)
