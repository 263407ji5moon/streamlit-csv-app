# -*- coding: utf-8 -*-
import os
import shutil
import io
import platform
import pandas as pd
import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# ==========================
# 폰트 설정 로직
# ==========================
FONT_OPTIONS = {
    "나눔스퀘어 네오 - Light (aLt)": "NanumSquareNeo-aLt.ttf",
    "나눔스퀘어 네오 - Regular (bRg)": "NanumSquareNeo-bRg.ttf",
    "나눔스퀘어 네오 - Bold (cBd)": "NanumSquareNeo-cBd.ttf",
    "나눔스퀘어 네오 - ExtraBold (dEb)": "NanumSquareNeo-dEb.ttf",
    "나눔스퀘어 네오 - Heavy (eHv)": "NanumSquareNeo-eHv.ttf"
}

def set_korean_font(font_filename):
    """선택된 폰트 파일을 Matplotlib에 강제 주입"""
    try:
        cache_dir = mpl.get_cachedir()
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
    except:
        pass

    if os.path.exists(font_filename):
        try:
            font_abs_path = os.path.abspath(font_filename)
            font_manager.fontManager.addfont(font_abs_path)
            prop = font_manager.FontProperties(fname=font_abs_path)
            font_name = prop.get_name()
            
            # 전역 폰트 강제 확정
            rc('font', family=font_name)
            plt.rcParams['font.family'] = font_name
            plt.rcParams['font.sans-serif'] = [font_name]
        except Exception as e:
            st.error(f"폰트 적용 실패: {e}")
    else:
        system_name = platform.system()
        if system_name == "Windows":
            rc('font', family='Malgun Gothic')
        elif system_name == "Darwin":
            rc('font', family='AppleGothic')
        else:
            rc('font', family='NanumGothic')
            
    plt.rcParams['axes.unicode_minus'] = False

# ==========================
# 예시 데이터 생성 함수
# ==========================
def load_demo_data():
    data = {
        "월별": ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"],
        "매출액": [2500, 2800, 3200, 3100, 3500, 4000, 4500, 4200, 3800, 3600, 4100, 4800],
        "방문자수": [120, 150, 180, 170, 210, 250, 300, 280, 230, 210, 240, 310],
        "만족도": [85, 88, 90, 89, 92, 95, 94, 91, 89, 87, 90, 96]
    }
    return pd.DataFrame(data)

# ==========================
# 스트림릿 UI
# ==========================
st.set_page_config(page_title="📊 CSV 데이터 분석기", layout="wide")
st.title("📊 CSV 데이터 분석기")

with st.sidebar:
    st.header("⚙️ 설정")
    data_source = st.radio("데이터 소스 선택", ["직접 업로드", "예시 데이터 사용"])
    
    # 💡 @st.fragment 등을 쓰지 않고 폰트/테마 변경 시 화면이 정상 리렌더링되도록 트리거 보장
    selected_font_label = st.selectbox("한글 폰트 스타일 선택", list(FONT_OPTIONS.keys()), index=1)
    selected_font_file = FONT_OPTIONS[selected_font_label]
    
    encoding_option = st.selectbox("파일 인코딩 (업로드 시)", ["utf-8", "cp949", "euc-kr", "utf-8-sig"])
    drop_na = st.checkbox("결측치 제거", value=True)
    use_plotly = st.checkbox("Plotly 그래프 사용 (인터랙티브)", value=False)

# 데이터 로드
df = None
if data_source == "예시 데이터 사용":
    df = load_demo_data()
    st.info("💡 시연용 예시 데이터를 불러왔습니다.")
else:
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding=encoding_option)
            if drop_na:
                df = df.dropna()
        except Exception as e:
            st.error(f"파일 로드 오류: {e}")

if df is not None:
    tab1, tab2 = st.tabs(["🔍 데이터 미리보기", "📈 그래프 분석"])

    with tab1:
        st.subheader("📋 데이터셋 정보")
        col1, col2 = st.columns(2)
        col1.metric("행 개수", df.shape[0])
        col2.metric("열 개수", df.shape[1])
        st.dataframe(df, use_container_width=True)
        st.subheader("📊 통계 요약")
        st.dataframe(df.describe(), use_container_width=True)

    with tab2:
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if numeric_columns:
            st.subheader("🎨 그래프 설정")
            selected_columns = st.multiselect("분석할 컬럼을 선택하세요", numeric_columns, default=numeric_columns[:1])
            
            if selected_columns:
                col_cfg1, col_cfg2 = st.columns(2)
                with col_cfg1:
                    graph_type = st.selectbox("그래프 종류", ["막대 그래프", "꺾은선 그래프"])
                    graph_title = st.text_input("그래프 제목", "데이터 분석 결과")
                with col_cfg2:
                    # 사용 가능한 스타일 목록 필터링 (한글 테마가 잘 먹히는 테마들 위주)
                    style = st.selectbox("그래프 테마(Style)", plt.style.available, index=plt.style.available.index('default') if 'default' in plt.style.available else 0)
                    show_mean = st.checkbox("평균선 표시")

                # 컬럼별 색상 선택
                st.write("🖌️ **컬럼별 색상 지정**")
                color_pickers = st.columns(len(selected_columns))
                column_colors = {}
                default_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
                
                for idx, col in enumerate(selected_columns):
                    with color_pickers[idx % len(color_pickers)]:
                        column_colors[col] = st.color_picker(f"{col}", default_colors[idx % len(default_colors)])

                # ==========================================
                # 🔥 [핵심 고정] 테마와 폰트 실시간 결합 로직
                # ==========================================
                # 1. 테마를 가장 먼저 적용 (기존 폰트 세팅이 리셋됨)
                plt.style.use(style)
                # 2. 리셋된 테마 위에 폰트를 강제로 다시 입힘
                set_korean_font(selected_font_file) 

                if use_plotly:
                    import plotly.express as px
                    fig = px.line(df, x=df.columns[0], y=selected_columns, title=graph_title, color_discrete_map=column_colors)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # 3. Figure와 Ax를 명시적으로 생성하여 테마와 폰트 동기화 보장
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    x_data = df[df.columns[0]].astype(str).tolist()
                    n_cols = len(selected_columns)
                    
                    # 4. df.plot 대신 Matplotlib 순수 함수로 직접 제어 (테마 색상/폰트 꼬임 방지)
                    if graph_type == "막대 그래프":
                        import numpy as np
                        x_indexes = np.arange(len(x_data))
                        width = 0.6 / n_cols
                        
                        for idx, col in enumerate(selected_columns):
                            offset = (idx - (n_cols - 1) / 2) * width
                            ax.bar(x_indexes + offset, df[col], width=width, label=col, color=column_colors[col])
                        
                        ax.set_xticks(x_indexes)
                        ax.set_xticklabels(x_data, rotation=45)
                    else:
                        for col in selected_columns:
                            ax.plot(x_data, df[col], marker='o', linewidth=2, label=col, color=column_colors[col])
                        plt.xticks(rotation=45)

                    if show_mean:
                        for col in selected_columns:
                            ax.axhline(df[col].mean(), color=column_colors[col], linestyle='--', alpha=0.6)

                    # 5. 제목 및 레이블에 폰트가 누락되지 않도록 명시적 설정
                    ax.set_title(graph_title, pad=15)
                    ax.set_ylabel("수치")
                    ax.set_xlabel(df.columns[0])
                    ax.legend(loc="upper right")
                    ax.grid(True, linestyle=':', alpha=0.6)
                    
                    # 레이아웃 조정 후 출력
                    plt.tight_layout()
                    st.pyplot(fig)

                    # 이미지 다운로드
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
                    st.download_button("📥 그래프 결과 저장 (PNG)", buf.getvalue(), "graph_result.png", "image/png")
        else:
            st.warning("분석 가능한 숫자형 데이터가 없습니다.")
else:
    st.write("---")
    st.write("👈 사이드바에서 데이터를 업로드하거나 '예시 데이터 사용'을 선택해 주세요.")
