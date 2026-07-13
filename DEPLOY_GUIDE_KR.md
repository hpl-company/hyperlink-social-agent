# 설치 없이 웹으로 여는 방법

## 준비물
- GitHub 계정
- Streamlit Community Cloud 계정
- Gemini API 키

## 1. GitHub에 파일 올리기
1. GitHub에서 새 저장소를 만듭니다.
2. 이 ZIP의 압축을 풉니다.
3. `app.py`, `requirements.txt`, `.streamlit` 폴더를 저장소에 업로드합니다.

## 2. Streamlit에 배포하기
1. Streamlit Community Cloud에 GitHub 계정으로 로그인합니다.
2. Create app을 누릅니다.
3. 방금 만든 저장소와 브랜치를 선택합니다.
4. Main file path에 `app.py`를 입력합니다.
5. Deploy를 누릅니다.

## 3. 사용하기
배포가 끝나면 `https://원하는이름.streamlit.app` 형태의 주소가 생깁니다.
접속 후 왼쪽 메뉴에 Gemini API 키를 입력하고 상품 분석을 시작합니다.

## 보안 주의
- API 키를 GitHub 코드나 README에 적지 마세요.
- 현재 MVP는 사용자가 화면에 직접 키를 입력하는 방식입니다.
- 사내 공용 버전에서는 로그인, 암호화된 비밀키 저장, 사용량 제한을 추가해야 합니다.
