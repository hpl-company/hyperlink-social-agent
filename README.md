# Hyperlink Product Intelligence — Web MVP

상품 URL과 내부 상품 정보를 입력하면 AI가 상품 진단, 판매전략, HyperScore, 상세페이지 구성, SNS·릴스·라이브 콘텐츠를 생성하는 Streamlit 웹앱입니다.

## 가장 쉬운 사용 방식

1. 이 폴더를 GitHub 저장소에 업로드합니다.
2. Streamlit Community Cloud에서 GitHub 저장소를 연결합니다.
3. 실행 파일(Main file path)로 `app.py`를 지정합니다.
4. 생성된 웹주소에 접속합니다.
5. 왼쪽 메뉴에서 Gemini를 선택하고 API 키를 입력합니다.

API 키는 앱 파일에 넣지 않아도 되며, 화면에 입력한 키는 현재 브라우저 세션에서만 사용됩니다.

## 로컬 테스트

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 권장 설정

- 제공사: Gemini
- 모델: `gemini-2.5-flash`
- 네이버 스마트스토어 등 동적·차단 페이지는 URL 수집이 제한될 수 있으므로, 상품명·가격·소재·사이즈·공급조건을 '추가 상품 정보'에 함께 입력하세요.

## 현재 MVP의 범위

- URL 기본 텍스트 수집
- AI 상품 진단
- 채널 적합도
- 가격 포지셔닝
- HyperScore
- 상세페이지 기획
- 상품명·SEO 키워드
- 인스타·릴스·라이브 대본
- JSON 보고서 다운로드

실시간 경쟁상품 검색, 이미지 자동 추출, 프로젝트 DB 저장, 쇼핑몰 자동 등록은 다음 버전에서 추가합니다.
