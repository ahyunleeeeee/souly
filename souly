import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "responses.csv"
DECISIONS_FILE = "decisions.csv"


# ==============================
# 데이터 로드 / 저장
# ==============================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)

    cols = [
        "timestamp", "user_id", "purpose",
        "match_mode", "group_size",
        "group_scope", "group_name",
        "self_age", "self_gender",
        "self_personality", "self_appearance",
        "self_height", "self_bmi",
        "manner_temperature",
        "pref_min_age", "pref_max_age",
        "pref_gender", "pref_personality",
        "pref_appearance",
        "pref_min_height", "pref_max_height",
        "pref_min_bmi", "pref_max_bmi",
        "blacklist_personality", "blacklist_appearance",
    ]
    return pd.DataFrame(columns=cols)


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def load_decisions():
    if os.path.exists(DECISIONS_FILE):
        return pd.read_csv(DECISIONS_FILE)
    return pd.DataFrame(columns=["timestamp", "from_user", "to_user", "decision"])


def save_decisions(df):
    df.to_csv(DECISIONS_FILE, index=False)


# ==============================
# 설문 페이지
# ==============================
def register_survey():
    st.subheader("1. 기본 정보")
    user_id = st.text_input("닉네임 또는 ID (로그인용으로 사용할 이름)", max_chars=30)
    purpose = st.selectbox("사용 목적", ["친구", "연애", "스터디/프로젝트", "취미/동아리", "기타"])
    match_mode = st.radio("매칭 방식", ["1:1 매칭", "다인원 매칭"])
    group_size = 2
    if match_mode == "다인원 매칭":
        group_size = st.slider("원하는 모임 인원 (본인 포함)", 3, 10, 4)

    st.markdown("---")
    st.subheader("2. 그룹 설정 (선택)")
    group_scope = st.selectbox(
        "매칭 범위",
        ["전체 공개 (아무와 매칭 가능)", "학교/학원 등 특정 그룹 내에서만 매칭"],
    )
    group_name = ""
    if group_scope != "전체 공개 (아무와 매칭 가능)":
        group_name = st.text_input("그룹 이름 (예: OO고등학교, OO학원, 1학년 3반 등)", max_chars=50)

    st.markdown("---")
    st.subheader("3. 나에 대한 정보 (Self)")
    col1, col2 = st.columns(2)
    with col1:
        self_age = st.number_input("나이", min_value=10, max_value=100, value=18, step=1)
        self_gender = st.selectbox("성별", ["여성", "남성", "기타/말하고 싶지 않음"])
        self_height = st.number_input("키 (cm)", min_value=120, max_value=220, value=165, step=1)
        self_bmi = st.number_input(
            "BMI (모를 경우 대략 입력 가능)",
            min_value=10.0, max_value=40.0, value=20.0, step=0.1,
        )
    with col2:
        personality_options = ["외향적", "내향적", "반반", "차분함", "열정적", "잘 모름"]
        self_personality = st.multiselect("본인의 성격 (복수 선택 가능)", personality_options)
        appearance_options = ["강아지상", "고양이상", "여우상", "토끼상", "곰상", "상관없음/모름"]
        self_appearance = st.selectbox("본인의 외모 이미지에 가장 가까운 것", appearance_options)
        manner_temperature = st.slider(
            "매너 온도 (다른 사람 평가 기반, 임시로 스스로 예상치 입력)",
            0, 100, 50
        )

    st.markdown("---")
    st.subheader("4. 내가 원하는 상대 (Preference)")
    col3, col4 = st.columns(2)
    with col3:
        pref_gender = st.selectbox("원하는 상대 성별", ["상관없음", "여성", "남성", "기타"])
        pref_min_age, pref_max_age = st.slider("원하는 나이 범위", 10, 100, (16, 22))
        pref_min_height, pref_max_height = st.slider("원하는 키 범위 (cm)", 120, 220, (155, 185))
        pref_min_bmi, pref_max_bmi = st.slider("원하는 BMI 범위", 10, 40, (17, 25))
    with col4:
        pref_personality = st.multiselect("원하는 상대 성격", personality_options)
        pref_appearance = st.multiselect("선호하는 외모 타입", appearance_options)

    st.markdown("---")
    st.subheader("5. 블랙리스트 / 매칭 원치 않는 유형 (선택)")
    blacklist_personality = st.multiselect("피하고 싶은 성격 유형", personality_options)
    blacklist_appearance = st.multiselect("피하고 싶은 외모 유형", appearance_options)

    submitted = st.button("설문 저장하기 / 업데이트 하기")
    if submitted:
        if not user_id:
            st.error("닉네임 또는 ID를 반드시 입력해 주세요.")
            return

        df = load_data()

        # 기존 응답이 있으면 덮어쓰기
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
            "manner_temperature": manner_temperature,
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
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("설문이 저장되었습니다! 이제 '매칭 보기' 탭에서 결과를 확인해 보세요.")


# ==============================
# 매칭 점수 계산
# ==============================
def calc_match_score(me, other):
    score = 0.0

    # 0. 기본 필터: 목적이 다르면 제외
    if me["purpose"] != other["purpose"]:
        return -1

    # 1. 그룹 필터
    if me["group_scope"] != "전체 공개 (아무와 매칭 가능)" and me["group_name"]:
        # 나는 특정 그룹만 원함 -> 상대도 같은 그룹이어야 함
        if other["group_name"] != me["group_name"]:
            return -1
    if other["group_scope"] != "전체 공개 (아무와 매칭 가능)" and other["group_name"]:
        # 상대가 특정 그룹만 원함 -> 나도 같은 그룹이어야 함
        if me["group_name"] != other["group_name"]:
            return -1

    # 2. 블랙리스트 필터 (내 입장에서)
    my_black_personality = str(me["blacklist_personality"]).split(";") if me["blacklist_personality"] else []
    my_black_appearance = str(me["blacklist_appearance"]).split(";") if me["blacklist_appearance"] else []

    other_personality = str(other["self_personality"]).split(";") if other["self_personality"] else []
    other_appearance = other["self_appearance"]

    if any(p for p in other_personality if p in my_black_personality):
        return -1
    if other_appearance in my_black_appearance:
        return -1

    # 3. 내가 원하는 조건 vs 상대 실제
    # 나이
    if me["pref_min_age"] <= other["self_age"] <= me["pref_max_age"]:
        score += 10
    else:
        # 범위 밖이면 점수 크게 깎음 (그냥 탈락 처리)
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
    my_pref_personality = str(me["pref_personality"]).split(";") if me["pref_personality"] else []
    overlap_p = len(set(my_pref_personality) & set(other_personality))
    score += overlap_p * 3

    # 외모 타입
    my_pref_appearance = str(me["pref_appearance"]).split(";") if me["pref_appearance"] else []
    if other_appearance in my_pref_appearance:
        score += 3

    # 4. 상대가 원하는 조건 vs 내 실제 (상호 매칭)
    # 나이
    if other["pref_min_age"] <= me["self_age"] <= other["pref_max_age"]:
        score += 8
    else:
        score -= 5

    # 성별
    if other["pref_gender"] != "상관없음":
        if other["pref_gender"] == me["self_gender"]:
            score += 5
        else:
            score -= 5
    else:
        score += 2

    # 성격
    other_pref_personality = str(other["pref_personality"]).split(";") if other["pref_personality"] else []
    my_personality = str(me["self_personality"]).split(";") if me["self_personality"] else []
    overlap_p2 = len(set(other_pref_personality) & set(my_personality))
    score += overlap_p2 * 2

    # 외모
    other_pref_appearance = str(other["pref_appearance"]).split(";") if other["pref_appearance"] else []
    if me["self_appearance"] in other_pref_appearance:
        score += 2

    # 5. 매너온도 보너스 (둘 다 높을수록 좋음)
    score += (me["manner_temperature"] + other["manner_temperature"]) / 50.0  # 최대 +4점 정도

    return score


# ==============================
# 매칭 결과 / 알림 페이지
# ==============================
def show_match_page():
    st.subheader("매칭 결과 보기 / 알림 확인")
    user_id = st.text_input("내 닉네임 또는 ID 입력", key="match_user_id")
    max_results = st.slider("최대 몇 명까지 보고 싶나요?", 1, 20, 5)

    if st.button("매칭 찾기"):
        if not user_id:
            st.error("닉네임 또는 ID를 입력해 주세요.")
            return

        df = load_data()
        if df.empty:
            st.warning("아직 저장된 설문이 없습니다. 먼저 '설문 참여'에서 정보를 입력해 주세요.")
            return

        if user_id not in df["user_id"].values:
            st.error("입력한 ID로 저장된 설문이 없습니다. 철자 또는 대소문자를 확인해 주세요.")
            return

        me = df[df["user_id"] == user_id].iloc[0]
        others = df[df["user_id"] != user_id].copy()

        if others.empty:
            st.info("아직 다른 사람이 설문에 참여하지 않았습니다. 나중에 다시 확인해 보세요.")
            return

        # 점수 계산
        scores = []
        for _, row in others.iterrows():
            s = calc_match_score(me, row)
            if s > 0:
                scores.append((row["user_id"], s))
        if not scores:
            st.info("조건에 맞는 매칭 상대를 찾지 못했습니다. 선호 조건을 조금 넓혀보는 것은 어떨까요?")
            return

        scores.sort(key=lambda x: x[1], reverse=True)
        top_ids = [u for u, _ in scores[:max_results]]
        top_df = others[others["user_id"].isin(top_ids)].copy()
        top_df["score"] = [dict(scores)[uid] for uid in top_df["user_id"]]

        decisions = load_decisions()

        st.markdown("### 나와 잘 맞는 사람들")
        for _, row in top_df.sort_values("score", ascending=False).iterrows():
            with st.expander(f"{row['user_id']} 님 (점수: {row['score']:.1f})"):
                st.write("**사용 목적:**", row["purpose"])
                st.write(
                    "**그룹:**",
                    f"{row['group_name']} ({row['group_scope']})"
                    if row["group_name"] else row["group_scope"],
                )
                st.write("---")
                st.write("#### 상대의 자기소개")
                st.write(f"- 나이: {row['self_age']}")
                st.write(f"- 성별: {row['self_gender']}")
                st.write(f"- 성격: {row['self_personality']}")
                st.write(f"- 외모 타입: {row['self_appearance']}")
                st.write(f"- 키: {row['self_height']} cm, BMI: {row['self_bmi']}")
                st.write(f"- 매너 온도: {row['manner_temperature']}°")

                st.write("#### 상대가 원하는 이상형 (Preference)")
                st.write(f"- 원하는 나이 범위: {row['pref_min_age']} ~ {row['pref_max_age']}")
                st.write(f"- 원하는 성별: {row['pref_gender']}")
                st.write(f"- 선호 성격: {row['pref_personality']}")
                st.write(f"- 선호 외모: {row['pref_appearance']}")
                st.write(
                    f"- 원하는 키 범위: {row['pref_min_height']} ~ {row['pref_max_height']} cm"
                )
                st.write(
                    f"- 원하는 BMI 범위: {row['pref_min_bmi']} ~ {row['pref_max_bmi']}"
                )

                st.write("#### 상대의 블랙리스트 정보")
                st.write(f"- 피하고 싶은 성격: {row['blacklist_personality']}")
                st.write(f"- 피하고 싶은 외모: {row['blacklist_appearance']}")

                st.write("---")
                st.write("### 매칭 수락 / 거절")

                # 기존 내 결정
                mask_me_to_other = (decisions["from_user"] == user_id) & (
                    decisions["to_user"] == row["user_id"]
                )
                existing = decisions[mask_me_to_other]
                my_decision = existing["decision"].iloc[0] if not existing.empty else None

                # 상대가 이미 나에 대해 내린 결정
                mask_other_to_me = (decisions["from_user"] == row["user_id"]) & (
                    decisions["to_user"] == user_id
                )
                other_existing = decisions[mask_other_to_me]
                other_decision = (
                    other_existing["decision"].iloc[0]
                    if not other_existing.empty
                    else None
                )

                if my_decision:
                    st.info(f"내 선택: **{my_decision}**")
                else:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(
                            "이 사람 마음에 들어요 💚 (수락)",
                            key=f"accept_{row['user_id']}",
                        ):
                            decisions = load_decisions()
                            decisions = decisions[
                                ~(
                                    (decisions["from_user"] == user_id)
                                    & (decisions["to_user"] == row["user_id"])
                                )
                            ]
                            new_dec = {
                                "timestamp": datetime.now().isoformat(),
                                "from_user": user_id,
                                "to_user": row["user_id"],
                                "decision": "수락",
                            }
                            decisions = pd.concat(
                                [decisions, pd.DataFrame([new_dec])],
                                ignore_index=True,
                            )
                            save_decisions(decisions)
                            st.success("수락으로 저장되었습니다. 상대방도 수락하면 매칭이 성사됩니다!")
                    with col_b:
                        if st.button(
                            "패스 🙅‍♀️ (거절)",
                            key=f"reject_{row['user_id']}",
                        ):
                            decisions = load_decisions()
                            decisions = decisions[
                                ~(
                                    (decisions["from_user"] == user_id)
                                    & (decisions["to_user"] == row["user_id"])
                                )
                            ]
                            new_dec = {
                                "timestamp": datetime.now().isoformat(),
                                "from_user": user_id,
                                "to_user": row["user_id"],
                                "decision": "거절",
                            }
                            decisions = pd.concat(
                                [decisions, pd.DataFrame([new_dec])],
                                ignore_index=True,
                            )
                            save_decisions(decisions)
                            st.warning("거절로 저장되었습니다. 이 상대와는 매칭되지 않습니다.")

                # 상호 수락 여부 최신 상태로 다시 확인
                decisions = load_decisions()
                mask_me_to_other = (decisions["from_user"] == user_id) & (
                    decisions["to_user"] == row["user_id"]
                )
                mask_other_to_me = (decisions["from_user"] == row["user_id"]) & (
                    decisions["to_user"] == user_id
                )
                my_decision = (
                    decisions[mask_me_to_other]["decision"].iloc[0]
                    if not decisions[mask_me_to_other].empty
                    else None
                )
                other_decision = (
                    decisions[mask_other_to_me]["decision"].iloc[0]
                    if not decisions[mask_other_to_me].empty
                    else None
                )

                if my_decision == "수락" and other_decision == "수락":
                    st.success("🎉 양쪽 모두 수락했습니다! 매칭이 성사되었습니다. (알림 발송이 일어나는 위치)")


# ==============================
# 메인
# ==============================
def main():
    st.set_page_config(page_title="소셜 매칭 앱 데모", page_icon="💞", layout="wide")
    st.title("💞 친구 / 연애 / 모임 매칭 앱 (Streamlit Demo)")
    st.write(
        """
        이 앱은 사용 목적(친구, 연애, 스터디 등)과 본인/이상형 설문을 기반으로
        서로 잘 맞는 사람을 찾아주는 데모 버전입니다.
        - 외모, 피지컬은 간단한 카테고리와 숫자 입력만 사용하며 사진은 사용하지 않습니다.
        - 학교/학원 등 그룹을 설정하면 그 그룹 내에서만 매칭되도록 제한할 수 있습니다.
        - 매너온도, 블랙리스트 기능으로 윤리적인 매칭을 돕습니다.
        """
    )

    menu = st.sidebar.radio("메뉴 선택", ["설문 참여", "매칭 보기"])

    if menu == "설문 참여":
        register_survey()
    else:
        show_match_page()


if __name__ == "__main__":
    main()
