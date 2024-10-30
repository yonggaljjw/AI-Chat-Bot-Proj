import json
import pandas as pd
from konlpy.tag import Okt
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from gensim import corpora
from gensim.models import LdaModel
from gensim.models.coherencemodel import CoherenceModel
import pyLDAvis.lda_model
import pyLDAvis.gensim_models
from datetime import datetime, timedelta
from collections import Counter
import numpy as np  # 추가된 부분

# JSON 파일 로드
with open('C:\\ITStudy\\Final_Project\\카드 상품_naver_news.json', 'r', encoding='utf-8') as file:
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
    stop_words = set(['것', '등', '및', '약', '또', '를', '을', '이', '가', '은', '는'])
    return [word for word in tokens if len(word) > 1 and word not in stop_words]

# 텍스트 전처리 적용
df_filtered.loc[:, 'processed_text'] = df_filtered['description'].apply(preprocess_text)

# Scikit-learn LDA 모델 훈련 및 Coherence Score 계산
vectorizer = CountVectorizer(tokenizer=lambda x: x, lowercase=False)
X = vectorizer.fit_transform(df_filtered['processed_text'])
lda_model_sklearn = LatentDirichletAllocation(n_components=5, random_state=100)
lda_model_sklearn.fit(X)

# Coherence Score 계산 (Scikit-learn)
def calculate_coherence_sklearn(model, vectorizer, X):
    topic_word_dist = model.components_ / model.components_.sum(axis=1)[:, np.newaxis]
    words = vectorizer.get_feature_names_out()
    
    coherence_scores = []
    for i in range(model.n_components):
        top_words_idx = topic_word_dist[i].argsort()[-10:][::-1]  # 상위 10개 단어 인덱스
        top_words = [words[j] for j in top_words_idx]
        coherence_scores.append(top_words)
    
    return coherence_scores

coherence_score_sklearn = calculate_coherence_sklearn(lda_model_sklearn, vectorizer, X)
print(f'Scikit-learn LDA Top Words: {coherence_score_sklearn}')

# Gensim LDA 모델 훈련 및 Coherence Score 계산
dictionary = corpora.Dictionary(df_filtered['processed_text'])
corpus = [dictionary.doc2bow(text) for text in df_filtered['processed_text']]
lda_model_gensim = LdaModel(corpus=corpus, id2word=dictionary, num_topics=5, random_state=100)

# Coherence Score 계산 (Gensim)
coherence_model_gensim = CoherenceModel(model=lda_model_gensim, texts=df_filtered['processed_text'], dictionary=dictionary)
coherence_score_gensim = coherence_model_gensim.get_coherence()
print(f'Gensim LDA Coherence Score: {coherence_score_gensim}')

# 시각화 (선택사항)
vis_sklearn = pyLDAvis.lda_model.prepare(lda_model_sklearn, X, vectorizer)
pyLDAvis.save_html(vis_sklearn, 'lda_visualization_sklearn.html')

vis_gensim = pyLDAvis.gensim_models.prepare(lda_model_gensim, corpus, dictionary)
pyLDAvis.save_html(vis_gensim, 'lda_visualization_gensim.html')

# 모든 문서의 단어를 하나의 리스트로 모읍니다
all_words = [word for doc in df_filtered['processed_text'] for word in doc]

# 단어의 빈도를 계산합니다
word_counts = Counter(all_words)

# 가장 빈번한 20개의 단어를 추출합니다
top_20_words = word_counts.most_common(20)

results = {
    'top_words': top_20_words,
}

# 결과를 JSON 파일로 저장
with open('topic_modeling_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("결과가 topic_modeling_results.json 파일로 저장되었습니다.")