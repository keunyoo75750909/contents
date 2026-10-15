import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. 페이지 기본 설정 및 제목 표시
# ==========================================
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# 앱 제목과 설명
st.title("👨‍👩‍👧‍👦 동네별 인구 피라미드")
st.caption("전국 읍·면·동의 최신 인구 구조를 피라미드 그래프로 확인해보세요.")


# ==========================================
# 2. 데이터 불러오기 (캐싱 처리로 속도 최적화)
# ==========================================
@st.cache_data
def load_data():
    # GitHub에서 압축된 CSV 파일 직접 읽기
    url = "https://raw.githubusercontent.com/first2022-cyber/contents/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url)
    
    # 가장 최신 연도 데이터만 필터링
    latest_year = df["연도"].max()
    df_latest = df[df["연도"] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 실행
with st.spinner("데이터를 불러오는 중입니다..."):
    df, latest_year = load_data()

st.sidebar.info(f"📅 기준 연도: **{latest_year}년**")


# ==========================================
# 3. 나이 및 성별 열(Column) 추출하기
# ==========================================
# '남_'으로 시작하는 열 이름 찾기 (예: '남_0세', '남_1세' ...)
male_cols = [c for c in df.columns if c.startswith("남_")]

# 나이 라벨 순서 추출 (예: '0세', '1세', ..., '100세 이상')
# '남_' 접두사를 제거하여 나이 라벨만 순서대로 보관합니다.
age_labels = [c.replace("남_", "") for c in male_cols]

# 나이 라벨에 대응하는 여성 열 이름 생성 (예: '여_0세', '여_1세' ...)
female_cols = [f"여_{age}" for age in age_labels]


# ==========================================
# 4. 지역 선택 드롭다운 (시도 -> 시군구 -> 동)
# ==========================================
st.subheader("📍 지역 선택")

# 3개의 드롭다운을 한 줄로 배치
col1, col2, col3 = st.columns(3)

# 1) 시도 선택
with col1:
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("시·도", sido_list)

# 선택한 시도에 해당하는 데이터만 필터링
df_sido = df[df["시도"] == selected_sido]

# 2) 시군구 선택
with col2:
    sigungu_list = sorted(df_sido["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("시·군·구", sigungu_list)

# 선택한 시군구에 해당하는 데이터만 필터링
df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]

# 3) 동 선택
with col3:
    dong_list = sorted(df_sigungu["동"].dropna().unique())
    selected_dong = st.selectbox("읍·면·동", dong_list)

# 최종 선택된 동네 데이터 필터링
selected_data = df_sigungu[df_sigungu["동"] == selected_dong]


# ==========================================
# 5. 인구 피라미드 그래프 생성
# ==========================================
if not selected_data.empty:
    # 선택된 동네의 남성/여성 나이별 인구수 추출 (숫자형으로 변환)
    row = selected_data.iloc[0]
    male_pop = [int(row[col]) for col in male_cols]
    female_pop = [int(row[col]) for col in female_cols]

    # 총 인구수 계산
    total_male = sum(male_pop)
    total_female = sum(female_pop)
    total_pop = total_male + total_female

    # 동네 요약 정보 카드 출력
    st.markdown("---")
    st.subheader(f"📊 {selected_sido} {selected_sigungu} {selected_dong} 인구 현황")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("총 인구수", f"{total_pop:,} 명")
    m_col2.metric("남성 인구수", f"{total_male:,} 명")
    m_col3.metric("여성 인구수", f"{total_female:,} 명")

    # 남성 인구수는 왼쪽(음수)으로 배치
    male_pop_neg = [-val for val in male_pop]

    # Plotly 시각화 객체 생성
    fig = go.Figure()

    # 남성 막대 그래프 (왼쪽, 따뜻한 슬레이트 블루 톤)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=male_pop_neg,
        name="남성",
        orientation="h",
        marker=dict(color="#4A6FA5"),
        hovertemplate="<b>%{y}</b><br>남성 인구: %{customdata:,}명<extra></extra>",
        customdata=male_pop  # 툴팁에는 양수로 표시
    ))

    # 여성 막대 그래프 (오른쪽, 따뜻한 로즈 피치 톤)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_pop,
        name="여성",
        orientation="h",
        marker=dict(color="#E07A5F"),
        hovertemplate="<b>%{y}</b><br>여성 인구: %{x:,}명<extra></extra>"
    ))

    # X축 눈금을 양수로 깔끔하게 표시하기 위한 설정
    max_val = max(max(male_pop, default=1), max(female_pop, default=1))
    step = max(1, int(max_val / 4))
    ticks = list(range(0, max_val + step, step))
    tickvals = [-t for t in reversed(ticks[1:])] + ticks
    ticktext = [f"{t:,}" for t in reversed(ticks[1:])] + [f"{t:,}" for t in ticks]

    # 레이아웃 설정
    fig.update_layout(
        title=dict(
            text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}] 연령별 인구 피라미드 ({latest_year}년)</b>",
            font=dict(size=18, color="#2D3142")
        ),
        barmode="relative",
        bargap=0.1,
        paper_bgcolor="#FFFDFC",  # 따뜻한 백그라운드 톤
        plot_bgcolor="#FFFDFC",
        xaxis=dict(
            title="인구수 (명)",
            tickvals=tickvals,
            ticktext=ticktext,
            zeroline=True,
            zerolinecolor="#999999",
            zerolinewidth=1,
            gridcolor="#F0EFE9"
        ),
        # 세로축(나이) 순서 고정: 0세가 맨 아래, 100세 이상이 맨 위
        # age_labels 리스트 순서대로 축에 배치합니다.
        yaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=age_labels,
            title="연령(나이)",
            gridcolor="#F0EFE9"
        ),
        legend=dict(
            x=0.85,
            y=0.95,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#E2E2E2",
            borderwidth=1
        ),
        height=750,
        margin=dict(l=60, r=40, t=60, b=50)
    )

    # Streamlit 화면에 그래프 출력
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("선택한 지역의 데이터가 존재하지 않습니다.")
