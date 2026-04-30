import os
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="맛집 추천 챗봇", page_icon="🍽️")
st.title("🍽️ 맛집 추천 챗봇")


def search_google_places(query: str, max_results: int = 5) -> list[dict]:
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.rating,"
            "places.userRatingCount,"
            "places.priceLevel,"
            "places.googleMapsUri,"
            "places.primaryTypeDisplayName,"
            "places.regularOpeningHours"
        ),
    }

    payload = {
        "textQuery": query,
        "languageCode": "ko",
        "regionCode": "KR",
        "maxResultCount": max_results,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()

    places = response.json().get("places", [])
    return places


def format_places_for_llm(places: list[dict]) -> str:
    if not places:
        return "검색된 맛집 정보가 없습니다."

    lines = []

    for i, place in enumerate(places, 1):
        name = place.get("displayName", {}).get("text", "이름 없음")
        address = place.get("formattedAddress", "주소 정보 없음")
        rating = place.get("rating", "평점 없음")
        review_count = place.get("userRatingCount", "리뷰 수 없음")
        price_level = place.get("priceLevel", "가격대 정보 없음")
        maps_url = place.get("googleMapsUri", "")
        category = place.get("primaryTypeDisplayName", {}).get("text", "카테고리 정보 없음")

        opening_hours = place.get("regularOpeningHours", {})
        open_now = opening_hours.get("openNow", "영업 여부 정보 없음")

        lines.append(
            f"""
{i}. {name}
- 카테고리: {category}
- 주소: {address}
- 평점: {rating}
- 리뷰 수: {review_count}
- 가격대: {price_level}
- 현재 영업 여부: {open_now}
- 지도 링크: {maps_url}
"""
        )

    return "\n".join(lines)


def answer_with_places(user_question: str, places_context: str) -> str:
    system_prompt = """
너는 맛집 추천 전문 챗봇이다.

규칙:
- 반드시 검색된 장소 정보만 근거로 답변한다.
- 사용자가 원하는 지역, 음식 종류, 분위기, 목적을 반영한다.
- 평점만 보지 말고 리뷰 수, 위치, 카테고리도 함께 고려한다.
- 정보가 부족하면 단정하지 말고 "검색 결과 기준"이라고 말한다.
- 재질문은 하지 말고, 가능한 추천을 먼저 제시한다.
- 답변은 간결하게 작성한다.

출력 형식:
### 🍽️ 추천 맛집

**1. [가게 이름]**
- 📍 위치: 위치 정보
- 💰 가격대: 예상 금액
- ⭐ 추천 이유: 검색 결과 기반 설명
- 💡 한줄평: 특징

[추천 맛집]
1. 식당명 - 추천 이유
2. 식당명 - 추천 이유
3. 식당명 - 추천 이유

[주의할 점]
영업 여부, 예약, 거리 등 확인이 필요한 점
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
사용자 질문:
{user_question}

Google Places 검색 결과:
{places_context}

위 정보를 바탕으로 맛집을 추천해줘.
""",
            },
        ],
    )

    return response.choices[0].message.content


if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("예: 강남역 근처 조용한 파스타 맛집 추천해줘")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("맛집 검색 중..."):
            try:
                search_query = f"{user_input} 맛집"
                places = search_google_places(search_query, max_results=5)
                places_context = format_places_for_llm(places)
                answer = answer_with_places(user_input, places_context)

            except Exception as e:
                answer = f"검색 중 오류가 발생했습니다: {e}"

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})