import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ------------------------------
# 파일 이름 설정
# ------------------------------
DATA_FILE = "responses.csv"
DECISIONS_FILE = "decisions.csv"
RATINGS_FILE = "ratings.csv"


# ------------------------------
# 데이터 로드/저장 함수
# ------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "timestamp", "user_id", "purpose",
        "match_mode", "group_size",
        "group_scope", "group_name",
        "self_age", "self_gender",
        "self_personality", "self_appearance",
        "self_height", "self_bmi",
        "pref_min_age", "pref_max_age",
        "pref_gender", "pref_personality",
        "pref_appearance",
        "pref_min_height", "pref_max_height",
        "pref_min_bmi", "pref_max_bmi",
        "blacklist_personality", "blacklist_appearance",
        "contact_info"
    ])


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def load_decisions():
    if os.path.exists(DECISIONS_FILE):
        return pd.read_csv(DECISIONS_FILE)
    return pd.DataFrame(columns=["timestamp", "from_user", "to_user", "decision"])


def save_decisions(df):
    df.to_csv(DECISIONS_FILE, index=False)


def load_ratings():
    if os.path.exists(RATINGS_FILE):
        return pd.read_csv(RATINGS_FILE)
    return pd.DataFrame(columns=["timestamp", "from_user", "to_user", "rating"])


def save_ratings(df):
    df.to_csv(RATINGS_FILE, index=False)


def get_user_manner_temperature(user_id: str) -> float:
    """
    매너온도 = (해당 유저에게 들어온 별점 평균) * 20
    별점이 하나도 없으면 50점으로 표시
    """
    df = load_ratings()
    if df.empty:
        return 50.0

    user_ratings = df[df["to_user"] == user_id]["rating"]
    if len(user_ratings) == 0:
        return 50.0

    return round(user_ratings.mean() * 20, 1)  # 5점 만점 → 100점 환산


def split_tags(val):
    """세미콜론으로 저장된 문자열을 리스트로 바꾸는 헬퍼 함수"""
    if pd.isna(val):
        return []
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return []
    return s.split(";")


# ------------------------------
# 매칭 점수 계산
# ------------------------------
def calc_match_score(me, other):
    """
    나(me)와 상대(other) 간의 매칭 점수 계산.
    - me, other: pandas.Series (각 사용자의 row)
    """
    score = 0.0

    # 목적이 다르면 제외
    if me["purpose"] != other["purpose"]:
        return -1

    # 그룹 필터
    if me["group_scope"] == "특정 그룹 내에서" and isinstance(me["group_name"], str) and me["group_name"].strip():
        if other["group_name"] != me["group_name"]:
            return -1

    if other["group_scope"] == "특정 그룹 내에서" and isinstance(other["group_name"], str) and other["group_name"].strip():
        if me["group_name"] != other["group_name"]:
            return -1

    # 블랙리스트(내 입장)
    my_black_p = split_tags(me["blacklist_personality"])
    my_black_a = split_tags(me["blacklist_appearance"])

    other_p = split_tags(other["self_personality"])
    other_a = other["self_appearance"]

    if any(p in my_black_p for p in other_p):
        return -1
    if other_a in my_black_a:
        return -1

    # 내가 원하는 조건 vs 상대 실제
    # 나이
    if me["pref_min_age"] <= other["self_age"] <= me["pref_max_age"]:
        score += 10
    else:
        return -1

    # 성별
    if me["pref_gender"] != "상관없음":
        if me["pref_gender"] == other["self_gender"]:
            score += 5
        else:
            return -1
    else:
        score += 3

    # 키
    if me["pref_min_height"] <= other["self_height"] <= me["pref_max_height"]:
        score += 4

    # BMI
    if me["pref_min_bmi"] <= other["self_bmi"] <= me["pref_max_bmi"]:
        score += 4

    # 성격
    my_pref_p = split_tags(me["pref_personality"])
    overlap1 = len(set(my_pref_p) & set(other_p))
    score += overlap1 * 3

    # 외모
    my_pref_a = split_tags(me["pref_appearance"])
    if other_a in my_pref_a:
        score += 3

    # 상대가 원하는 조건 vs 내 실제 (상호 매칭)
    if other["pref_min_age"] <= me["self_age"] <= other["pref_max_age"]:
        score += 8
    else:
        score -= 5

    if other["pref_gender"] != "상관없음":
        if other["pref_gender"] == me["self_gender"]:
            score += 5
        else:
            score -= 5
    else:
        score += 2

    other_pref_p = split_tags(other["pref_personality"])
    my_p = split_tags(me["self_personality"])
    overlap2 = len(set(other_pref_p) & set(my_p))
    score += overlap2 * 2

    other_pref_a = split_tags(other["pref_appearance"])
    if me["self_appearance"] in other_pref_a:
        score += 2

    # 매너온도 보너스 (둘 다 높으면 약간 플러스)
    mt_me = get_user_manner_temperature(me["user_id"])
    mt_other = get_user_manner_temperature(other["user_id"])
    score += (mt_me + mt_other) / 50.0  # 대략 최대 +4점 정도

    return score


# ------------------------------
# 설문 페이지
# ------------------------------
def register_survey():
    st.subheader("1. 기본 정보")
    user_id = st.text_input("닉네임 또는 ID (유일하게 구분 가능한 이름)", max_chars=30)

    purpose = st.selectbox("사용 목적", ["친구", "연애", "스터디", "취미", "기타"])
    match_mode = st.radio("매칭 방식", ["1:1 매칭", "다인원 매칭"])
    group_size = 2 if match_mode == "1:1 매칭" else st.slider("희망 모임 인원 (본인 포함)", 3, 10, 4)

    st.markdown("---")
    st.subheader("2. 그룹 설정 (선택)")
    group_scope = st.selectbox("매칭 범위", ["전체 공개", "특정 그룹 내에서"])
    group_name = ""
    if group_scope == "특정 그룹 내에서":
        group_name = st.text_input("그룹 이름 (예: OO고등학교, OO학원, 1학년 3반 등)", max_chars=50)

    st.markdown("---")
    st.subheader("3. 나에 대한 정보")

    col1, col2 = st.columns(2)
    with col1:
        self_age = st.number_input("나이", 10, 100, 18)
        self_gender = st.selectbox("성별", ["여성", "남성", "기타"])
        self_height = st.number_input("키 (cm)", 130, 220, 165)
        self_bmi = st.number_input("BMI (모를 경우 대략 입력)", 10.0, 40.0, 20.0, step=0.1)

    personality_options = ["내향적", "외향적", "열정적", "차분함", "유머있음", "반반"]
    appearance_options = ["강아지상", "고양이상", "여우상", "토끼상", "곰상"]

    with col2:
        self_personality = st.multiselect("본인 성격 (복수 선택 가능)", personality_options)
        self_appearance = st.selectbox("본인 외모 이미지에 가장 가까운 것", appearance_options)

    st.markdown("---")
    st.subheader("4. 내가 원하는 상대")

    col3, col4 = st.columns(2)
    with col3:
        pref_gender = st.selectbox("원하는 성별", ["상관없음", "여성", "남성"])
        pref_min_age, pref_max_age = st.slider("원하는 나이 범위", 10, 100, (16, 22))
        pref_min_height, pref_max_height = st.slider("원하는 키 범위 (cm)", 130, 220, (155, 180))
        pref_min_bmi, pref_max_bmi = st.slider("원하는 BMI 범위", 10, 40, (17, 25))

    with col4:
        pref_personality = st.multiselect("원하는 성격 (복수 선택 가능)", personality_options)
        pref_appearance = st.multiselect("선호 외모 타입", appearance_options)

    st.markdown("---")
    st.subheader("5. 블랙리스트 / 피하고 싶은 유형 (선택)")

    blacklist_personality = st.multiselect("피하고 싶은 성격", personality_options)
    blacklist_appearance = st.multiselect("피하고 싶은 외모 타입", appearance_options)

    st.info("※ 매너온도는 스스로 설정하지 않고, 이후 매칭된 사람들이 별점으로 평가한 값으로 자동 계산됩니다.")

    if st.button("설문 저장하기 / 업데이트 하기"):
        if not user_id:
            st.error("닉네임 또는 ID를 반드시 입력해 주세요.")
            return

        df = load_data()
        # 기존 user_id 응답 삭제 후 새로 저장
        df = df[df["user_id"] != user_id]

        new_row = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "purpose": purpose,
            "match_mode": match_mode,
            "group_size": group_size,
            "group_scope": group_scope,
            "group_name": group_name,
            "self_age": self_age,
            "self_gender": self_gender,
            "self_personality": ";".join(self_personality),
            "self_appearance": self_appearance,
            "self_height": self_height,
            "self_bmi": self_bmi,
            "pref_min_age": pref_min_age,
            "pref_max_age": pref_max_age,
            "pref_gender": pref_gender,
            "pref_personality": ";".join(pref_personality),
            "pref_appearance": ";".join(pref_appearance),
            "pref_min_height": pref_min_height,
            "pref_max_height": pref_max_height,
            "pref_min_bmi": pref_min_bmi,
            "pref_max_bmi": pref_max_bmi,
            "blacklist_personality": ";".join(blacklist_personality),
            "blacklist_appearance": ";".join(blacklist_appearance),
            "contact_info": ""
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("설문이 저장되었습니다! 이제 '매칭 보기' 또는 '알림' 탭을 이용해 보세요.")


# ------------------------------
# 매칭 보기 페이지
# ------------------------------
def show_match_page():
    st.subheader("매칭 결과 보기")

    user_id = st.text_input("내 닉네임 또는 ID 입력", key="match_user_id")
    max_results = st.slider("최대 몇 명까지 보고 싶나요?", 1, 20, 5)

    if st.button("매칭 찾기"):
        if not user_id:
            st.error("닉네임 또는 ID를 입력해 주세요.")
            return

        df = load_data()
        if df.empty:
            st.warning("아직 설문 데이터가 없습니다. 먼저 '설문 참여'에서 정보를 입력해 주세요.")
            return

        if user_id not in df["user_id"].values:
            st.error("해당 ID로 저장된 설문이 없습니다. 철자 또는 대소문자를 확인해 주세요.")
            return

        me = df[df["user_id"] == user_id].iloc[0]
        others = df[df["user_id"] != user_id].copy()

        if others.empty:
            st.info("아직 다른 사람이 설문에 참여하지 않았습니다.")
            return

        # 점수 계산
        scores = []
        for _, row in others.iterrows():
            s = calc_match_score(me, row)
            if s > 0:
                scores.append((row["user_id"], s))

        if not scores:
            st.info("지금 설정된 조건으로는 매칭 후보가 없습니다. 조건을 조금 완화해 보는 건 어떨까요?")
            return

        scores.sort(key=lambda x: x[1], reverse=True)
        top_ids = [u for u, _ in scores[:max_results]]

        top_df = others[others["user_id"].isin(top_ids)].copy()
        top_df["score"] = top_df["user_id"].map(dict(scores))

        decisions = load_decisions()

        st.markdown("### 나와 잘 맞는 사람들 (조건 + 매너온도 기준)")
        for _, row in top_df.sort_values("score", ascending=False).iterrows():
            partner_id = row["user_id"]
            mt = get_user_manner_temperature(partner_id)

            with st.expander(f"{partner_id} 님 (매칭 점수: {row['score']:.1f}, 매너온도: {mt}°)"):
                st.write("**사용 목적:**", row["purpose"])
                if isinstance(row["group_name"], str) and row["group_name"].strip():
                    st.write("**그룹:**", f"{row['group_name']} ({row['group_scope']})")
                else:
                    st.write("**그룹:**", row["group_scope"])

                st.write("---")
                st.write("#### 상대의 자기소개")
                st.write(f"- 나이: {row['self_age']}")
                st.write(f"- 성별: {row['self_gender']}")
                st.write(f"- 성격: {row['self_personality']}")
                st.write(f"- 외모 타입: {row['self_appearance']}")
                st.write(f"- 키: {row['self_height']} cm / BMI: {row['self_bmi']}")
                st.write(f"- 현재 매너온도: {mt}°")

                st.write("---")
                st.write("#### 상대가 원하는 이상형")
                st.write(f"- 나이 범위: {row['pref_min_age']} ~ {row['pref_max_age']}")
                st.write(f"- 성별: {row['pref_gender']}")
                st.write(f"- 선호 성격: {row['pref_personality']}")
                st.write(f"- 선호 외모: {row['pref_appearance']}")
                st.write(f"- 키 범위: {row['pref_min_height']} ~ {row['pref_max_height']} cm")
                st.write(f"- BMI 범위: {row['pref_min_bmi']} ~ {row['pref_max_bmi']}")

                st.write("---")
                st.write("### 이 사람과의 매칭 여부 선택")

                # 내 기존 결정
                dec = decisions[
                    (decisions["from_user"] == user_id) &
                    (decisions["to_user"] == partner_id)
                ]
                my_decision = dec["decision"].iloc[0] if not dec.empty else None

                if my_decision:
                    st.info(f"내 선택: **{my_decision}** (알림 탭에서 최종 매칭 여부를 확인할 수 있습니다.)")
                else:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("💚 이 사람 마음에 들어요 (수락)", key=f"accept_{partner_id}"):
                            decisions = load_decisions()
                            decisions = decisions[
                                ~(
                                    (decisions["from_user"] == user_id) &
                                    (decisions["to_user"] == partner_id)
                                )
                            ]
                            new_dec = {
                                "timestamp": datetime.now().isoformat(),
                                "from_user": user_id,
                                "to_user": partner_id,
                                "decision": "수락"
                            }
                            decisions = pd.concat([decisions, pd.DataFrame([new_dec])], ignore_index=True)
                            save_decisions(decisions)
                            st.success("수락으로 저장되었습니다. 상대방도 수락하면 알림 탭에서 최종 매칭을 확인할 수 있어요.")

                    with col_b:
                        if st.button("🙅‍♀️ 패스 (거절)", key=f"reject_{partner_id}"):
                            decisions = load_decisions()
                            decisions = decisions[
                                ~(
                                    (decisions["from_user"] == user_id) &
                                    (decisions["to_user"] == partner_id)
                                )
                            ]
                            new_dec = {
                                "timestamp": datetime.now().isoformat(),
                                "from_user": user_id,
                                "to_user": partner_id,
                                "decision": "거절"
                            }
                            decisions = pd.concat([decisions, pd.DataFrame([new_dec])], ignore_index=True)
                            save_decisions(decisions)
                            st.warning("거절로 저장되었습니다. 이 상대와는 매칭되지 않습니다.")


# ------------------------------
# 알림 / 최종 매칭 페이지
# ------------------------------
def show_notifications_page():
    st.subheader("알림 / 최종 매칭 결과 확인")

    user_id = st.text_input("내 닉네임 또는 ID 입력", key="notify_user_id")

    if st.button("알림 확인하기"):
        if not user_id:
            st.error("닉네임 또는 ID를 입력해 주세요.")
            return

        df = load_data()
        if df.empty or user_id not in df["user_id"].values:
            st.error("해당 ID로 저장된 설문이 없습니다. 먼저 '설문 참여'에서 설문을 저장해 주세요.")
            return

        decisions = load_decisions()
        ratings = load_ratings()

        # 내 매너온도 표시
        my_mt = get_user_manner_temperature(user_id)
        st.info(f"현재 내 매너온도는 **{my_mt}°** 입니다.")

        # 내 정보
        me = df[df["user_id"] == user_id].iloc[0]

        # 상호 수락한 사람 찾기
        my_accepts = decisions[
            (decisions["from_user"] == user_id) &
            (decisions["decision"] == "수락")
        ]

        mutual_ids = set()
        for _, row in my_accepts.iterrows():
            other = row["to_user"]
            cond = decisions[
                (decisions["from_user"] == other) &
                (decisions["to_user"] == user_id) &
                (decisions["decision"] == "수락")
            ]
            if not cond.empty:
                mutual_ids.add(other)

        if not mutual_ids:
            st.warning("아직 양쪽 모두 수락한 최종 매칭이 없습니다. 조금만 더 기다려 볼까요?")
            return

        st.markdown("### ✅ 최종 매칭된 사람들")
        # 내 연락처 등록/수정
        st.markdown("#### 📞 나의 연락처 등록 / 수정")
        current_contact = me["contact_info"] if isinstance(me["contact_info"], str) else ""
        new_contact = st.text_input(
            "인스타그램 ID, 이메일, 카카오톡 오픈채팅 링크 등 (선택)",
            value=current_contact,
            max_chars=100,
            key="my_contact_input"
        )
        if st.button("내 연락처 저장/업데이트"):
            df.loc[df["user_id"] == user_id, "contact_info"] = new_contact
            save_data(df)
            st.success("내 연락처가 저장되었습니다. 최종 매칭된 상대가 이 정보를 볼 수 있습니다.")

        # 다시 로드해서 최신 상태 반영
        df = load_data()

        for pid in mutual_ids:
            partner = df[df["user_id"] == pid]
            if partner.empty:
                continue
            partner = partner.iloc[0]
            partner_mt = get_user_manner_temperature(pid)
            partner_contact = partner["contact_info"] if isinstance(partner["contact_info"], str) else ""

            with st.expander(f"🎉 {pid} 님과 최종 매칭되었습니다!"):
                st.write("**사용 목적:**", partner["purpose"])
                if isinstance(partner["group_name"], str) and partner["group_name"].strip():
                    st.write("**그룹:**", f"{partner['group_name']} ({partner['group_scope']})")
                else:
                    st.write("**그룹:**", partner["group_scope"])

                st.write("---")
                st.write("#### 상대 프로필")
                st.write(f"- 나이: {partner['self_age']}")
                st.write(f"- 성별: {partner['self_gender']}")
                st.write(f"- 성격: {partner['self_personality']}")
                st.write(f"- 외모 타입: {partner['self_appearance']}")
                st.write(f"- 키: {partner['self_height']} cm / BMI: {partner['self_bmi']}")
                st.write(f"- 매너온도: {partner_mt}°")

                st.write("---")
                st.write("#### 연락처 정보")
                if partner_contact:
                    st.success(f"상대가 등록한 연락처: **{partner_contact}**")
                else:
                    st.info("상대가 아직 연락처를 등록하지 않았습니다. 나중에 다시 확인해 볼 수 있어요.")

                st.write("---")
                st.write("#### ⭐ 이 사람의 매너를 평가해 주세요 (매너온도 계산에 반영됩니다)")

                # 기존에 내가 준 별점이 있다면 불러오기
                existing_rating = ratings[
                    (ratings["from_user"] == user_id) &
                    (ratings["to_user"] == pid)
                ]
                default_rating = int(existing_rating["rating"].iloc[0]) if not existing_rating.empty else 5

                new_rating = st.slider(
                    "별점 (1점 = 별로, 5점 = 매우 좋음)",
                    1, 5, default_rating,
                    key=f"rating_{pid}"
                )

                if st.button("별점 저장", key=f"rating_save_{pid}"):
                    ratings = load_ratings()
                    # 기존 기록 삭제 후 새 기록 저장
                    ratings = ratings[
                        ~(
                            (ratings["from_user"] == user_id) &
                            (ratings["to_user"] == pid)
                        )
                    ]
                    new_row = {
                        "timestamp": datetime.now().isoformat(),
                        "from_user": user_id,
                        "to_user": pid,
                        "rating": new_rating,
                    }
                    ratings = pd.concat([ratings, pd.DataFrame([new_row])], ignore_index=True)
                    save_ratings(ratings)
                    st.success("별점이 저장되었습니다! 상대의 매너온도에 반영됩니다. (다음 새로고침 때 반영)")


# ------------------------------
# 메인 함수
# ------------------------------
def main():
    st.set_page_config(page_title="소셜 매칭 앱", page_icon="💞", layout="wide")

    st.title("💞 친구 / 연애 / 모임 매칭 앱 (Streamlit Demo)")
    st.write(
        """
        이 앱은 사용 목적과 본인/이상형 설문을 기반으로 서로 잘 맞는 사람을 찾아주는 데모입니다.
        - 사진 대신 간단한 외모 카테고리와 키/BMI만 사용합니다.
        - 학교/학원 같은 그룹을 설정하면 그 안에서만 매칭할 수 있습니다.
        - 매너온도는 직접 입력하지 않고, 최종 매칭된 사람들이 남긴 별점으로 계산됩니다.
        """
    )

    menu = st.sidebar.radio(
        "메뉴 선택",
        ["설문 참여", "매칭 보기", "알림(Notification)"]
    )

    if menu == "설문 참여":
        register_survey()
    elif menu == "매칭 보기":
        show_match_page()
    else:
        show_notifications_page()


if __name__ == "__main__":
    main()
