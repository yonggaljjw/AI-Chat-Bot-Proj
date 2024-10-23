- **Commit message 형식**
  ```markdown
  **전체 양식**
  Type: [#issue] 세부기능명

  - **Type**
    첫 글자는 무조건 대문자로 입력한다.
    :의 앞은 공백 없이, 뒤에는 공백 한 개를 넣는다.

  - **[#issue]**
    대괄호 안에 #issue-number 를 입력한다.
    issue가 없을 경우에는 생략.

  - **세부기능명**
    개조식 구문으로 작성한다.
    마침표는 넣지 않는다.

  **예시**
  Feat: [#12] 로그인 페이지 추가 , 회원가입 기능 추가
  Error: 상품리스트 불러오기
  Design: [#24] 메인화면 UI 변경
  Setting: src 폴더 생성

  **기능 구분 (Type)**
  **[Setting]**
  초기 세팅, 폴더 생성

  **[Feat]**
  새로운 파일 , 소스코드(기능) 추가 되었을때

  **[Modify]**
  기존에 있었던 폴더 , 파일 , 소스코드가 수정 되었을때
  (단순이름변경도 포함)

  **[Delete]**
  삭제관련 모든 것들

  **[Error]**
  기능측면에서 제대로 작동되지 않고
  에러나 버그가 발생되는 부분

  **[Fix]**
  error를 고쳐서 정상 작동 되었을때

  **[Refactor]**
  기존에 소스코드를 더 효율적으로 변경했을때
  (modify와 구분 필요)

  **[Design]**
  CSS 등 사용자 UI 디자인 변경

  **[Commit]**
  커밋 관련 수정사항을 반영하기 위한 경우 (커밋 취소 등)
  ```
- **Issue 형식**
  ```markdown
  [타입] Issue 내용 <label>

  타입: Feat, Design, Setting, Modify 에서 선택
  Issue 내용: 한글로 간결하게 작성.
  label: 해당하는 내용이 있는 경우 label 적극 사용

  ex)
  [Feat] 일정 예산 프로그레스 바
  [Feat] 나의 여행 게시물 공유
  [Design] 마이페이지 레이아웃
  [Setting] 보일러 플레이트
  [Modify] 공통 컴포넌트 파일명 수정

  라벨 작성

  BugFix : 버그 픽스 완료

  Error : 에러발생

  Need yarn install : package.json 업데이트 필요
  ```
- **Branch/ Pull Request 형식**
  **Branch 이름 형식**
  ```markdown
  feature-#이슈넘버
  ex) feature-#12
  ```
  **Pull Request 형식**
  ```markdown
  - PR 이름은 커밋 메시지 그대로
  - PR은 항상 upstream develop 브랜치로 올릴 것
  ```
- **변수/파일 & 생성자 작성 규칙**
  ```markdown
  - 변수 이름 : Camel case로 작성 (`clientLogin`)
  - 파일, 생성자 이름 : Pascal case로 작성 ( `ClientSide` )
  ```
