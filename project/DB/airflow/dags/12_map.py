from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
from shapely.geometry import shape
from bs4 import BeautifulSoup
import pandas as pd
import os
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenSearch 연결 정보
host = os.getenv("HOST")
port = os.getenv("PORT")
auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD"))

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    use_ssl=False,
    verify_certs=False
)

# GeoJSON 데이터를 로드하고 국가별 중심 좌표를 추출하는 함수
def load_geojson_and_extract_centroids():
    geojson_url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    response = requests.get(geojson_url)
    if response.status_code == 200:
        geojson_data = response.json()
        centroids = {}
        for feature in geojson_data["features"]:
            country_name = feature["properties"]["name"]  # 국가 이름
            geometry = shape(feature["geometry"])  # 경계 정보
            centroid = geometry.centroid
            centroids[country_name] = {"lat": centroid.y, "lon": centroid.x}  # 중심 좌표
        return centroids
    else:
        print(f"GeoJSON 데이터를 가져오지 못했습니다. 상태 코드: {response.status_code}")
        return None

# 좌표 데이터를 캐싱
centroids_cache = load_geojson_and_extract_centroids()

# 인덱스 설정
index_name = "travel_cautions"

def setup_index():
    if client.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists.")
        client.indices.delete(index=index_name)
        print(f"Existing index '{index_name}' deleted.")
    else:
        mapping = {
            "mappings": {
                "properties": {
                    "Country": {"type": "keyword"},
                    "Coordinates": {
                        "type": "geo_point"  # 'geo_point' 타입으로 수정
                    },
                    "Travel_Caution": {"type": "boolean"},
                    "Travel_Restriction": {"type": "boolean"},
                    "Departure_Advisory": {"type": "boolean"},
                    "Travel_Ban": {"type": "boolean"},
                    "Special_Travel_Advisory": {"type": "boolean"}
                }
            }
        }
        client.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created with mapping.")

# 여행 권고 데이터를 크롤링하는 함수
def fetch_travel_advice():
    url = "https://www.0404.go.kr/dev/country.mofa?idx=&hash=&chkvalue=no1&stext=&group_idx="
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    data = []
    countries = soup.select("ul.country_list > li")
    advice_levels = ["Travel_Caution", "Travel_Restriction", "Departure_Advisory", "Travel_Ban", "Special_Travel_Advisory"]

    for country in countries:
        country_name = country.select_one("a").text.strip()  # 한국어 국가 이름
        img_tags = country.select("img")
        travel_advice = [img["alt"].strip() for img in img_tags if img.get("alt")]
        
        # 기본적으로 모든 권고는 False로 설정
        advice_flags = {level: False for level in advice_levels}
        
        # 각 권고를 True로 설정
        if "여행자제" in travel_advice:
            advice_flags["Travel_Caution"] = True
        if "여행유의" in travel_advice:
            advice_flags["Travel_Restriction"] = True
        if "출국권고" in travel_advice:
            advice_flags["Departure_Advisory"] = True
        if "여행금지" in travel_advice:
            advice_flags["Travel_Ban"] = True
        if "특별여행권고" in travel_advice:
            advice_flags["Special_Travel_Advisory"] = True
        
        advice_flags = {"Country": country_name, **advice_flags}
        data.append(advice_flags)

    return pd.DataFrame(data)

# 데이터를 OpenSearch에 업로드하는 함수
def upload_data_with_coordinates():
    df = fetch_travel_advice()
    if not centroids_cache:
        print("좌표 데이터를 로드하지 못했습니다.")
        return

    actions = []
    for _, row in df.iterrows():
        country_name = row["Country"]
        coordinates = centroids_cache.get(country_name, {"lat": None, "lon": None})
        actions.append({
            "_op_type": "index",
            "_index": index_name,
            "_source": {
                "Country": country_name,
                "Coordinates": coordinates,
                "Travel_Caution": row["Travel_Caution"],
                "Travel_Restriction": row["Travel_Restriction"],
                "Departure_Advisory": row["Departure_Advisory"],
                "Travel_Ban": row["Travel_Ban"],
                "Special_Travel_Advisory": row["Special_Travel_Advisory"]
            }
        })
    
    if actions:
        helpers.bulk(client, actions)
        print(f"{len(actions)}개의 데이터를 업로드했습니다.")
    else:
        print("업로드할 데이터가 없습니다.")

# Airflow DAG 설정
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 11, 13),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "12_daily_travel_cautions_dag",
    default_args=default_args,
    description="Fetch and upload travel cautions daily with coordinates",
    schedule_interval="0 0 * * *",  # 매일 자정에 실행
    catchup=False,
) as dag:

    setup_index_task = PythonOperator(
        task_id="setup_index",
        python_callable=setup_index
    )

    upload_data_with_coordinates_task = PythonOperator(
        task_id="upload_data_with_coordinates",
        python_callable=upload_data_with_coordinates
    )

    setup_index_task >> upload_data_with_coordinates_task
