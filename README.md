# Hyperlink Social Agent MVP

하이퍼링크 인스타그램 운영을 위한 Streamlit 웹앱입니다.

## 주요 기능

- 브랜드 톤앤매너 저장
- 7일·14일·30일 콘텐츠 전략 및 캘린더 생성
- 피드·캐러셀·릴스·스토리 캡션 제작
- 해시태그 5개 자동 생성
- 비주얼 브리프, 릴스 대본, 캐러셀 슬라이드 구성
- 콘텐츠 승인 큐
- JSON·CSV 내보내기
- Meta Instagram Graph API를 통한 이미지 즉시 게시

## 배포

1. 이 폴더 안의 파일을 GitHub 저장소 최상단에 업로드합니다.
2. Streamlit Community Cloud에서 저장소를 연결합니다.
3. Main file path는 `app.py`로 설정합니다.
4. Deploy를 누릅니다.

## 사용

왼쪽 사이드바에 Gemini API Key를 입력합니다. 키는 앱 코드나 GitHub에 저장하지 않습니다.

## Instagram 공식 게시 준비사항

- Instagram Business 또는 Creator 계정
- 연결된 Facebook Page
- Meta Developer App
- 필요한 Instagram 콘텐츠 게시 권한
- Instagram User ID와 유효한 Access Token
- 외부에서 접근 가능한 HTTPS 이미지 URL

초기에는 콘텐츠 생성과 승인 기능부터 사용하고, Meta 앱 검수와 계정 연결이 끝난 뒤 공식 게시 기능을 활성화하는 것을 권장합니다.
