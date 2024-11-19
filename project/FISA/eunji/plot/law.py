from opensearchpy import OpenSearch
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}]
)


def fetch_recent_korean_law_data_v1(start_date, end_date):
    # OpenSearch 쿼리 정의
    query = {
        "size": 10,  # 최신 10개 데이터
        "sort": [
            {"start_date": {"order": "desc"}}  # 최신순 정렬
        ],
        "query": {
            "bool": {
                "must": [
                    {"range": {"start_date": {"gte": start_date}}},
                    {"range": {"end_date": {"lte": end_date}}}
                ]
            }
        }
    }

    # 데이터 검색
    response = client.search(
        index='korean_law_data',
        body=query
    )

    # 결과 처리
    results = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        results.append({
            "start_date": source.get("start_date"),
            "end_date": source.get("end_date"),
            "title": source.get("title"),
            "summary": source.get("summary"),
        })

    return results

# 함수 실행 예제
start_date = "2024-01-01"
end_date = "2024-12-31"
data = fetch_recent_korean_law_data_v1(start_date, end_date)
print(data)



def fetch_current_korean_law_data_v2():
    # 현재 시간 가져오기
    current_time = datetime.utcnow().isoformat()

    # OpenSearch 쿼리 정의
    query = {
        "size": 10,  # 최신 10개 데이터
        "sort": [
            {"start_date": {"order": "desc"}}  # 최신순 정렬
        ],
        "query": {
            "bool": {
                "must": [
                    {"range": {"start_date": {"lte": current_time}}},  # start_date <= 현재 시간
                    {"range": {"end_date": {"gte": current_time}}}  # end_date >= 현재 시간
                ]
            }
        }
    }

    # 데이터 검색
    response = client.search(
        index='korean_law_data',
        body=query
    )

    # 결과 처리
    results = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        results.append({
            "start_date": source.get("start_date"),
            "end_date": source.get("end_date"),
            "title": source.get("title"),
            "summary": source.get("summary"),
        })

    return results

# 함수 실행 예제
data = fetch_current_korean_law_data_v2()
print(data)


# views에 아래 넣기
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
def law_data_view(request):
    data = fetch_current_korean_law_data()
    page = request.GET.get('page', 1)
    paginator = Paginator(data, 5)  # 페이지당 5개씩 표시

    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        # 페이지 번호가 정수가 아닌 경우, 첫 번째 페이지로 이동
        paginated_data = paginator.page(1)
    except EmptyPage:
        # 페이지 번호가 범위를 벗어난 경우, 마지막 페이지로 이동
        paginated_data = paginator.page(paginator.num_pages)

    return render(request, 'law_data.html', {'data': paginated_data})

# html 에 아래 넣기
'''
    <h1>법률 데이터 목록</h1>
    <ul>
        {% for item in data %}
            <li>
                <strong>{{ item.title }}</strong> ({{ item.start_date }} ~ {{ item.end_date }})
                <br>
                - {{ item.summary }}
            </li>
        {% endfor %}
    </ul>

    <!-- 페이지네이션 -->
    <div class="pagination">
        <span class="step-links">
            {% if data.has_previous %}
                <a href="?page=1">&laquo; 처음</a>
                <a href="?page={{ data.previous_page_number }}">이전</a>
            {% endif %}

            <span class="current">
                페이지 {{ data.number }} / {{ data.paginator.num_pages }}
            </span>

            {% if data.has_next %}
                <a href="?page={{ data.next_page_number }}">다음</a>
                <a href="?page={{ data.paginator.num_pages }}">마지막 &raquo;</a>
            {% endif %}
        </span>
    </div>
    '''
# url에 아래 넣기
# path('law-data/', law_data_view, name='law_data'),