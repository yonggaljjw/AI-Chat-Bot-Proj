# 네이버 기사 크롤링
import urllib.request
import datetime
import json

client_id = "xaKw7jRi9oNo8orrCBYB"
client_secret = "TQtRJrhWU9"

# [CODE 1]
def getRequestUrl(url):
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)

    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            print("[%s] Url Request Success" % datetime.datetime.now())
            return response.read().decode('utf-8')
    except Exception as e:
        print(e)
        print("[%s] Error for URL : %s" % (datetime.datetime.now(), url))
        return None

# [CODE 2]
def getNaverSearch(node, srcText, start, display):
    base = "https://openapi.naver.com/v1/search"
    node = "/%s.json" % node
    parameters = "?query=%s&start=%s&display=%s" % (urllib.parse.quote(srcText), start, display)

    url = base + node + parameters
    responseDecode = getRequestUrl(url)  # [CODE 1]

    if responseDecode is None:
        return None
    else:
        return json.loads(responseDecode)

# [CODE 3]
def getPostData(post, jsonResult, cnt):
    title = post['title']
    description = post['description']
    org_link = post['originallink']
    link = post['link']

    pDate = datetime.datetime.strptime(post['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
    pDate = pDate.strftime('%Y-%m-%d %H:%M:%S')

    jsonResult.append({'cnt': cnt, 'title': title, 'description': description,
                       'org_link': org_link, 'link': org_link, 'pDate': pDate})
    return

# [CODE 0]
def main():
    node = 'news'  # 크롤링 할 대상
    categories = ['경제', '스포츠', '사회', '정치']  # 카테고리 리스트

    for category in categories:
        srcText = category
        cnt = 0
        jsonResult = []

        jsonResponse = getNaverSearch(node, srcText, 1, 100)  # [CODE 2]
        if jsonResponse is None:
            print(f"{category}에 대한 검색 결과가 없습니다.")
            continue
        
        total = jsonResponse['total']

        while (jsonResponse is not None and jsonResponse['display'] != 0):
            for post in jsonResponse['items']:
                cnt += 1
                getPostData(post, jsonResult, cnt)  # [CODE 3]

            start = jsonResponse['start'] + jsonResponse['display']
            jsonResponse = getNaverSearch(node, srcText, start, 100)  # [CODE 2]

        print('전체 검색 : %d 건' % total)

        # 각 카테고리별로 JSON 파일 저장
        with open('%s_naver_%s.json' % (srcText, node), 'w', encoding='utf8') as outfile:
            jsonFile = json.dumps(jsonResult, indent=4, sort_keys=True, ensure_ascii=False)
            outfile.write(jsonFile)

        print("가져온 데이터 : %d 건" % (cnt))
        print('%s_naver_%s.json SAVED' % (srcText, node))

if __name__ == '__main__':
    main()
