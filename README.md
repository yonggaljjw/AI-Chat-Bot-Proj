# 우대리(Woodarei)

🚧🚧 우리 FIS 아카데미 최종 프로젝트 🚧🚧

## 멤버
![image](https://github.com/user-attachments/assets/1d6c74fd-3abc-459d-b2ac-6b1513794758)

<table>
 <tr>
    <td align="center"><a href="https://github.com/awesome98"><img src="https://avatars.githubusercontent.com/awesome98" width="150px;" alt=""></td>
    <td align="center"><a href="https://github.com/eunchaipark"><img src="https://avatars.githubusercontent.com/eunchaipark" width="150px;" alt=""></td>
    <td align="center"><a href="https://github.com/euneun9"><img src="https://avatars.githubusercontent.com/euneun9" width="150px;" alt=""></td>
    <td align="center"><a href="https://github.com/JiyeonJeong02"><img src="https://avatars.githubusercontent.com/JiyeonJeong02" width="150px;" alt=""></td>
    <td align="center"><a href="https://github.com/yonggaljjw"><img src="https://avatars.githubusercontent.com/yonggaljjw" width="150px;" alt=""></td>
    <td align="center"><a href="https://github.com/SukbeomH"><img src="https://avatars.githubusercontent.com/SukbeomH" width="150px;" alt=""></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/awesome98"><b>👑 신호섭</b></td>
    <td align="center"><a href="https://github.com/eunchaipark"><b>박은채</b></td>
    <td align="center"><a href="https://github.com/euneun9"><b>이은지</b></td>
    <td align="center"><a href="https://github.com/JiyeonJeong02"><b>정지연</b></td>
    <td align="center"><a href="https://github.com/yonggaljjw"><b>조진원</b></td>
    <td align="center"><a href="https://github.com/SukbeomH"><b>홍석범</b></td>
  </tr>
</table>

## Manuals

### Git

- [git convention](./Documents/Manual/gitConvention.md)
- [git](./Documents/Manual/git.md)

## Project Structure

![image](https://github.com/user-attachments/assets/68344a40-8837-43da-bf9d-6a3ab9f0790a)

> [draw.io](https://app.diagrams.net/)를 이용하여 작성하였습니다.

- **Airflow**: 주기적으로 데이터를 수집하고, 전처리하는 역할을 합니다.
- **Elasticsearch**: 수집된 데이터를 저장하고, 백터화된 데이터를 저장, 검색하는 역할을 합니다.
- **Kibana**: Elasticsearch에 저장된 데이터를 시각화하는 역할을 합니다.
- **Django**: 사용자에게 데이터를 제공하고, 사용자의 요청에 따라 데이터를 Elasticsearch에서 가져와서 제공하는 역할을 합니다.
- **MySQL**: 사용자의 정보를 저장하고, Django에서 사용하는 데이터를 저장하는 역할을 합니다.

## Tech Stack

- Python 3.11
- Django 5.0
- MySQL 8.0
- Elasticsearch 7.15

---------

# 우대리
![image](https://github.com/user-attachments/assets/5062b5f9-07b0-44f5-8332-3aa8fc20830b)

## 프로젝트 소개
- 상품 개발 (및 마케팅)에 필요한 정보를 대시보드로 시각화 하며, 대시보드 내 정보를 챗봇을 통해 쉽게 이해하고 분석할 수 있도록 구현한 대직원 서비스

## 개발환경

- Front: HTML, CSS, JavaScript
- Back-end: 
  - Docker container
  - Port forwarding
  - Django
  - 제공된 API 활용
- 버전 및 이슈관리: 
  - GitHub
  - GitHub Issues
  - GitHub Project
- 협업 툴: 
  - Discord
  - Notion
  - GitHub Wiki
- 서비스 배포 환경: AWS


## 채택한 개발 기술과 브랜치 전략



## 기술 스택
- Python 3.12
- Django 5.0
- MySQL 8.0
- OpenSearch 2.18.0

## 프로젝트 구조
```
AI-Chat-Bot-Proj/
├── FISA/
│   ├── eunchai/
│   │   ├── watching_word.py
│   │   ├── another_script.py
│   │   └── ...
├── project/
│   ├── WEB/
│   │   ├── woodjango/
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   ├── asgi.py
│   │   │   ├── wsgi.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── static/
│   │   │   │   ├── css/
│   │   │   │   │   ├── style.css
│   │   │   │   └── js/
│   │   │   │       ├── script.js
│   │   │   ├── templates/
│   │   │   │   ├── index.html
│   │   │   │   └── dashboard/
│   │   │   │       ├── dashboard.html
│   │   │   └── migrations/
│   │   │       ├── __init__.py
│   │   ├── chatbot/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── manage.py
│   ├── requirements.txt
├── .gitignore
├── README.md
└── LICENSE
```

## 개발기간 및 작업관리

- 2024.10.25 ~ 2024.12.10

## 페이지별 기능
### 인증/인가 [초기화면]
- 서비스 접속 초기화면에서 회원가입 시 개인정보 조건 및 비밀번호 조건을 명시합니다.
  - 비밀번호 조건: 유사한 비밀번호, 글자수 제한 등
- 회원의 정보는 MySQL에 저장됩니다.

| 기능           | 설명               | GIF                           |
|----------------|--------------------|-------------------------------|
| 회원가입       | 개인정보와 조건 명시 | ![01 회원가입](https://github.com/user-attachments/assets/711e52c7-7062-4c42-aa40-d30d6efc3a61) |
| 로그인         | 로그인 화면        | ![02 로그인](https://github.com/user-attachments/assets/ff92dbbe-a304-45d9-bfd9-fee1b4b92f6d) |


### 대시보드 
(대시보드 1,2,3번이 용량 문제로 안올라감)

## 챗봇 기능

챗봇 아이콘을 클릭하면 챗봇 기능을 사용할 수 있습니다.  
아래는 주요 기능과 챗봇 실행 구조 및 화면 예시입니다.

---

### 📌 주요 기능
1. **질의 / 응답 기능**  
   데이터베이스로부터 데이터를 추출하여 참고 후 답변을 생성합니다.
2. **히스토리 기능**  
   모든 DB를 기반으로 대화 이력을 관리하고 저장합니다.
3. **멀티턴 기능**  
   연속적인 대화를 이해하고 맥락을 유지합니다.
4. **평가 기능**  
   사용자의 피드백을 수집해 챗봇 성능을 지속적으로 개선합니다.
5. **파워모드**  
   확장된 키워드 추출 및 웹 크롤링을 통해 심화 정보를 제공합니다.

---

### 🛠 챗봇 구성 구조
![챗봇 구조 이미지](https://github.com/user-attachments/assets/175ff579-8699-4db4-afd8-5a4cbbd3c4c2)

---

#### 💬 챗봇 실행 화면 및 히스토리 화면

| **챗봇 실행 화면**                                                                 | **챗봇 히스토리 화면**                                                         |
|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| ![챗봇 실행 화면 GIF](https://github.com/user-attachments/assets/dac23602-4c9e-4e16-bbac-5084855f10a8) | ![챗봇 히스토리 화면](https://github.com/user-attachments/assets/1de032fb-4b2a-4fd7-a329-75759601621a) |

---

챗봇은 실행 화면에서 다양한 대화 기능을 제공하며, 히스토리 화면에서는 대화 이력을 관리할 수 있습니다.
챗봇은 사용자에게 더 나은 경험을 제공하기 위해 지속적으로 업데이트됩니다.

---

## 트러블 슈팅


## 개선 목표



## 프로젝트 후기


