# pip install selenium webdriver-manager

import os
import time
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from selenium.common.exceptions import ElementClickInterceptedException
# 1. 'data' 디렉토리 생성
download_dir = os.path.join(os.getcwd(), 'data')
os.makedirs(download_dir, exist_ok=True)

# 2. ChromeDriver 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option('prefs', {
    "download.default_directory": download_dir,  # PDF 파일 다운로드 위치
    "download.prompt_for_download": False,  # 다운로드 창 띄우지 않기
    "plugins.always_open_pdf_externally": True  # PDF 미리보기 방지
})
chrome_options.add_argument("--headless")  # Headless 모드 활성화
chrome_options.add_argument("--disable-gpu")  # GPU 비활성화 (일부 환경에서는 필요)

# 3. ChromeDriver 자동 설치 및 설정
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 4. 웹페이지 접근
url = "https://pc.wooricard.com/dcpc/yh1/cct/cct11/prdntc/H1CCT211S09.do#"
driver.get(url)
wait = WebDriverWait(driver, 10)

# 크롬 화면을 축소 (줌 아웃)
driver.execute_script("document.body.style.zoom='50%'")

def download_pdf_files():
    while True:
        # 5. 현재 페이지의 모든 행 가져오기
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        time.sleep(3)
        for row in rows:
            try:
                for i in range(1, 11):
                
                    issue_status = row.find_element(By.XPATH, '//*[@id="agrmList"]/tr[{}]/td[10]'.format(i)).text
                    print(issue_status)
                    
                    if "발급가능" in issue_status:
                        # 7. 상품설명서 링크 추출 (4번째 컬럼)
                        pdf_link_element = row.find_element(By.XPATH,'//*[@id="agrmList"]/tr[{}]/td[4]//a'.format(i))
                        pdf_link = pdf_link_element.get_attribute("href")
                        print(pdf_link)

                        if pdf_link == "javascript:void(0)":
                            # 링크 클릭하여 다운로드 시도
                            pdf_link_element.click()
                            time.sleep(10)  # 다운로드 대기 시간 (필요에 따라 조정)
                        else:
                            # 파일명 추출
                            pdf_filename = pdf_link.split("/")[-1]
                            download_path = os.path.join(download_dir, pdf_filename)

                            # 8. 중복 다운로드 방지 및 PDF 파일 다운로드
                            if not os.path.exists(download_path):
                                try:
                                    print(f"다운로드 중: {pdf_filename}")
                                    urllib.request.urlretrieve(pdf_link, download_path)
                                except Exception as e:
                                    print(f"다운로드 실패: {pdf_filename}, 에러: {e}")
            
            # 9. 다음 페이지로 이동
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[em]/following-sibling::li[1]")))
                print(next_button.text)
                # JavaScript를 사용하여 클릭하기
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)  # 페이지 로딩 대기
            except Exception as e:
                print(f"Error occurred while processing row: {e}")
                continue

            
            # 9. 다음 페이지로 이동
            try:
                # 'em' 요소의 형제 'li' 요소를 선택하는 XPath
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[em]/following-sibling::li[1]")))
                
                # 스크롤을 통해 요소가 화면에 보이도록 하기
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)  # 스크롤 후 잠시 대기
                
                # JavaScript를 사용하여 클릭하기
                if next_button:
                    driver.execute_script("arguments[0].click();", next_button)
                else:
                    driver.quit()
                    print("더 이상 다음 페이지가 없습니다.")
                    return
                
                time.sleep(10)  # 페이지 로딩 대기
            except ElementClickInterceptedException as e:
                print(f"다음 페이지로 이동 실패: {e}")
            except Exception as e:
                print(f"Error occurred while processing row: {e}")
                continue




# 10. PDF 파일 다운로드 함수 실행
try:
    download_pdf_files()
finally:
    driver.quit()
    