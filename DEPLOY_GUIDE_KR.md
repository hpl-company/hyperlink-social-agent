# Hyperlink Social Agent 배포 가이드

## 1. GitHub 저장소 만들기

저장소 이름 추천: `hyperlink-social-agent`

Public 또는 Private로 만들 수 있습니다. Streamlit 계정에서 해당 저장소 접근 권한을 허용해야 합니다.

## 2. 파일 업로드

압축을 푼 뒤 폴더 자체가 아니라 내부 파일을 저장소 최상단에 업로드합니다.

정상 구조:

```
app.py
requirements.txt
README.md
DEPLOY_GUIDE_KR.md
.streamlit/config.toml
```

## 3. Streamlit 배포

- Repository: 본인계정/hyperlink-social-agent
- Branch: main
- Main file path: app.py

## 4. 첫 실행

1. Gemini API Key 입력
2. API 연결 테스트
3. 브랜드 설정 확인
4. 운영 전략 또는 콘텐츠 생성
5. 승인 큐에서 수정·승인

## 5. Instagram 자동 게시

Meta 개발자 설정이 완료되기 전에는 콘텐츠 생성·승인·CSV 내보내기 기능을 사용합니다.
자동 게시에는 프로페셔널 계정과 공식 Graph API 권한이 필요합니다.
