import json
import re
from datetime import datetime
from typing import Any

import requests
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="Hyperlink Product Intelligence", page_icon="🔗", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 3rem;}
[data-testid="stMetricValue"] {font-size: 2rem;}
.small-muted {color:#6b7280;font-size:0.9rem;}
.card {border:1px solid rgba(120,120,120,.25);border-radius:14px;padding:18px;margin-bottom:12px;}
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """
당신은 Hyperlink의 수석 커머스 MD이자 시장조사·가격·콘텐츠 전략 전문가다.
근거 없는 매출 예측이나 확정적 표현을 피하고, 제공된 상품 정보가 부족하면 명확히 한계를 표시한다.
반드시 한국어로 답하며 아래 JSON 스키마만 출력한다. 마크다운 코드블록은 사용하지 않는다.

{
  "executive_summary": "대표가 30초 안에 이해할 수 있는 상품 평가",
  "product": {"name":"", "brand":"", "category":"", "price":"", "key_features":[], "missing_information":[]},
  "target_customers": [{"segment":"", "needs":"", "purchase_moment":""}],
  "buying_points": [],
  "purchase_barriers": [],
  "channel_fit": [{"channel":"스마트스토어", "score":0, "reason":""}],
  "price_strategy": {"positioning":"", "recommended_range":"", "logic":"", "required_cost_data":[]},
  "hyper_score": {"overall":0, "marketability":0, "differentiation":0, "margin_potential":0, "content_fit":0, "live_commerce_fit":0, "confidence":0, "score_notes":""},
  "detail_page": {"headline":"", "subheadline":"", "sections":[{"title":"", "purpose":"", "copy":""}], "required_images":[]},
  "listing": {"smartstore_title":"", "seo_keywords":[]},
  "content": {"instagram_caption":"", "reels_script":"", "live_opening_script":""},
  "risks_and_checks": [],
  "next_actions": []
}

점수는 0~100의 정수다. 실제 시장 검색 데이터가 없으면 경쟁사·시장 규모를 아는 것처럼 쓰지 말고,
현재 입력만으로 판단한 가설임을 executive_summary와 score_notes에 표시한다.
"""


def fetch_page(url: str) -> dict[str, Any]:
    if not url:
        return {"ok": False, "error": "URL이 입력되지 않았습니다."}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }
    try:
        r = requests.get(url, headers=headers, timeout=18, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        title = (soup.title.string.strip() if soup.title and soup.title.string else "")
        description = ""
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta and meta.get("content"):
            description = meta.get("content", "").strip()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        return {
            "ok": True,
            "final_url": r.url,
            "status": r.status_code,
            "title": title[:500],
            "description": description[:1500],
            "text": text[:12000],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end+1])
        raise


def call_gemini(api_key: str, model: str, payload_text: str) -> dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n분석 입력:\n" + payload_text}]}],
        "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json"},
    }
    r = requests.post(url, json=body, timeout=120)
    if not r.ok:
        raise RuntimeError(f"Gemini API 오류 {r.status_code}: {r.text[:500]}")
    data = r.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Gemini 응답을 해석할 수 없습니다: {data}") from e
    return extract_json(text)


def call_openai_compatible(api_key: str, base_url: str, model: str, payload_text: str) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "분석 입력:\n" + payload_text},
        ],
        "temperature": 0.35,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(url, headers=headers, json=body, timeout=120)
    if not r.ok:
        # Some compatible providers do not support response_format.
        body.pop("response_format", None)
        r = requests.post(url, headers=headers, json=body, timeout=120)
    if not r.ok:
        raise RuntimeError(f"API 오류 {r.status_code}: {r.text[:500]}")
    text = r.json()["choices"][0]["message"]["content"]
    return extract_json(text)


def show_report(report: dict[str, Any]) -> None:
    st.success(report.get("executive_summary", "분석 완료"))
    scores = report.get("hyper_score", {})
    cols = st.columns(6)
    score_keys = [
        ("종합", "overall"), ("시장성", "marketability"), ("차별성", "differentiation"),
        ("마진 잠재력", "margin_potential"), ("콘텐츠 적합", "content_fit"), ("라이브 적합", "live_commerce_fit")
    ]
    for c, (label, key) in zip(cols, score_keys):
        c.metric(label, f"{scores.get(key, 0)}점")
    st.caption(f"AI 판단 신뢰도: {scores.get('confidence', 0)}점 · {scores.get('score_notes', '')}")

    tabs = st.tabs(["상품 진단", "판매 전략", "상세페이지", "콘텐츠", "리스크·실행"])
    with tabs[0]:
        st.subheader("상품 요약")
        st.json(report.get("product", {}), expanded=True)
        st.subheader("타깃 고객")
        st.dataframe(report.get("target_customers", []), use_container_width=True, hide_index=True)
        a, b = st.columns(2)
        with a:
            st.subheader("구매 포인트")
            for x in report.get("buying_points", []): st.write("•", x)
        with b:
            st.subheader("구매 장벽")
            for x in report.get("purchase_barriers", []): st.write("•", x)
    with tabs[1]:
        st.subheader("채널 적합도")
        st.dataframe(report.get("channel_fit", []), use_container_width=True, hide_index=True)
        st.subheader("가격 전략")
        st.json(report.get("price_strategy", {}), expanded=True)
    with tabs[2]:
        detail = report.get("detail_page", {})
        st.header(detail.get("headline", ""))
        st.subheader(detail.get("subheadline", ""))
        for section in detail.get("sections", []):
            with st.container(border=True):
                st.markdown(f"### {section.get('title','')}")
                st.caption(section.get("purpose", ""))
                st.write(section.get("copy", ""))
        st.markdown("#### 필요한 이미지")
        for x in detail.get("required_images", []): st.write("•", x)
        st.markdown("#### 상품 등록")
        st.write("**상품명:**", report.get("listing", {}).get("smartstore_title", ""))
        st.write("**SEO 키워드:**", ", ".join(report.get("listing", {}).get("seo_keywords", [])))
    with tabs[3]:
        content = report.get("content", {})
        st.markdown("#### 인스타그램")
        st.text_area("인스타 캡션", content.get("instagram_caption", ""), height=180)
        st.markdown("#### 릴스")
        st.text_area("릴스 대본", content.get("reels_script", ""), height=220)
        st.markdown("#### 라이브커머스")
        st.text_area("라이브 오프닝", content.get("live_opening_script", ""), height=180)
    with tabs[4]:
        st.subheader("리스크와 확인사항")
        for x in report.get("risks_and_checks", []): st.warning(x)
        st.subheader("다음 실행")
        for i, x in enumerate(report.get("next_actions", []), 1): st.write(f"{i}. {x}")


st.title("🔗 Hyperlink Product Intelligence")
st.caption("상품 URL과 내부 정보를 입력하면 AI MD가 판매 전략·상세페이지·콘텐츠 초안을 만듭니다.")

with st.sidebar:
    st.header("AI 연결")
    provider = st.selectbox("AI 제공사", ["Gemini", "Groq", "OpenAI-compatible"], index=0)
    api_key = st.text_input("API Key", type="password", help="키는 브라우저 세션에서만 사용하며 파일에 저장하지 않습니다.")
    if provider == "Gemini":
        model = st.text_input("모델", value="gemini-2.5-flash")
        base_url = ""
    elif provider == "Groq":
        model = st.text_input("모델", value="llama-3.3-70b-versatile")
        base_url = "https://api.groq.com/openai/v1"
    else:
        base_url = st.text_input("Base URL", value="https://api.openai.com/v1")
        model = st.text_input("모델", value="gpt-4.1-mini")
    st.info("공용 배포 시 API 키를 서버에 저장하지 말고, 사용자별로 직접 입력하게 하는 MVP 구조입니다.")

left, right = st.columns([1.1, 0.9])
with left:
    product_url = st.text_input("상품 URL", placeholder="https://...")
    product_notes = st.text_area(
        "추가 상품 정보",
        height=240,
        placeholder="상품명, 공급가, 판매 희망가, 브랜드, 소재, 사이즈, 재고, 배송 방식, 판매권한, 강점 등을 입력하세요.\nURL이 네이버 스마트스토어처럼 차단되는 경우 반드시 내용을 추가하세요.",
    )
with right:
    st.markdown("#### 분석 범위")
    st.write("• 상품·타깃·구매 포인트 진단")
    st.write("• 채널 적합도와 가격 포지셔닝")
    st.write("• HyperScore 및 판단 신뢰도")
    st.write("• 전문가형 상세페이지 구조")
    st.write("• 상품명·SEO·인스타·릴스·라이브 대본")
    st.warning("현재 MVP는 실시간 경쟁상품 검색을 별도 수행하지 않습니다. 시장 수치는 가설로 표시됩니다.")

if st.button("상품 분석 시작", type="primary", use_container_width=True):
    if not api_key:
        st.error("왼쪽 메뉴에 API Key를 입력하세요.")
        st.stop()
    if not product_url and not product_notes.strip():
        st.error("상품 URL 또는 추가 상품 정보를 입력하세요.")
        st.stop()
    with st.status("상품 정보를 수집하고 AI MD가 분석 중입니다...", expanded=True) as status:
        page = fetch_page(product_url) if product_url else {"ok": False, "error": "URL 없음"}
        if page.get("ok"):
            st.write("웹페이지 기본 정보 수집 완료")
        else:
            st.write(f"웹페이지 자동 수집 제한: {page.get('error', '알 수 없음')}")
        input_payload = {
            "analysis_time": datetime.now().isoformat(timespec="seconds"),
            "source_url": product_url,
            "web_page": page,
            "internal_product_notes": product_notes,
            "important_rule": "실시간 시장검색 결과가 없으면 추정이라고 명시하고, 수치를 지어내지 않는다.",
        }
        try:
            if provider == "Gemini":
                report = call_gemini(api_key, model, json.dumps(input_payload, ensure_ascii=False))
            else:
                report = call_openai_compatible(api_key, base_url, model, json.dumps(input_payload, ensure_ascii=False))
            st.session_state["report"] = report
            status.update(label="분석이 완료되었습니다.", state="complete")
        except Exception as e:
            status.update(label="분석 중 오류가 발생했습니다.", state="error")
            st.error(str(e))

if "report" in st.session_state:
    show_report(st.session_state["report"])
    raw = json.dumps(st.session_state["report"], ensure_ascii=False, indent=2)
    st.download_button("분석 보고서 JSON 다운로드", raw, file_name="hyperlink_product_report.json", mime="application/json")
