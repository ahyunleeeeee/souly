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
# 기본 유틸
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
        "self_body_type", "self_mbti",
        "self_height",
        "pref_min_age", "pref_max_age",
        "pref_gender", "pref_personality",
        "pref_appearance", "pref_body_type",
        "pref_min_height", "pref_max_height",
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


def split_tags(val):
    """세미콜론으로 저장된 문자열을 리스트로 바꾸는 헬퍼 함수"""
    if pd.isna(val):
        return []
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return []
    return s.split(";")


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


def get_prev(prev_row, col, default):
    """이전에 저장된 설문이 있으면 그 값을 기본값으로 쓰는 헬퍼 함수"""
    if prev_row is None:
        return default
    try:
        val = prev_row.get(col, default)
    except Exception:
        return default
    try:
        if pd.isna(val):
            return default
    except Exception:
        pass
    if isinstance(val, str) and val.lower() == "nan":
        return default
    return val


# ------------------------------
# 매칭 점수 계산
# ------------------------------
def calc_match_score(me, other):
    """
    나(me)와 상대(other) 간의 매칭 점수 계산.
    - me, other: pandas.Series (각 사용자의 row)
    """
    score = 0.0

    # 1. 목적이 다르면 제외
    if me["purpose"] != other["purpose"]:
        return -1

    # 2. 그룹 필터
    if me["group_scope"] == "특정 그룹 내에서" and isinstance(me["group_name"], str) and me["group_name"].strip():
        if other["group_name"] != me["group_name"]:
            return -1

    if other["group_scope"] == "특정 그룹 내에서" and isinstance(other["group_name"], str) and other["group_name"].strip():
        if me["group_name"] != other["group_name"]:
            return -1

    # 3. 내 블랙리스트 (내 입장에서 상대 거르기)
    my_black_p = split_tags(me["blacklist_personality"])
    my_black_a = split_tags(me["blacklist_appearance"])

    other_p = split_tags(other["self_personality"])
    other_a = other["self_appearance"]

    if any(p in my_black_p for p in other_p):
        return -1
    if other_a in my_black_a:
        return -1

    # ===== 내가 원하는 조건 vs 상대 실제 =====

    # 나이
    if me["pref_min_age"] <= other["self_age"] <= me["pref_max_age"]:
        score += 10
    else:
        # 범위 밖이면 매칭 안 함
        return -1

    # 성별
    if me["pref_gender"] != "상관없음":
        if me["pref_gender"] == other["self_gender"]:
            score += 5
        else:
            return -1
    else:
        score += 3  # 성별 상관없으면 살짝 보너스

    # 키
    if me["pref_min_height"] <= other["self_height"] <= me["pref_max_height"]:
        score += 4

    # 체형
    my_pref_body = split_tags(me["pref_body_type"])
    other_body = other["self_body_type"]

    if (not my_pref_body) or ("상관없음" in my_pref_body):
        # 체형 상관 없으면 약간의 기본 점수
        score += 1
    else:
        if other_body in my_pref_body:
            score += 4
        else:
            score -= 1  # 살짝 감점

    # 성격
    my_pref_p = split_tags(me["pref_personality"])
    overlap1 = len(set(my_pref_p) & set(other_p))
    score += overlap1 * 3

    # 외모 (상관없음 처리)
    my_pref_a = split_tags(me["pref_appearance"])
    if (not my_pref_a) or ("상관없음" in my_pref_a):
        # 외모 상관 없으면 약간의 기본 점수
        score += 1
    else:
        if other_a in my_pref_a:
            score += 3

    # ===== 상대가 원하는 조건 vs 내 실제 (상호 매칭) =====

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
    other_pref_p = split_tags(other["pref_personality"])
    my_p = split_tags(me["self_personality"])
    overlap2 = len(set(other_pref_p) & set(my_p))
    score += overlap2 * 2

    # 외모
    other_pref_a = split_tags(other["pref_appearance"])
    if (not other_pref_a) or ("상관없음" in other_pref_a):
        score += 1
    else:
        if me["self_appearance"] in other_pref_a:
            score += 2

    # 체형
    other_pref_body = split_tags(other["pref_body_type"])
    my_body = me["self_body_type"]
    if (not other_pref_body) or ("상관없음" in other_pref_body):
        score += 1
    else:
        if my_body in other_pref_body:
            score += 2

    # ===== 매너온도 보너스 =====
    mt_me = get_user_manner_temperature(me["user_id"])
    mt_other = get_user_manner_temperature(other["user_id"])
    score += (mt_me + mt_other) / 50.0  # 대략 최대 +4점 정도

    return score


# ------------------------------
# 설문 페이지
# ------------------------------
def register_survey():
    st.subheader("프로필 & 설문")

    df = load_data()

    # 세션에 저장된 user_id가 있으면 기본값으로
    default_id = st.session_state.get("user_id", "")
    user_id = st.text_input("닉네임 (로그인에 사용할 이름)", max_chars=30, value=default_id)

    prev = None
    if user_id and user_id in df["user_id"].values:
        prev = df[df["user_id"] == user_id].iloc[0]
        st.success("기존 설문을 불러왔어요. 수정 후 다시 저장하면 업데이트됩니다.")

    # 기본 설정
    purpose_options = ["친구", "연애", "스터디", "취미", "기타"]
    match_mode_options = ["1:1 매칭", "다인원 매칭"]
    group_scope_options = ["전체 공개", "특정 그룹 내에서"]

    purpose_default = get_prev(prev, "purpose", "친구")
    match_mode_default = get_prev(prev, "match_mode", "1:1 매칭")
    group_scope_default = get_prev(prev, "group_scope", "전체 공개")
    group_name_default = get_prev(prev, "group_name", "")

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        purpose = st.selectbox(
            "사용 목적",
            purpose_options,
            index=purpose_options.index(purpose_default) if purpose_default in purpose_options else 0
        )
    with col_top2:
        match_mode = st.radio(
            "매칭 방식",
            match_mode_options,
            index=match_mode_options.index(match_mode_default) if match_mode_default in match_mode_options else 0
        )

    prev_group_size = int(get_prev(prev, "group_size", 2))
    if match_mode == "1:1 매칭":
        group_size = 2
    else:
        group_size = st.slider("희망 모임 인원 (본인 포함)", 3, 10, prev_group_size if 3 <= prev_group_size <= 10 else 4)

    st.markdown("---")
    st.markdown("### 그룹 설정 (선택)")
    group_scope = st.selectbox(
        "매칭 범위",
        group_scope_options,
        index=group_scope_options.index(group_scope_default) if group_scope_default in group_scope_options else 0
    )
    group_name = ""
    if group_scope == "특정 그룹 내에서":
        group_name = st.text_input(
            "그룹 이름 (예: OO고등학교, OO학원, 1학년 3반 등)",
            max_chars=50,
            value=group_name_default
        )

    st.markdown("---")
    st.markdown("### 나에 대한 정보")

    personality_options = [
        "내향적", "외향적", "차분함", "활발함", "유머있음",
        "논리적", "감성적", "리더형", "서포터형", "즉흥적", "계획적"
    ]
    appearance_base = ["강아지상", "고양이상", "여우상", "토끼상", "곰상", "사슴상", "공룡상", "기타"]
    body_type_options = ["저체중", "보통", "과체중"]

    col1, col2 = st.columns(2)
    with col1:
        self_age_default = int(get_prev(prev, "self_age", 18))
        self_height_default = int(get_prev(prev, "self_height", 165))
        self_gender_default = get_prev(prev, "self_gender", "여성")
        self_body_type_default = get_prev(prev, "self_body_type", "보통")
        self_mbti_default = get_prev(prev, "self_mbti", "")
        contact_default = get_prev(prev, "contact_info", "")

        self_age = st.number_input("나이", 10, 100, self_age_default)
        self_gender = st.selectbox(
            "성별",
            ["여성", "남성", "기타"],
            index=["여성", "남성", "기타"].index(self_gender_default)
            if self_gender_default in ["여성", "남성", "기타"] else 0
        )
        self_height = st.number_input("키 (cm)", 130, 220, self_height_default)
        self_body_type = st.selectbox(
            "본인 체형",
            body_type_options,
            index=body_type_options.index(self_body_type_default) if self_body_type_default in body_type_options else 1
        )
        self_mbti = st.text_input("MBTI (선택, 예: INFP)", max_chars=4, value=str(self_mbti_default))

    with col2:
        self_personality_default = split_tags(get_prev(prev, "self_personality", ""))
        self_appearance_default = get_prev(prev, "self_appearance", appearance_base[0])

        self_personality = st.multiselect(
            "본인 성격 (복수 선택 가능)",
            personality_options,
            default=[p for p in self_personality_default if p in personality_options]
        )
        self_appearance = st.selectbox(
            "본인 외모 이미지에 가장 가까운 것",
            appearance_base,
            index=appearance_base.index(self_appearance_default) if self_appearance_default in appearance_base else 0
        )

    st.markdown("##### 📞 연락처 (선택)")
    st.write("인스타 ID / 이메일 / 카카오 오픈채팅 링크 등. **최종 매칭된 사람에게만 공개**됩니다.")
    contact_info = st.text_input("연락처", max_chars=100, value=contact_default)

    st.markdown("---")
    st.markdown("### 내가 원하는 상대")

    pref_gender_default = get_prev(prev, "pref_gender", "상관없음")
    pref_min_age_default = int(get_prev(prev, "pref_min_age", 16))
    pref_max_age_default = int(get_prev(prev, "pref_max_age", 22))
    pref_min_height_default = int(get_prev(prev, "pref_min_height", 155))
    pref_max_height_default = int(get_prev(prev, "pref_max_height", 180))
    pref_personality_default = split_tags(get_prev(prev, "pref_personality", ""))
    pref_appearance_default = split_tags(get_prev(prev, "pref_appearance", ""))
    pref_body_type_default = split_tags(get_prev(prev, "pref_body_type", ""))

    with st.columns(2)[0]:
        pref_gender = st.selectbox(
            "원하는 성별",
            ["상관없음", "여성", "남성"],
            index=["상관없음", "여성", "남성"].index(pref_gender_default)
            if pref_gender_default in ["상관없음", "여성", "남성"] else 0
        )
        pref_min_age, pref_max_age = st.slider(
            "원하는 나이 범위",
            10, 100,
            (pref_min_age_default, pref_max_age_default)
        )
        pref_min_height, pref_max_height = st.slider(
            "원하는 키 범위 (cm)",
            130, 220,
            (pref_min_height_default, pref_max_height_default)
        )

    with st.columns(2)[1]:
        pref_personality = st.multiselect(
            "원하는 성격 (복수 선택 가능)",
            personality_options,
            default=[p for p in pref_personality_default if p in personality_options]
        )
        pref_appearance = st.multiselect(
            "선호 외모 타입",
            ["상관없음"] + appearance_base,
            default=[a for a in pref_appearance_default if a in (["상관없음"] + appearance_base)]
        )
        pref_body_type = st.multiselect(
            "선호 체형",
            ["상관없음"] + body_type_options,
            default=[b for b in pref_body_type_default if b in (["상관없음"] + body_type_options)]
        )

    st.markdown("---")
    st.markdown("### 블랙리스트 / 피하고 싶은 유형 (선택)")

    blacklist_personality_default = split_tags(get_prev(prev, "blacklist_personality", ""))
    blacklist_appearance_default = split_tags(get_prev(prev, "blacklist_appearance", ""))

    blacklist_personality = st.multiselect(
        "피하고 싶은 성격",
        personality_options,
        default=[p for p in blacklist_personality_default if p in personality_options]
    )
    blacklist_appearance = st.multiselect(
        "피하고 싶은 외모 타입",
        appearance_base,
        default=[a for a in blacklist_appearance_default if a in appearance_base]
    )

    st.info("※ 매너온도는 내가 설정하지 않고, **최종 매칭된 사람들이 남긴 별점**으로 자동 계산됩니다.")

    if st.button("프로필 저장하기", use_container_width=True):
        if not user_id:
            st.error("닉네임을 반드시 입력해 주세요.")
            return

        # 세션에 현재 닉네임 저장 → 다른 탭에서 자동 사용
        st.session_state["user_id"] = user_id

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
            "self_body_type": self_body_type,
            "self_mbti": self_mbti,
            "self_height": self_height,
            "pref_min_age": pref_min_age,
            "pref_max_age": pref_max_age,
            "pref_gender": pref_gender,
            "pref_personality": ";".join(pref_personality),
            "pref_appearance": ";".join(pref_appearance),
            "pref_body_type": ";".join(pref_body_type),
            "pref_min_height": pref_min_height,
            "pref_max_height": pref_max_height,
            "blacklist_personality": ";".join(blacklist_personality),
            "blacklist_appearance": ";".join(blacklist_appearance),
            "contact_info": contact_info
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("프로필이 저장되었습니다! 이제 '매칭 찾기' 또는 '알림함' 탭을 이용해 보세요.")


# ------------------------------
# 매칭 보기 페이지
# ------------------------------
def show_match_page():
    st.subheader("매칭 찾기")

    # 세션에 저장된 ID 사용
    session_id = st.session_state.get("user_id", "")
    if session_id:
        st.info(f"현재 로그인된 닉네임: **{session_id}** (닉네임 변경은 '프로필 & 설문' 탭에서)")
        user_id = session_id
    else:
        user_id = st.text_input("내 닉네임 또는 ID 입력", key="match_user_id")

    if not user_id:
        st.info("매칭을 보려면 먼저 닉네임을 입력하거나 프로필을 저장해 주세요.")
        return

    df = load_data()
    if df.empty:
        st.warning("아직 프로필 데이터가 없습니다. 먼저 '프로필 & 설문'에서 정보를 입력해 주세요.")
        return

    if user_id not in df["user_id"].values:
        st.error("해당 ID로 저장된 프로필이 없습니다. 철자 또는 대소문자를 확인해 주세요.")
        return

    # 설문에서 바로 들어온 경우 세션에 ID 저장
    st.session_state["user_id"] = user_id

    me = df[df["user_id"] == user_id].iloc[0]
    others = df[df["user_id"] != user_id].copy()

    if others.empty:
        st.info("아직 다른 사용자가 프로필을 등록하지 않았습니다.")
        return

    decisions = load_decisions()

    max_results = st.slider("한 번에 볼 매칭 후보 수", 1, 20, 5)

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

    st.markdown("### ✨ 나와 잘 맞는 사람들")
    for _, row in top_df.sort_values("score", ascending=False).iterrows():
        partner_id = row["user_id"]
        partner_mt = get_user_manner_temperature(partner_id)

        # 내 선택 상태
        dec_me = decisions[
            (decisions["from_user"] == user_id) &
            (decisions["to_user"] == partner_id)
        ]
        my_decision = dec_me["decision"].iloc[0] if not dec_me.empty else None

        if my_decision == "수락":
            icon = "💚"
        elif my_decision == "거절":
            icon = "❌"
        else:
            icon = "🤍"

        label = f"{icon} {partner_id} 님 · 점수 {row['score']:.1f} · 매너온도 {partner_mt}°"

        with st.expander(label):
            st.write("**사용 목적:**", row["purpose"])
            if isinstance(row["group_name"], str) and row["group_name"].strip():
                st.write("**그룹:**", f"{row['group_name']} ({row['group_scope']})")
            else:
                st.write("**그룹:**", row["group_scope"])

            st.write("---")
            st.write("#### 🎭 상대 프로필")
            st.write(f"- 나이: {row['self_age']}")
            st.write(f"- 성별: {row['self_gender']}")
            st.write(f"- 성격: {row['self_personality']}")
            st.write(f"- 외모 타입: {row['self_appearance']}")
            st.write(f"- 체형: {row['self_body_type']}")
            if isinstance(row.get("self_mbti", ""), str) and row.get("self_mbti", "").strip():
                st.write(f"- MBTI: {row['self_mbti']}")
            st.write(f"- 키: {row['self_height']} cm")
            st.write(f"- 현재 매너온도: {partner_mt}°")

            st.write("---")
            st.write("#### 💎 상대가 원하는 이상형")
            st.write(f"- 나이 범위: {row['pref_min_age']} ~ {row['pref_max_age']}")
            st.write(f"- 성별: {row['pref_gender']}")
            st.write(f"- 선호 성격: {row['pref_personality']}")
            st.write(f"- 선호 외모: {row['pref_appearance']}")
            st.write(f"- 선호 체형: {row['pref_body_type']}")
            st.write(f"- 키 범위: {row['pref_min_height']} ~ {row['pref_max_height']} cm")

            st.write("---")
            st.write("### 매칭 선택")

            if my_decision:
                st.info(f"내 선택: **{my_decision}** (최종 결과는 '알림함'에서 확인할 수 있어요.)")
            else:
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("💗 이 사람 마음에 들어요", key=f"accept_{partner_id}"):
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
                        st.success("수락으로 저장되었습니다. '알림함'에서 최종 매칭을 확인해 보세요.")
                        st.rerun()
                with col_b:
                    if st.button("🚫 패스할래요", key=f"reject_{partner_id}"):
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
                        st.rerun()


# ------------------------------
# 알림 / 최종 매칭 페이지
# ------------------------------
def show_notifications_page():
    st.subheader("알림함")

    session_id = st.session_state.get("user_id", "")
    if session_id:
        st.info(f"현재 로그인된 닉네임: **{session_id}**")
        user_id = session_id
    else:
        user_id = st.text_input("내 닉네임 또는 ID 입력", key="notify_user_id")

    if not user_id:
        st.info("알림을 보려면 먼저 닉네임을 입력하거나 프로필을 저장해 주세요.")
        return

    df = load_data()
    if df.empty or user_id not in df["user_id"].values:
        st.error("해당 ID로 저장된 프로필이 없습니다. 먼저 '프로필 & 설문'에서 프로필을 저장해 주세요.")
        return

    # 세션에 ID 저장
    st.session_state["user_id"] = user_id

    decisions = load_decisions()
    ratings = load_ratings()

    # 내 매너온도
    my_mt = get_user_manner_temperature(user_id)
    me = df[df["user_id"] == user_id].iloc[0]
    my_contact = me["contact_info"] if isinstance(me["contact_info"], str) else ""

    st.info(f"현재 내 매너온도는 **{my_mt}°** 입니다.")
    if my_contact:
        st.write(f"📞 등록된 내 연락처: **{my_contact}**")
    else:
        st.write("📞 아직 연락처가 없습니다. '프로필 & 설문' 탭에서 연락처를 추가해 보세요.")

    # ===== 상호 수락(최종 매칭) 계산 =====
    accepts = decisions[decisions["decision"] == "수락"]

    mutual_ids = set()
    my_accepts = accepts[accepts["from_user"] == user_id]

    for _, row in my_accepts.iterrows():
        other = row["to_user"]
        if not accepts[(accepts["from_user"] == other) & (accepts["to_user"] == user_id)].empty:
            mutual_ids.add(other)

    # ===== 나를 수락한 사람들 (한쪽만 수락해도) =====
    liked_me_ids_all = set(accepts[accepts["to_user"] == user_id]["from_user"])
    liked_me_only = liked_me_ids_all - mutual_ids

    # --- 최종 매칭 ---
    st.markdown("### ✅ 최종 매칭된 사람들")
    if not mutual_ids:
        st.info("아직 양쪽 모두 수락한 최종 매칭은 없습니다.")
    else:
        for pid in mutual_ids:
            partner = df[df["user_id"] == pid]
            if partner.empty:
                continue
            partner = partner.iloc[0]
            partner_mt = get_user_manner_temperature(pid)
            partner_contact = partner["contact_info"] if isinstance(partner["contact_info"], str) else ""

            with st.expander(f"🎉 {pid} 님과 매칭되었어요!"):
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
                st.write(f"- 체형: {partner['self_body_type']}")
                if isinstance(partner.get("self_mbti", ""), str) and partner.get("self_mbti", "").strip():
                    st.write(f"- MBTI: {partner['self_mbti']}")
                st.write(f"- 키: {partner['self_height']} cm")
                st.write(f"- 매너온도: {partner_mt}°")

                st.write("---")
                st.write("#### 연락처")
                if partner_contact:
                    st.success(f"상대가 등록한 연락처: **{partner_contact}**")
                else:
                    st.info("상대가 아직 연락처를 등록하지 않았어요. 나중에 다시 확인해 보세요.")

                st.write("---")
                st.write("#### ⭐ 매너 평가")

                existing_rating = ratings[
                    (ratings["from_user"] == user_id) &
                    (ratings["to_user"] == pid)
                ]
                default_rating = int(existing_rating["rating"].iloc[0]) if not existing_rating.empty else 5

                new_rating = st.slider(
                    "별점 (1점 = 별로, 5점 = 최고)",
                    1, 5, default_rating,
                    key=f"rating_{pid}"
                )

                if st.button("별점 저장", key=f"rating_save_{pid}"):
                    ratings = load_ratings()
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
                    st.success("별점이 저장되었습니다! 상대의 매너온도에 반영됩니다.")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 💌 나를 먼저 수락한 사람들")
    if not liked_me_only:
        st.info("아직 나를 먼저 수락한 사람이 없습니다.")
    else:
        for pid in liked_me_only:
            partner = df[df["user_id"] == pid]
            if partner.empty:
                continue
            partner = partner.iloc[0]
            with st.expander(f"{pid} 님이 나를 수락했습니다 💚"):
                st.write("**사용 목적:**", partner["purpose"])
                st.write(f"- 나이: {partner['self_age']}")
                st.write(f"- 성별: {partner['self_gender']}")
                st.write(f"- 성격: {partner['self_personality']}")
                st.write(f"- 외모 타입: {partner['self_appearance']}")
                st.write(f"- 체형: {partner['self_body_type']}")
                if isinstance(partner.get("self_mbti", ""), str) and partner.get("self_mbti", "").strip():
                    st.write(f"- MBTI: {partner['self_mbti']}")
                st.write("※ 이 사람을 나도 수락하면 최종 매칭으로 전환됩니다. (→ '매칭 찾기' 탭에서 수락 가능)")


# ------------------------------
# 메인 함수 + 글로벌 UI 스타일
# ------------------------------
def main():
    st.set_page_config(page_title="HeartMatch", page_icon="💗", layout="wide")

    # ===== 글로벌 CSS (핑크 데이팅 앱 느낌) =====
    st.markdown(
        """
        <style>
        /* 배경 살짝 톤 다운 */
        .stApp {
            background: radial-gradient(circle at top left, #ffe4f0 0, #ffffff 50%, #ffe9f2 100%);
        }

        /* 메인 컨테이너 폭 제한 */
        .main-block {
            max-width: 980px;
            margin: 0 auto;
        }

        /* 히어로 카드 */
        .hero-card {
            background: linear-gradient(135deg, #ff9ac6, #ff4b6b);
            border-radius: 32px;
            padding: 24px 32px;
            color: white;
            display: flex;
            align-items: center;
            gap: 24px;
            box-shadow: 0 18px 40px rgba(255, 75, 107, 0.35);
            margin-bottom: 24px;
        }
        .hero-icon {
            width: 88px;
            height: 88px;
            border-radius: 24px;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 46px;
            color: #ff4b6b;
            flex-shrink: 0;
        }
        .hero-text h1 {
            font-size: 32px;
            margin: 0 0 6px 0;
            font-weight: 800;
        }
        .hero-text p {
            margin: 2px 0;
            font-size: 15px;
            opacity: 0.92;
        }
        .hero-tagline {
            font-size: 13px;
            opacity: 0.85;
        }

        /* 섹션 카드 */
        .section-card {
            background: rgba(255,255,255,0.96);
            border-radius: 24px;
            padding: 20px 24px 24px 24px;
            box-shadow: 0 10px 28px rgba(0,0,0,0.05);
            margin-bottom: 18px;
        }

        /* 제목 스타일 */
        .section-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
            color: #222;
        }

        /* 버튼 스타일 */
        .stButton > button {
            border-radius: 999px;
            padding: 0.55rem 1.3rem;
            border: none;
            background: linear-gradient(135deg, #ff5c8d, #ff2e63);
            color: white;
            font-weight: 600;
            box-shadow: 0 10px 22px rgba(255, 46, 99, 0.35);
        }
        .stButton > button:hover {
            filter: brightness(1.05);
        }

        /* 라디오 / 셀렉트 살짝 둥글게 */
        .stRadio > label, .stSelectbox > label {
            font-weight: 600;
        }

        /* 사이드바 */
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid rgba(255,192,203,0.45);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===== 헤더 (히어로 카드) =====
    st.markdown('<div class="main-block">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="hero-card">
          <div class="hero-icon">💗</div>
          <div class="hero-text">
            <h1>Souly</h1>
            <p>친구 · 연애 · 모임까지, 설문 기반으로 나와 잘 맞는 사람을 찾아주는 매칭 서비스</p>
            <p class="hero-tagline">사진 대신 성격 · 외모 타입 · 체형 정보만 사용해, 조금 더 안전하고 편안한 매칭을 지향해요.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== 페이지 선택 =====
    menu = st.sidebar.radio(
        "탭 이동",
        ["프로필 & 설문", "매칭 찾기", "알림함"],
    )

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    if menu == "프로필 & 설문":
        register_survey()
    elif menu == "매칭 찾기":
        show_match_page()
    else:
        show_notifications_page()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

# ===== 온보딩 모달 (처음 접속 시 표시) =====
if "onboarding_shown" not in st.session_state:
    st.session_state["onboarding_shown"] = False

if not st.session_state["onboarding_shown"]:
    st.markdown(
        """
        <style>
        .onboard-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 380px;
            background: white;
            padding: 26px 30px;
            border-radius: 22px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(255, 60, 120, 0.35);
            z-index: 9999;
            border: 2px solid #FFD6E8;
        }
        .onboard-title {
            font-size: 24px;
            font-weight: 800;
            color: #FF2E63;
            margin-bottom: 10px;
        }
        .onboard-text {
            font-size: 15px;
            color: #333;
            line-height: 1.45;
            margin-bottom: 18px;
        }
        </style>
        <div class="onboard-modal">
            <div class="onboard-title">환영합니다! 💗</div>
            <div class="onboard-text">
                Souly는 성격과 취향 기반으로<br>
                나와 잘 맞는 사람을 연결해주는 매칭 서비스예요.<br><br>
                사진 없이 더 안전하고 편안한 매칭을 경험해보세요!
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("시작하기 💞", key="close_onboard"):
        st.session_state["onboarding_shown"] = True
        st.rerun()

