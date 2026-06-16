import streamlit as st
import os
import tempfile
from backend import (
    get_outfit_combinations,
    extract_clothing_attributes,
    add_to_closet,
    IMAGE_DIR,
)

st.set_page_config(page_title="Find Closet", layout="wide")

for key, default in [
    ("current_page", "home"),
    ("search_query", ""),
    ("sel_top", False),
    ("sel_bottom", False),
    ("sel_dress", False),
    ("selected_item", None),
    ("show_uploader", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    st.title("Find Closet")
    st.write("---")
    if st.button("홈 (스타일 추천)", use_container_width=True):
        st.session_state.current_page = "home"
        st.session_state.selected_item = None
        st.rerun()
    if st.button("내 옷장 관리", use_container_width=True):
        st.session_state.current_page = "closet"
        st.session_state.selected_item = None
        st.rerun()
    st.write("---")
    st.info("**AI STATUS**\n\nCLIP Ready")

# ── 홈 페이지 ──────────────────────────────────────────────
if st.session_state.current_page == "home":
    st.title("파인드 클로젯")
    st.subheader("자신의 옷장을 검색하고 상황에 맞는 최고의 옷을 추천받으세요.")
    st.write("---")

    st.markdown("### 추천받고 싶은 카테고리를 선택하세요")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("상의", type="primary" if st.session_state.sel_top else "secondary", use_container_width=True):
            st.session_state.sel_top = not st.session_state.sel_top
            st.rerun()
    with col2:
        if st.button("하의", type="primary" if st.session_state.sel_bottom else "secondary", use_container_width=True):
            st.session_state.sel_bottom = not st.session_state.sel_bottom
            st.rerun()
    with col3:
        if st.button("원피스", type="primary" if st.session_state.sel_dress else "secondary", use_container_width=True):
            st.session_state.sel_dress = not st.session_state.sel_dress
            st.rerun()

    st.write("")
    query = st.text_input("어떤 스타일을 찾으시나요?", placeholder="예: '결혼식 하객룩 추천해줘'")
    if st.button("추천받기", type="primary", use_container_width=True):
        if not (st.session_state.sel_top or st.session_state.sel_bottom or st.session_state.sel_dress):
            st.error("카테고리 중 최소 하나를 선택해 주세요!")
        elif not query.strip():
            st.warning("스타일 문장을 입력해 주세요.")
        else:
            st.session_state.search_query = query
            st.session_state.current_page = "results"
            st.rerun()

# ── 결과 페이지 ────────────────────────────────────────────
elif st.session_state.current_page == "results":
    if st.button("← 메인으로 돌아가기"):
        st.session_state.current_page = "home"
        st.rerun()

    st.title("스타일 추천 결과")
    st.success(f"**'{st.session_state.search_query}'** 기반으로 내 옷장에서 최적의 조합을 찾았습니다.")

    selected_tabs, selected_categories = [], []
    if st.session_state.sel_top:
        selected_tabs.append("상의"); selected_categories.append("Top")
    if st.session_state.sel_bottom:
        selected_tabs.append("하의"); selected_categories.append("Bottom")
    if st.session_state.sel_dress:
        selected_tabs.append("원피스"); selected_categories.append("Dress")

    with st.spinner("AI가 코디를 분석 중이에요..."):
        result = get_outfit_combinations(
            st.session_state.search_query,
            st.session_state.sel_top,
            st.session_state.sel_bottom,
            st.session_state.sel_dress,
        )

    if not result["tops"] and not result["bottoms"] and not result["dresses"]:
        st.error("옷장이 비어있어요! 먼저 옷을 등록해주세요.")
        if st.button("옷장 관리로 이동"):
            st.session_state.current_page = "closet"
            st.rerun()
        st.stop()

    st.markdown(f"**AI 키워드:** {', '.join(result['keywords'])}")
    st.write("---")

    tabs = st.tabs(selected_tabs)
    for idx, cat in enumerate(selected_categories):
        with tabs[idx]:
            items = result["tops"] if cat == "Top" else result["bottoms"] if cat == "Bottom" else result["dresses"]
            if not items:
                st.warning("해당 카테고리에 옷이 없어요!")
            else:
                cols = st.columns(len(items))
                for rank, item in enumerate(items):
                    with cols[rank]:
                        st.image(item["path"], use_container_width=True)
                        st.markdown(f"**TOP {rank+1}**")
                        st.info(f"유사도: {item['score']:.3f}")

    if result["combinations"]:
        st.write("---")
        st.markdown("### 최적 코디 조합 Top 3")
        for i, combo in enumerate(result["combinations"]):
            st.markdown(f"**{i+1}번 코디** (점수: {combo['score']:.3f})")
            c1, c2 = st.columns(2)
            with c1:
                st.image(combo["top"], caption="상의")
            with c2:
                st.image(combo["bottom"], caption="하의")

# ── 옷장 관리 페이지 ───────────────────────────────────────
elif st.session_state.current_page == "closet":
    st.title("내 옷장 관리")

    if st.session_state.selected_item:
        item = st.session_state.selected_item
        if st.button("← 옷장으로 돌아가기"):
            st.session_state.selected_item = None
            st.rerun()
        st.markdown(f"### {item['name']}")
        c1, c2 = st.columns(2)
        with c1:
            st.image(item["path"], use_container_width=True)
        with c2:
            with st.spinner("AI가 속성 분석 중..."):
                attrs = extract_clothing_attributes(item["path"])
            st.markdown(f"**카테고리:** {item['category']}")
            st.markdown("**AI가 분석한 속성:**")
            for k, v in attrs.items():
                st.write(f"• **{k}**: {v}")
        st.stop()

    if st.button("옷 추가하기"):
        st.session_state.show_uploader = not st.session_state.show_uploader

    if st.session_state.show_uploader:
        uploaded_file = st.file_uploader("의류 사진 업로드 (JPG, PNG, WEBP)")
        if uploaded_file:
            with st.spinner("AI가 옷을 분석 중이에요..."):
                suffix = "." + uploaded_file.name.split(".")[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                attrs = extract_clothing_attributes(tmp_path)
                category = add_to_closet(tmp_path, uploaded_file.name)
                os.unlink(tmp_path)
            st.success(f"[{category}] 로 저장 완료!")
            c1, c2 = st.columns(2)
            with c1:
                st.image(uploaded_file, use_container_width=True)
            with c2:
                st.markdown(f"**분류된 카테고리:** {category}")
                st.markdown("**AI가 분석한 속성:**")
                for k, v in attrs.items():
                    st.write(f"• **{k}**: {v}")
            st.session_state.show_uploader = False
            st.rerun()

    st.write("---")
    all_items = []
    for cat_kor, cat_eng in [("상의", "Top"), ("하의", "Bottom"), ("원피스", "Dress")]:
        folder = os.path.join(IMAGE_DIR, cat_kor)
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
                    all_items.append({"path": os.path.join(folder, f), "name": f, "category": cat_eng})

    st.write(f"현재 등록된 아이템: **{len(all_items)}개**")
    cols = st.columns(4)
    for i, item in enumerate(all_items):
        with cols[i % 4]:
            st.image(item["path"], use_container_width=True)
            st.caption(f"[{item['category']}] {item['name']}")
            if st.button("상세보기", key=f"detail_{i}"):
                st.session_state.selected_item = item
                st.rerun()
