# -*- coding: utf-8 -*-
import os
import io
import platform
import pandas as pd
import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# ==========================
# 📂 폰트 자동 감지 및 설정 로직 (안정성 강화 버전)
# ==========================
def get_local_fonts():
    """현재 폴더에 있는 모든 .ttf 및 .otf 폰트 파일을 자동으로 찾아오는 함수"""
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    files = os.listdir(current_dir)
    font_files = [f for f in files if f.lower().endswith(('.ttf', '.otf'))]
    
    font_dict = {}
    for f in font_files:
        try:
            prop = font_manager.FontProperties(fname=os.path.abspath(f))
            actual_name = prop.get_name()
            display_name = f"{actual_name} ({f})"
            font_dict[display_name] = f
        except:
            font_dict[f] = f
    return font_dict

def set_korean_font(font_filename):
    """화면 멈춤(하얀 화면)을 방지하며 나눔고딕 충돌을 안전하게 우회하는 함수"""
    if font_filename and os.path.exists(font_filename):
        try:
            font_abs_path = os.path.abspath(font_filename)
            
            # 1. 안전하게 폰트 파일만 추가 등록
            font_manager.fontManager.addfont(font_abs_path)
            prop = font_manager.FontProperties(fname=font_abs_path)
            font_name = prop.get_name()
            
            # 2. 전역 rcParams 설정을 폰트 패밀리 이름으로 고정
            rc('font', family=font_name)
            plt.rcParams['font.family'] = font_name
            
            # 3. 특이 테마 대응을 위해 폰트 리스트 맨 앞에 삽입
            if font_name not in plt.rcParams['font.sans-serif']:
                plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                
        except Exception as e:
            st.sidebar.error(f"⚠️ 폰트 로드 실패: {e}")
            fallback_system_font()
    else:
        fallback_system_font()
        
    plt.rcParams['axes.unicode_minus'] = False

def fallback_system_font():
    """안전 장치용 기본 시스템 폰트"""
    system_name = platform.system()
    if system_name == "Windows":
        rc('font', family='Malgun Gothic')
    elif system_name == "Darwin":
        rc('font', family='AppleGothic')
    else:
        rc('font', family='NanumGothic')

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
# 스트림릿 UI 시작
# ==========================
st.set_page_config(page_title="📊 CSV 데이터 분석기", layout="wide")
st.title("📊 CSV 데이터 분석기")

# 폴더 내 폰트 스캔
detected_fonts = get_local_fonts()

with st.sidebar:
    st.header("⚙️ 설정")
    data_source = st.radio("데이터 소스 선택", ["직접 업로드", "예시 데이터 사용"])
    
    if detected_fonts:
        selected_font_label = st.selectbox(
            "🔤 가져온 폰트 중 선택", 
            list(detected_fonts.keys()), 
            index=0,
            key="font_selector_stable"
        )
        selected_font_file = detected_fonts[selected_font_label]
    else:
        st.warning("⚠️ 폴더 내에 폰트 파일이 없습니다.")
        selected_font_file = None
    
    encoding_option = st.selectbox("파일 인코딩 (업로드 시)", ["utf-8", "cp949", "euc-kr", "utf-8-sig"])
    drop_na = st.checkbox("결측치 제거", value=True)
    use_plotly = st.checkbox("Plotly 그래프 사용 (인터랙티브)", value=False)

# 최초 폰트 설정
set_korean_font(selected_font_file)

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
                    # ✨ 그래프 종류에 산점도와 영역형 그래프 추가
                    graph_type = st.selectbox("그래프 종류", ["막대 그래프", "꺾은선 그래프", "산점도 (Scatter)", "영역형 그래프"])
                    graph_title = st.text_input("그래프 제목", "데이터 분석 결과")
                with col_cfg2:
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

                # 테마 설정 후 다시 한번 폰트 주입
                plt.style.use(style)
                set_korean_font(selected_font_file) 
                
                plt.close('all') 
                fig, ax = plt.subplots(figsize=(10, 5))
                
                x_data = df[df.columns[0]].astype(str).tolist()
                n_cols = len(selected_columns)
                
                # --- 📊 그래프 그리기 로직 (종류 분기) ---
                if graph_type == "막대 그래프":
                    import numpy as np
                    x_indexes = np.arange(len(x_data))
                    width = 0.6 / n_cols
                    
                    for idx, col in enumerate(selected_columns):
                        offset = (idx - (n_cols - 1) / 2) * width
                        ax.bar(x_indexes + offset, df[col], width=width, label=col, color=column_colors[col])
                    
                    ax.set_xticks(x_indexes)
                    ax.set_xticklabels(x_data, rotation=45)
                    
                elif graph_type == "꺾은선 그래프":
                    for col in selected_columns:
                        ax.plot(x_data, df[col], marker='o', linewidth=2, label=col, color=column_colors[col])
                    plt.xticks(rotation=45)
                    
                elif graph_type == "산점도 (Scatter)":
                    for col in selected_columns:
                        ax.scatter(x_data, df[col], s=100, label=col, color=column_colors[col], alpha=0.8, edgecolors='black')
                    plt.xticks(rotation=45)
                    
                elif graph_type == "영역형 그래프":
                    # 누적되지 않고 각각의 독립된 영역을 투명도(alpha)를 주어 겹쳐서 표현
                    for col in selected_columns:
                        ax.fill_between(x_data, df[col], label=col, color=column_colors[col], alpha=0.4)
                        ax.plot(x_data, df[col], color=column_colors[col], linewidth=1.5)
                    plt.xticks(rotation=45)

                if show_mean:
                    for col in selected_columns:
                        ax.axhline(df[col].mean(), color=column_colors[col], linestyle='--', alpha=0.6)

                # 개별 요소 텍스트 폰트 속성 직접 강제 적용 (안전성 확보)
                if selected_font_file and os.path.exists(selected_font_file):
                    font_p = font_manager.FontProperties(fname=os.path.abspath(selected_font_file))
                    ax.set_title(graph_title, pad=15, fontproperties=font_p)
                    ax.set_ylabel("수치", fontproperties=font_p)
                    ax.set_xlabel(df.columns[0], fontproperties=font_p)
                    for tick in ax.get_xticklabels():
                        tick.set_fontproperties(font_p)
                    for tick in ax.get_yticklabels():
                        tick.set_fontproperties(font_p)
                    if ax.get_legend():
                        plt.setp(ax.get_legend().get_texts(), fontproperties=font_p)
                else:
                    ax.set_title(graph_title, pad=15)
                    ax.set_ylabel("수치")
                    ax.set_xlabel(df.columns[0])

                ax.grid(True, linestyle=':', alpha=0.6)
                
                plt.tight_layout()
                st.pyplot(fig)

                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
                st.download_button("📥 그래프 결과 저장 (PNG)", buf.getvalue(), "graph_result.png", "image/png")
        else:
            st.warning("분석 가능한 숫자형 데이터가 없습니다.")
else:
    st.write("---")
    st.write("👈 사이드바에서 데이터를 업로드하거나 '예시 데이터 사용'을 선택해 주세요.")
