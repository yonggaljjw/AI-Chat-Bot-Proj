# 토픽 모델링 코드
import json
import pandas as pd
from konlpy.tag import Okt
from gensim import corpora
from gensim.models import LdaModel
import pyLDAvis.gensim_models
from datetime import datetime, timedelta
from collections import Counter

# JSON 파일 로드
with open('C:\ITStudy\Final_Project\카드 상품_naver_news.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 데이터프레임 생성
df = pd.DataFrame(data)

# 현재 날짜 가져오기
current_date = datetime.now()

# pDate를 datetime 객체로 변환
df['pDate'] = pd.to_datetime(df['pDate'])

# 최근 2일 이내의 기사만 필터링
two_days_ago = current_date - timedelta(days=2)
df_filtered = df[df['pDate'] > two_days_ago]

# 한국어 텍스트 전처리 함수
okt = Okt()
def preprocess_text(text):
    tokens = okt.nouns(text)  # 명사만 추출
    # 불용어 처리
    stop_words = set(['것', '등', '및', '약', '또', '를', '을', '이', '가', '은', '는'])
    return [word for word in tokens if len(word) > 1 and word not in stop_words]

# 텍스트 전처리 적용
df_filtered['processed_text'] = df_filtered['description'].apply(preprocess_text)

# 단어 사전 생성
dictionary = corpora.Dictionary(df_filtered['processed_text'])

# 코퍼스 생성
corpus = [dictionary.doc2bow(text) for text in df_filtered['processed_text']]

# LDA 모델 훈련 (토픽 수를 5개로 설정)
lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=5, random_state=100)

# 토픽과 주요 단어 출력
for idx, topic in lda_model.print_topics(-1):
    print(f'Topic: {idx}')
    print(f'Words: {topic}')
    print()

# 시각화 (선택사항)
vis = pyLDAvis.gensim_models.prepare(lda_model, corpus, dictionary)
pyLDAvis.save_html(vis, 'lda_visualization.html')

# 모든 문서의 단어를 하나의 리스트로 모읍니다
all_words = [word for doc in df_filtered['processed_text'] for word in doc]

# 단어의 빈도를 계산합니다
word_counts = Counter(all_words)

# 가장 빈번한 20개의 단어를 추출합니다
top_20_words = word_counts.most_common(20)

results = {
    'top_words': top_20_words,
    'topics': lda_model.print_topics(-1)
}

# 결과를 JSON 파일로 저장
with open('topic_modeling_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("결과가 topic_modeling_results.json 파일로 저장되었습니다.")