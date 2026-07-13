import csv
import io
import json
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Hyperlink Social Agent", page_icon="🔗", layout="wide")

DEFAULT_BRAND = {
    "brand_name": "Hyperlink",
    "instagram_id": "@hello.hyperlink",
    "brand_description": "브랜드와 시장을 연결하고, 지속 가능한 성장을 설계하는 브랜드 성장 파트너",
    "tone": "세련되고 신뢰감 있으며 절제된 기업형 톤",
    "audience": "브랜드 대표, 제조사, 유통사, 온라인 셀러, 사업 확장을 준비하는 기업",
    "pillars": ["브랜드 전략", "커머스 인사이트", "유통과 성장", "회사 이야기", "프로젝트 사례"],
    "avoid": "AI라는 표현을 전면에 내세우지 않기, 과장된 매출 보장, 근거 없는 수치",
}

if "brand" not in st.session_state:
    st.session_state.brand = DEFAULT_BRAND.copy()
if "drafts" not in st.session_state:
    st.session_state.drafts = []
if "calendar" not in st.session_state:
    st.session_state.calendar = []
if "last_error" not in st.session_state:
    st.session_state.last_error = ""


def clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return text


def gemini_generate(api_key: str, model: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
    }
    r = requests.post(url, params={"key": api_key}, json=payload, timeout=120)
    if not r.ok:
        raise RuntimeError(f"Gemini API 오류 {r.status_code}: {r.text[:600]}")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise RuntimeError(f"Gemini 응답 형식을 읽지 못했습니다: {json.dumps(data, ensure_ascii=False)[:800]}") from e


def list_gemini_models(api_key: str) -> List[str]:
    r = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": api_key},
        timeout=60,
    )
    if not r.ok:
        raise RuntimeError(f"모델 조회 오류 {r.status_code}: {r.text[:500]}")
    models = []
    for item in r.json().get("models", []):
        methods = item.get("supportedGenerationMethods", [])
        name = item.get("name", "").replace("models/", "")
        if "generateContent" in methods and ("flash" in name.lower() or "pro" in name.lower()):
            models.append(name)
    return sorted(models)


def make_strategy_prompt(brand: Dict[str, Any], goal: str, days: int, extra: str) -> str:
    return f"""
당신은 한국 기업 인스타그램을 운영하는 시니어 브랜드 전략가다.
다음 브랜드의 인스타그램 콘텐츠 전략과 {days}일 운영 캘린더를 작성하라.

브랜드명: {brand['brand_name']}
계정: {brand['instagram_id']}
브랜드 설명: {brand['brand_description']}
톤앤매너: {brand['tone']}
핵심 고객: {brand['audience']}
콘텐츠 기둥: {', '.join(brand['pillars'])}
금지/주의: {brand['avoid']}
이번 목표: {goal}
추가 요청: {extra or '없음'}

공개 문구에서는 AI라는 표현을 전면에 내세우지 마라.
현실적으로 제작 가능한 콘텐츠만 제안하고, 근거 없는 성과 보장 표현은 금지한다.

반드시 아래 JSON만 출력하라.
{{
  "strategy_summary": "3~5문장",
  "content_mix": [{{"pillar":"", "ratio":0, "reason":""}}],
  "calendar": [
    {{
      "day": 1,
      "format": "피드|릴스|캐러셀|스토리",
      "pillar": "",
      "topic": "",
      "hook": "",
      "goal": "인지|신뢰|문의|저장|공유",
      "visual_direction": "",
      "cta": ""
    }}
  ]
}}
"""


def make_post_prompt(brand: Dict[str, Any], topic: str, post_format: str, objective: str, notes: str) -> str:
    return f"""
당신은 브랜드 계정 전문 카피라이터이자 콘텐츠 디렉터다.
다음 조건으로 인스타그램 게시물 1개를 완성하라.

브랜드명: {brand['brand_name']}
브랜드 설명: {brand['brand_description']}
톤앤매너: {brand['tone']}
고객: {brand['audience']}
금지/주의: {brand['avoid']}
주제: {topic}
형식: {post_format}
목표: {objective}
추가 메모: {notes or '없음'}

공개 문구에서는 AI라는 표현을 전면에 내세우지 마라.
해시태그는 정확히 5개만 작성하라.
한국어 문장은 자연스럽고 과장 없이 전문적으로 작성하라.

반드시 아래 JSON만 출력하라.
{{
  "title": "내부 관리용 제목",
  "hook": "첫 문장",
  "caption": "줄바꿈 포함 완성 캡션",
  "hashtags": ["#Hyperlink", "#...", "#...", "#...", "#..."],
  "visual_brief": "디자인팀이나 이미지 제작 도구에 전달할 구체적인 비주얼 지시",
  "reel_script": {{
    "duration": "15초|30초|해당없음",
    "scenes": [{{"time":"0-3초", "visual":"", "onscreen_text":"", "voiceover":""}}]
  }},
  "carousel_slides": [{{"slide":1, "headline":"", "body":""}}],
  "cta": "",
  "best_posting_window": "예: 평일 오후 7~9시",
  "quality_check": ["브랜드 톤 일치", "과장 표현 없음", "CTA 명확"]
}}
"""


def parse_json_or_raise(text: str) -> Dict[str, Any]:
    try:
        return json.loads(clean_json_text(text))
    except Exception as e:
        raise RuntimeError(f"AI 응답이 올바른 JSON이 아닙니다. 원문: {text[:1000]}") from e


def publish_instagram_image(ig_user_id: str, access_token: str, image_url: str, caption: str) -> Dict[str, Any]:
    create_url = f"https://graph.facebook.com/v25.0/{ig_user_id}/media"
    create = requests.post(
        create_url,
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
        timeout=60,
    )
    if not create.ok:
        raise RuntimeError(f"미디어 컨테이너 생성 실패 {create.status_code}: {create.text[:800]}")
    creation_id = create.json().get("id")
    if not creation_id:
        raise RuntimeError(f"컨테이너 ID가 없습니다: {create.text[:800]}")

    publish_url = f"https://graph.facebook.com/v25.0/{ig_user_id}/media_publish"
    pub = requests.post(
        publish_url,
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=60,
    )
    if not pub.ok:
        raise RuntimeError(f"게시 실패 {pub.status_code}: {pub.text[:800]}")
    return pub.json()


st.title("🔗 Hyperlink Social Agent")
st.caption("브랜드 콘텐츠 기획 · 제작 · 승인 · 게시를 한곳에서 관리하는 인스타그램 운영 MVP")

with st.sidebar:
    st.header("연결 설정")
    api_key = st.text_input("Gemini API Key", type="password", help="브라우저 세션에서만 사용됩니다.")
    model_default = "gemini-2.5-flash"
    model = st.text_input("Gemini 모델", value=model_default)
    if st.button("API 연결 테스트", use_container_width=True):
        try:
            models = list_gemini_models(api_key)
            st.success(f"연결 성공 · 사용 가능 모델 {len(models)}개")
            if models:
                st.code("\n".join(models[:12]))
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.subheader("프로젝트 현황")
    st.metric("저장된 초안", len(st.session_state.drafts))
    st.metric("캘린더 항목", len(st.session_state.calendar))


tabs = st.tabs(["1. 브랜드 설정", "2. 운영 전략", "3. 콘텐츠 제작", "4. 승인 큐", "5. 공식 API 게시", "6. 내보내기"])

with tabs[0]:
    st.subheader("브랜드 기본 정보")
    c1, c2 = st.columns(2)
    with c1:
        brand_name = st.text_input("브랜드명", st.session_state.brand["brand_name"])
        instagram_id = st.text_input("인스타그램 계정", st.session_state.brand["instagram_id"])
        brand_description = st.text_area("브랜드 설명", st.session_state.brand["brand_description"], height=100)
        audience = st.text_area("핵심 고객", st.session_state.brand["audience"], height=100)
    with c2:
        tone = st.text_area("톤앤매너", st.session_state.brand["tone"], height=100)
        pillars_text = st.text_area("콘텐츠 기둥 · 쉼표로 구분", ", ".join(st.session_state.brand["pillars"]), height=100)
        avoid = st.text_area("금지 또는 주의 표현", st.session_state.brand["avoid"], height=100)

    if st.button("브랜드 설정 저장", type="primary"):
        st.session_state.brand = {
            "brand_name": brand_name.strip(),
            "instagram_id": instagram_id.strip(),
            "brand_description": brand_description.strip(),
            "tone": tone.strip(),
            "audience": audience.strip(),
            "pillars": [x.strip() for x in pillars_text.split(",") if x.strip()],
            "avoid": avoid.strip(),
        }
        st.success("브랜드 설정을 저장했습니다.")

with tabs[1]:
    st.subheader("콘텐츠 운영 전략과 캘린더 생성")
    c1, c2, c3 = st.columns([2, 1, 2])
    goal = c1.selectbox("이번 운영 목표", ["브랜드 인지도", "기업 문의 유입", "전문성 구축", "팔로워 성장", "서비스 출시 준비"])
    days = c2.selectbox("기간", [7, 14, 30], index=0)
    extra = c3.text_input("추가 요청", placeholder="예: 첫 7일은 회사 소개 중심")

    if st.button("운영 전략 생성", type="primary"):
        if not api_key:
            st.warning("왼쪽에 Gemini API Key를 입력하세요.")
        else:
            try:
                with st.spinner("전략과 캘린더를 작성하고 있습니다..."):
                    raw = gemini_generate(api_key, model, make_strategy_prompt(st.session_state.brand, goal, days, extra))
                    result = parse_json_or_raise(raw)
                st.session_state.calendar = result.get("calendar", [])
                st.success("운영 전략을 생성했습니다.")
                st.write(result.get("strategy_summary", ""))
                mix = result.get("content_mix", [])
                if mix:
                    st.dataframe(pd.DataFrame(mix), use_container_width=True, hide_index=True)
            except Exception as e:
                st.session_state.last_error = str(e)
                st.error(str(e))

    if st.session_state.calendar:
        st.markdown("#### 콘텐츠 캘린더")
        st.dataframe(pd.DataFrame(st.session_state.calendar), use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("게시물 한 개 완성하기")
    c1, c2, c3 = st.columns(3)
    topic = c1.text_input("주제", placeholder="예: 하이퍼링크가 존재하는 이유")
    post_format = c2.selectbox("형식", ["피드", "캐러셀", "릴스", "스토리"])
    objective = c3.selectbox("목표", ["인지", "신뢰", "문의", "저장", "공유"])
    notes = st.text_area("추가 메모", placeholder="예: 첫 게시물과 동일한 네이비 톤, 회사다운 문장")

    if st.button("콘텐츠 생성", type="primary"):
        if not api_key:
            st.warning("왼쪽에 Gemini API Key를 입력하세요.")
        elif not topic.strip():
            st.warning("주제를 입력하세요.")
        else:
            try:
                with st.spinner("캡션과 비주얼 기획을 만들고 있습니다..."):
                    raw = gemini_generate(api_key, model, make_post_prompt(st.session_state.brand, topic, post_format, objective, notes))
                    result = parse_json_or_raise(raw)
                result["status"] = "검토 대기"
                result["format"] = post_format
                result["objective"] = objective
                result["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.drafts.append(result)
                st.success("초안을 생성해 승인 큐에 저장했습니다.")
                st.markdown(f"### {result.get('title', topic)}")
                st.markdown(result.get("caption", ""))
                st.code(" ".join(result.get("hashtags", [])))
                st.info(result.get("visual_brief", ""))
            except Exception as e:
                st.session_state.last_error = str(e)
                st.error(str(e))

with tabs[3]:
    st.subheader("콘텐츠 승인 큐")
    if not st.session_state.drafts:
        st.info("아직 생성된 콘텐츠가 없습니다.")
    else:
        for idx, item in enumerate(st.session_state.drafts):
            with st.expander(f"{idx+1}. {item.get('title', '제목 없음')} · {item.get('status', '')}", expanded=idx == len(st.session_state.drafts)-1):
                st.caption(f"{item.get('format','')} · {item.get('objective','')} · {item.get('created_at','')}")
                caption_val = st.text_area("캡션", item.get("caption", ""), key=f"caption_{idx}", height=220)
                tags_val = st.text_input("해시태그", " ".join(item.get("hashtags", [])), key=f"tags_{idx}")
                st.markdown("**비주얼 가이드**")
                st.write(item.get("visual_brief", ""))
                if item.get("reel_script", {}).get("scenes"):
                    st.markdown("**릴스 대본**")
                    st.dataframe(pd.DataFrame(item["reel_script"]["scenes"]), use_container_width=True, hide_index=True)
                if item.get("carousel_slides"):
                    st.markdown("**캐러셀 구성**")
                    st.dataframe(pd.DataFrame(item["carousel_slides"]), use_container_width=True, hide_index=True)
                b1, b2, b3 = st.columns(3)
                if b1.button("수정 저장", key=f"save_{idx}"):
                    st.session_state.drafts[idx]["caption"] = caption_val
                    st.session_state.drafts[idx]["hashtags"] = tags_val.split()
                    st.success("수정 내용을 저장했습니다.")
                if b2.button("승인", key=f"approve_{idx}"):
                    st.session_state.drafts[idx]["caption"] = caption_val
                    st.session_state.drafts[idx]["hashtags"] = tags_val.split()
                    st.session_state.drafts[idx]["status"] = "승인 완료"
                    st.success("승인 완료")
                if b3.button("삭제", key=f"delete_{idx}"):
                    st.session_state.drafts.pop(idx)
                    st.rerun()

with tabs[4]:
    st.subheader("Instagram 공식 API로 이미지 게시")
    st.warning("공식 API 게시에는 Instagram 프로페셔널 계정, 연결된 Facebook 페이지, Meta 앱과 권한 설정이 필요합니다.")
    st.caption("이미지는 인터넷에서 직접 접근 가능한 HTTPS URL이어야 합니다. 컴퓨터의 로컬 파일 경로는 사용할 수 없습니다.")

    ig_user_id = st.text_input("Instagram User ID")
    access_token = st.text_input("Meta Access Token", type="password")
    image_url = st.text_input("공개 이미지 URL", placeholder="https://...")

    approved = [x for x in st.session_state.drafts if x.get("status") == "승인 완료"]
    if approved:
        selected_title = st.selectbox("게시할 승인 콘텐츠", [x.get("title", "제목 없음") for x in approved])
        selected = approved[[x.get("title", "제목 없음") for x in approved].index(selected_title)]
        default_caption = selected.get("caption", "") + "\n\n" + " ".join(selected.get("hashtags", []))
    else:
        selected = None
        default_caption = ""
    publish_caption = st.text_area("최종 캡션", default_caption, height=240)

    confirm = st.checkbox("공식 계정에 즉시 게시되는 것을 확인했습니다.")
    if st.button("Instagram에 지금 게시", type="primary", disabled=not confirm):
        if not all([ig_user_id.strip(), access_token.strip(), image_url.strip(), publish_caption.strip()]):
            st.warning("Instagram User ID, 토큰, 이미지 URL, 캡션을 모두 입력하세요.")
        else:
            try:
                with st.spinner("Instagram에 게시하고 있습니다..."):
                    result = publish_instagram_image(ig_user_id.strip(), access_token.strip(), image_url.strip(), publish_caption.strip())
                st.success(f"게시 완료 · Media ID: {result.get('id', '')}")
                if selected:
                    selected["status"] = "게시 완료"
            except Exception as e:
                st.error(str(e))

with tabs[5]:
    st.subheader("파일로 내보내기")
    brand_json = json.dumps(st.session_state.brand, ensure_ascii=False, indent=2)
    st.download_button("브랜드 설정 JSON", brand_json, file_name="hyperlink_brand.json", mime="application/json")

    drafts_json = json.dumps(st.session_state.drafts, ensure_ascii=False, indent=2)
    st.download_button("콘텐츠 초안 JSON", drafts_json, file_name="hyperlink_social_drafts.json", mime="application/json")

    if st.session_state.drafts:
        rows = []
        for x in st.session_state.drafts:
            rows.append({
                "title": x.get("title", ""),
                "format": x.get("format", ""),
                "objective": x.get("objective", ""),
                "status": x.get("status", ""),
                "caption": x.get("caption", ""),
                "hashtags": " ".join(x.get("hashtags", [])),
                "visual_brief": x.get("visual_brief", ""),
                "best_posting_window": x.get("best_posting_window", ""),
            })
        csv_bytes = pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")
        st.download_button("콘텐츠 초안 CSV", csv_bytes, file_name="hyperlink_social_drafts.csv", mime="text/csv")

    if st.session_state.calendar:
        cal_bytes = pd.DataFrame(st.session_state.calendar).to_csv(index=False).encode("utf-8-sig")
        st.download_button("콘텐츠 캘린더 CSV", cal_bytes, file_name="hyperlink_content_calendar.csv", mime="text/csv")

    if st.session_state.last_error:
        st.markdown("#### 최근 오류")
        st.code(st.session_state.last_error)
