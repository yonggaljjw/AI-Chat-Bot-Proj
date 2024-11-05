import json
import pandas as pd
from konlpy.tag import Okt
from gensim import corpora
from gensim.models import LdaModel
from datetime import datetime, timedelta
from collections import Counter

# 한국어 텍스트 전처리 함수
okt = Okt()
def preprocess_text(text, stop_words):
    tokens = okt.nouns(text)  # 명사만 추출
    return [word for word in tokens if len(word) > 1 and word not in stop_words]

# 현재 날짜와 2일 전 날짜 설정
current_date = datetime.now()
two_days_ago = current_date - timedelta(days=2)

# 카테고리 리스트
categories = ['경제', '스포츠', '사회', '정치']
results = {}

for category in categories:
    try:
        # JSON 파일 로드
        with open(f'./{category}_naver_news.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 데이터프레임 생성
        df = pd.DataFrame(data)
        
        # pDate를 datetime 객체로 변환하고 최근 2일 이내의 기사만 필터링
        df['pDate'] = pd.to_datetime(df['pDate'])
        df_filtered = df[df['pDate'] > two_days_ago].copy()
        
        # 불용어 설정 (카테고리명 포함)
        stop_words = set(['것', '등', '및', '약', '또', '를', '을', '이', '가', '은', '는', category])
        
        # 텍스트 전처리
        df_filtered['processed_text'] = df_filtered['description'].apply(lambda x: preprocess_text(x, stop_words))
        
        # 단어 사전과 코퍼스 생성
        dictionary = corpora.Dictionary(df_filtered['processed_text'])
        corpus = [dictionary.doc2bow(text) for text in df_filtered['processed_text']]
        
        # LDA 모델 훈련
        lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=5, random_state=100)
        
        # 단어별 빈도수 집계
        all_words = [word for doc in df_filtered['processed_text'] for word in doc]
        word_counts = Counter(all_words)
        
        # 빈도수 기준으로 하위 60%와 70%에 해당하는 단어 필터링
        total_words = len(word_counts)
        sorted_word_counts = sorted(word_counts.items(), key=lambda x: x[1])
        
        # 60%와 70% 인덱스 계산
        lower_bound = int(total_words * 0.7)
        upper_bound = int(total_words * 0.8)

        # 하위 60%에서 70%의 단어 추출
        filtered_words = sorted_word_counts[lower_bound:upper_bound]

        # 하위 60%에서 70%에 해당하는 단어에서 최대 15개 단어 선택
        filtered_words = filtered_words[:15]

        # 단어별 대표 기사 링크 3개씩 수집
        top_word_links = {}
        for word, _ in filtered_words:
            word_links = []
            for i, row in df_filtered.iterrows():
                if word in row['processed_text']:
                    word_links.append(row['link'])
                if len(word_links) >= 3:  # 링크를 3개까지만 수집
                    break
            top_word_links[word] = word_links
        
        # 결과 저장
        results[category] = {
            'top_words': [{'word': word, 'count': count, 'links': top_word_links[word]} for word, count in filtered_words]
        }
    
    except FileNotFoundError:
        print(f"{category}에 대한 JSON 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"{category} 처리 중 오류 발생: {e}")

# 결과를 JSON 파일로 저장
with open('topic_modeling_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("결과가 topic_modeling_results.json 파일로 저장되었습니다.")
