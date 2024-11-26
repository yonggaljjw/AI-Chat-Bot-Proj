from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
from openai import OpenAI
import urllib.parse
import requests
from bs4 import BeautifulSoup
from chatbot.sql import engine
from opensearchpy import OpenSearch
import os
from dotenv import load_dotenv

load_dotenv()
############################################################################################################
# 여기에 오픈 서치 내용 만들기
client = OpenSearch(
    hosts = [{'host': os.getenv("OPENSEARCH_HOST"), 'port': os.getenv("OPENSEARCH_PORT")}]
)
def search_embedding(query_embedding):
    """
    주어진 임베딩에 가장 유사한 문서 검색.
    """
    index = 'korean_law_data'
    num_results=10
    field_name = "embedding_vector"  # 검색할 임베딩 필드
    try:
        body = {
            "size": num_results,
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": f"cosineSimilarity(params.query_vector, '{field_name}') + 1.0",
                        "params": {
                            "query_vector": query_embedding
                        }
                    }
                }
            }
        }

        # 검색 실행
        res = client.search(index=index, body=body)
        return res
    except Exception as e:
        print(f"Error executing search: {e}")
        return None
    
def os_output_text(query_embedding):
    BEST_SCORE_THRESHOLD = 1.7
    matched_texts = ""
    best_score = 0

    res = search_embedding(query_embedding)
    if res:
        i = 0
        for hit in res['hits']['hits']:
            score = hit['_score']
            text = hit['_source'].get('content') 
            # 임계값 이상의 점수를 가진 텍스트를 최대 5개까지 추가
            if score >= BEST_SCORE_THRESHOLD and len(text) > 30 and i < 5:
                matched_texts += text + "\n"
                i += 1
        best_score = res['hits']['hits'][0]['_score']
        return matched_texts
    else:
        print('유사 항목 없음')
############################################################################################################

def execute_query_to_dataframe(query):
    try:
        # pandas의 read_sql 함수를 사용하여 쿼리 실행 및 DataFrame 생성
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

# 쿼리 정의
query = """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, TABLE_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'team5'
"""

# 쿼리 실행 및 DataFrame 생성
result_df = execute_query_to_dataframe(query)

# 연결 종료
engine.dispose()

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text):
    if not text:
        return None
    text = str(text).replace("\n", "")
    res = openai.embeddings.create(input=[text], model="text-embedding-3-small")
    embedding = res.data[0].embedding
    return embedding

def generate_query(query):
    # 필드 정보 추출
    table_info = result_df.groupby('TABLE_NAME').apply(
        lambda x: ", ".join(x['COLUMN_NAME'] + " (" + x['DATA_TYPE'] + ", 결측값: " + x['IS_NULLABLE'] + ")")
    ).to_dict()

    # 테이블 정보 포맷팅
    table_info_str = "\n".join([f"{table}: {columns}" for table, columns in table_info.items()])

    # 프롬프트 생성
    prompt = f"The database has the following tables and fields:\n{table_info_str}\nWrite an only MySQL query for the following question: {query}"

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an excellent MySQL query creator, Only Provide MySQL Query"},
            {"role": "user", "content": prompt}
        ]
    )
    
    generated_query = response.choices[0].message.content
    generated_query = generated_query.replace("```sql","").replace("```","").strip()
    return generated_query

def get_wikipedia_content(keyword):
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        url = f'https://ko.wikipedia.org/wiki/{encoded_keyword}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('div', {'id': 'mw-content-text'})
        # print(content)
        if content:
            for unwanted in content.find_all(['script', 'style', 'sup', 'table']):
                unwanted.decompose()
            
            text = content.get_text(strip=True)
            text = ' '.join(text.split())
            
            return text[:1000]  # 컨텍스트 길이 제한
        
        return "내용을 찾을 수 없습니다."
        
    except Exception as e:
        return f"Wikipedia 검색 중 오류 발생: {str(e)}"

def answer_question_with_context(query, context=None):
    # Search for relevant documents
    search_query = generate_query(query)
    ############################################################################################################
    # 여기에 오픈 서치 내용 만들기
    embedding_qury = get_embedding(query)
    os_relevant_docs = os_output_text(embedding_qury)
    ############################################################################################################   
    relevant_docs = execute_query_to_dataframe(search_query)
    
    # 컨텍스트가 있는 경우와 없는 경우에 따라 프롬프트 구성
    context_text = f"\nAdditional context from Wikipedia:\n{context}" if context else ""
    
    prompt = f"""
    The following is a table of data extracted from an OpenSearch query:\n\n{os_relevant_docs}\n\n{relevant_docs}\n
    {context_text}\n
    Based on this data and context, provide an effective and detailed answer to the following natural language query: {query}
    
    Please follow these guidelines when answering:
    1. Provide accurate and concise answers based on both the data and Wikipedia context if available.
    2. Only mention information relevant to the question.
    3. If using Wikipedia information, integrate it naturally with the database information.
    4. Write your answer in Korean and keep it under 800 characters.
    
    Answer: """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Your name is 우대리, You are an excellent assistant proficient in data analysis"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800
    )
    return response.choices[0].message.content

def extract_keywords(text):
    """사용자 메시지에서 핵심 키워드 추출"""
    prompt = f"""
    다음 텍스트에서 Wikipedia 검색에 사용할 핵심 키워드 1개만 추출해주세요.
    긴 문장이나 설명은 제외하고 명사형 키워드만 추출해주세요.
    
    텍스트: {text}
    
    키워드:"""

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a keyword extraction expert. Extract only one main keyword in Korean."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )
    
    keyword = response.choices[0].message.content.strip()
    return keyword

def get_google_search_content(keyword):
    try:
        # 구글 검색 URL 생성
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}"
        
        # 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # 검색 결과 페이지 가져오기
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 검색 결과 추출 (구글 검색 결과의 스니펫)
        search_results = []
        for div in soup.find_all('div', class_=['VwiC3b', 'yXK7lf', 'MUxGbd', 'yDYNvb', 'lyLwlc']):
            if div.get_text(strip=True):
                search_results.append(div.get_text(strip=True))
        
        if not search_results:
            return "검색 결과를 찾을 수 없습니다."
        
        # 결과 합치기 (최대 1000자)
        combined_results = ' '.join(search_results)
        return combined_results[:1000]
        
    except requests.RequestException as e:
        return f"검색 요청 중 오류 발생: {str(e)}"
    except Exception as e:
        return f"검색 중 오류 발생: {str(e)}"



# 대시보드 내 한 줄 인사이트 제공
@csrf_exempt
def chatbot_response(request):
    # GET 요청 처리 (차트 인사이트)
    if request.method == 'GET':
        chart_id = request.GET.get('chartId')
        if chart_id:
            try:
                # OpenAI 클라이언트 초기화 및 인사이트 생성기 설정
                insight_generator = InsightGenerator(openai)
                
                # 차트 데이터 조회
                chart_data = insight_generator.get_chart_data(chart_id)
                
                if not chart_data or "No data available" in chart_data:
                    return JsonResponse({
                        'status': 'success',
                        'insight': '이 차트에 대한 데이터를 찾을 수 없습니다.'
                    })
                
                # 인사이트 생성
                insight = insight_generator.generate_chart_insight(chart_id, chart_data)
                
                return JsonResponse({
                    'status': 'success',
                    'insight': insight
                })
                
            except Exception as e:
                print(f"Error generating insight: {str(e)}")  # 디버깅용
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
    
    # POST 요청 처리 (기존 챗봇 대화)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            is_power_mode = data.get('isPowerMode', False)
            
            search_context = None
            if is_power_mode:
                keyword = extract_keywords(user_message)
                print(f"추출된 키워드: {keyword}")  # 디버깅용
                
                search_context = get_google_search_content(keyword)
                print(f"Google 검색 컨텍스트: {search_context[:100]}...")  # 디버깅용
            
            bot_response = f"우대리: {answer_question_with_context(user_message, search_context)}"
            
            return JsonResponse({
                'status': 'success',
                'response': bot_response
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'response': f'오류가 발생했습니다: {str(e)}'
            })
            
    return JsonResponse({'status': 'error'}, status=400)


class InsightGenerator:
    def __init__(self, openai_client):
        self.client = openai_client
        
    def get_chart_data(self, chart_id):
        """차트 ID에 따른 실제 데이터 조회"""
        try:
            from sqlalchemy import create_engine
            engine = create_engine('mysql+pymysql://root:0000@localhost:3306/team5')
            
            # 차트 ID별 쿼리 매핑
            query_map = {
                'gender_json': "SELECT * FROM team5.card_category_gender ORDER BY date DESC LIMIT 10",
                'card_total_sales_ladar_json': "SELECT * FROM team5.card_sales ORDER BY date DESC LIMIT 10",
                'wooricard_sales_treemap_json': "SELECT * FROM team5.woori_card ORDER BY date DESC LIMIT 10",
                'tour_servey_json': "SELECT * FROM team5.tour_survey ORDER BY date DESC LIMIT 10",
                'travel_trend_line_json': "SELECT * FROM team5.travel_trend ORDER BY date DESC LIMIT 10",
                'currency_rates_json': "SELECT * FROM team5.currency_rates ORDER BY date DESC LIMIT 10",
                'bankrate_indicator_json': "SELECT * FROM team5.bank_rate ORDER BY date DESC LIMIT 10",
                'K_GDP_indicator_json': "SELECT * FROM team5.gdp_data ORDER BY date DESC LIMIT 10",
                'K_cpi_indicator_json': "SELECT * FROM team5.cpi_data ORDER BY date DESC LIMIT 10",
                'K_pce_indicator_json': "SELECT * FROM team5.pce_data ORDER BY date DESC LIMIT 10",
                'K_USD_indicator_json': "SELECT * FROM team5.usd_rate ORDER BY date DESC LIMIT 10",
                'K_growth_indicator_json': "SELECT * FROM team5.growth_rate ORDER BY date DESC LIMIT 10",
                'economic_indicators_table_json': "SELECT * FROM team5.fred_data ORDER BY date DESC LIMIT 10",
                'cpi_card_predict_json': "SELECT * FROM team5.cpi_card_predict ORDER BY date DESC LIMIT 10"
            }
            
            if chart_id not in query_map:
                return "해당 차트의 데이터가 준비중입니다."
                
            df = pd.read_sql(query_map[chart_id], engine)
            engine.dispose()
            
            if df.empty:
                return "데이터가 없습니다."
                
            return df.to_string()
            
        except Exception as e:
            print(f"Error in get_chart_data: {str(e)}")
            return "분석 준비중입니다."
        
    def generate_chart_insight(self, chart_id, chart_data):
        """차트별 인사이트 생성"""
        # 차트별 컨텍스트 매핑
        context_map = {
            'gender_json': "성별에 따른 카드 사용 패턴",
            'card_total_sales_ladar_json': "카드사별 총 매출 현황",
            'wooricard_sales_treemap_json': "우리카드 실제 매출 구조",
            'tour_servey_json': "여행 관련 소비자 설문 결과",
            'travel_trend_line_json': "여행 트렌드 변화",
            'currency_rates_json': "주요 환율 동향",
            'bankrate_indicator_json': "금리 변동 추이",
            'K_GDP_indicator_json': "GDP 성장률 동향",
            'K_cpi_indicator_json': "소비자물가지수 변화",
            'K_pce_indicator_json': "개인소비지출 동향",
            'K_USD_indicator_json': "달러 환율 추이",
            'K_growth_indicator_json': "경제성장률 동향",
            'economic_indicators_table_json': "주요 경제지표 현황",
            'cpi_card_predict_json': "물가와 카드소비 연관성"
        }
        
        base_prompt = f"""
        다음은 {context_map.get(chart_id, '차트')}에 대한 최근 데이터입니다:
        {chart_data}
        
        다음 두 가지 분석을 수행해주세요:
        1. 데이터 변화 요약 (15자 내외):
        - read_sql에서 조회된 구체적인 데이터 변화 수치 설명
        - 눈에 띄는 패턴이 있을시 우선적으로 해당 데이터와 기간을 설명
        - 예시) "(00)기간 동안 (sql_컬럼)이 (변화율|변화 수치) 증가/감소/유지"
        
        2. 카드 개발/마케팅 관점의 시사점 (20자 내외):
        - 상품 개발시 유의점 제안
        - 상품 개발 방향
        - 마케팅 전략 제안
        
        결과는 다음 형식으로 제시:
        [변화] (분석1)
        [제안] (분석2)
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial data analyst expert in card industry."},
                    {"role": "user", "content": base_prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "분석 준비중입니다."