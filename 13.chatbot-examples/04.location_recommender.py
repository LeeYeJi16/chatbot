import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

st.set_page_config(page_title="이사 지역 분석기", page_icon="🏠")

st.title("🏠 이사 지역 분석기")
st.caption("Google Places API 기반 생활 편의 분석")


# -----------------------------
# 주소 → 좌표 변환
# -----------------------------
def geocode_address(address: str):
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": address,
        "key": API_KEY,
        "language": "ko",
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    if not data["results"]:
        return None

    location = data["results"][0]["geometry"]["location"]

    return {
        "lat": location["lat"],
        "lng": location["lng"],
    }


# -----------------------------
# 주변 장소 검색
# -----------------------------
def nearby_search(lat, lng, place_type, radius=1000):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": place_type,
        "key": API_KEY,
        "language": "ko",
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    return data.get("results", [])


# -----------------------------
# 점수 계산
# -----------------------------
def calculate_score(counts):
    weights = {
        "subway": 30,
        "hospital": 20,
        "supermarket": 20,
        "cafe": 10,
        "park": 10,
        "convenience_store": 10,
    }

    total = 0

    for k, v in counts.items():
        capped = min(v, 10)
        total += (capped / 10) * weights[k]

    return round(total, 1)


# -----------------------------
# UI
# -----------------------------
address = st.text_input(
    "분석할 주소를 입력하세요",
    placeholder="예: 서울 강남구 테헤란로 152",
)


if st.button("지역 분석 시작"):

    if not address:
        st.warning("주소를 입력해주세요.")
        st.stop()

    with st.spinner("지역 분석 중..."):

        geo = geocode_address(address)

        if not geo:
            st.error("주소를 찾을 수 없습니다.")
            st.stop()

        lat = geo["lat"]
        lng = geo["lng"]

        categories = {
            "subway": "subway_station",
            "hospital": "hospital",
            "supermarket": "supermarket",
            "cafe": "cafe",
            "park": "park",
            "convenience_store": "convenience_store",
        }

        results = {}

        for label, place_type in categories.items():
            places = nearby_search(lat, lng, place_type)
            results[label] = places

        counts = {
            k: len(v)
            for k, v in results.items()
        }

        score = calculate_score(counts)


    # -----------------------------
    # 결과 출력
    # -----------------------------

    st.success("분석 완료")

    st.subheader("📊 생활 편의 점수")

    st.metric("총점", f"{score} / 100")


    score_df = pd.DataFrame({
        "시설": [
            "지하철역",
            "병원",
            "마트",
            "카페",
            "공원",
            "편의점",
        ],
        "개수": [
            counts["subway"],
            counts["hospital"],
            counts["supermarket"],
            counts["cafe"],
            counts["park"],
            counts["convenience_store"],
        ]
    })

    st.dataframe(score_df, use_container_width=True)


    st.subheader("🗺️ 위치 정보")

    st.map(pd.DataFrame([
        {
            "lat": lat,
            "lon": lng,
        }
    ]))


    st.subheader("🏆 분석 결과")

    if score >= 80:
        st.write("생활 인프라가 매우 우수한 지역입니다.")

    elif score >= 60:
        st.write("생활 편의성이 좋은 지역입니다.")

    elif score >= 40:
        st.write("평균적인 생활 인프라 수준입니다.")

    else:
        st.write("생활 편의 시설이 다소 부족할 수 있습니다.")


    st.subheader("📌 주변 주요 시설")

    for category, places in results.items():

        display_name = {
            "subway": "🚇 지하철역",
            "hospital": "🏥 병원",
            "supermarket": "🛒 마트",
            "cafe": "☕ 카페",
            "park": "🌳 공원",
            "convenience_store": "🏪 편의점",
        }[category]

        with st.expander(display_name):

            if not places:
                st.write("검색 결과 없음")
                continue

            for p in places[:5]:

                name = p.get("name", "이름 없음")
                rating = p.get("rating", "평점 없음")
                vicinity = p.get("vicinity", "주소 정보 없음")

                st.write(f"**{name}**")
                st.write(f"평점: {rating}")
                st.write(f"주소: {vicinity}")
                st.divider()