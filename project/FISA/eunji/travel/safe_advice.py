import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# from opensearchpy import OpenSearch, helpers
# from dotenv import load_dotenv

# load_dotenv()

# host = os.getenv("HOST")
# port = os.getenv("PORT")
# auth = (os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")) # For testing only. Don't store credentials in code.

# client = OpenSearch(
#     hosts = [{'host': host, 'port': port}],
#     http_auth = auth,
#     use_ssl = True,
#     
# )

# # 인덱스 이름
# index_name = "travel_cautions"

# # 인덱스가 없는 경우 생성하고 매핑 설정
# if not client.indices.exists(index=index_name):
#     mapping = {
#         "mappings": {
#             "properties": {
#                 "Country": {"type": "keyword"},
#                 "Travel_Caution": {"type": "keyword"},
#                 "Travel_Restriction": {"type": "keyword"},
#                 "Departure_Advisory": {"type": "keyword"},
#                 "Travel_Ban": {"type": "keyword"},
#                 "Special_Travel_Advisory": {"type": "keyword"}
#             }
#         }
#     }
#     client.indices.create(index=index_name, body=mapping)
#     print(f"Index '{index_name}' created with mapping.")
# else:
#     print(f"Index '{index_name}' already exists.")

def fetch_data():
    url = "https://www.0404.go.kr/dev/country.mofa?idx=&hash=&chkvalue=no1&stext=&group_idx="
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    advice_levels = ["여행유의", "여행자제", "출국권고", "여행금지", "특별여행주의보"]
    data = []
    countries = soup.select("ul.country_list > li")
    for country in countries:
        country_name = country.select_one("a").text.strip()
        img_tags = country.select("img")
        travel_advice = [img["alt"].strip() for img in img_tags if img.get("alt")]
        advice_flags = {level: True if level in travel_advice else False for level in advice_levels}
        advice_flags = {"Country": country_name, **advice_flags}
        data.append(advice_flags)

    # DataFrame 생성
    df = pd.DataFrame(data)

    # 새로운 컬럼명 설정
    new_columns = ["Country", "Travel_Caution", "Travel_Restriction", "Departure_Advisory", "Travel_Ban", "Special_Travel_Advisory"]
    df.columns = new_columns

    return df


# def upload_data():
#     df = fetch_data()
#     actions = [
#         {   
#             "_op_type": "index",
#             "_index": "Travel_Cautions",
#             "_source": {
#                 "Country": row["Country"],
#                 "Travel_Caution": row["Travel_Caution"],
#                 "Travel_Restriction": row["Travel_Restriction"],
#                 "Departure_Advisory": row["Departure_Advisory"],
#                 "Travel_Ban": row["Travel_Ban"],
#                 "Special_Travel_Advisory": row["Special_Travel_Advisory"]

#             }
#         }
#         for _, row in df.iterrows()
#     ]

#     print(f"삽입할 데이터 수: {len(actions)}")
    
#     if actions:
#         # helpers.bulk(es, actions)
#         helpers.bulk(client, actions)
#         print(f"{len(actions)}개의 데이터를 업로드했습니다.")
#     else:
#         print("업로드할 데이터가 없습니다.")
# CSV로 저장
output_file = "travel_advice.csv"
df = fetch_data()
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"데이터가 '{output_file}'로 저장되었습니다.")
