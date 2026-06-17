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

# 마커 모양 매핑 딕셔너리
MARKER_OPTIONS = {
    '원형 (●)': 'o',
    '사각형 (■)': 's',
    '삼각형 (▲)': '^',
    '다이아몬드 (◆)': 'D',
    '별형 (★)': '*',
    '점형 (·)': '.',
    'X형 (✖)': 'x'
}

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
                    # 그래프 종류 추가: 영역형, 히스토그램, 박스 플롯 추가
                    graph_type = st.selectbox("그래프 종류", ["막대 그래프", "꺾은선 그래프", "산점도 (Scatter)", "영역형 그래프", "히스토그램", "박스 플롯"])
                    graph_title = st.text_input("그래프 제목", "데이터 분석 결과")
                with col_cfg2:
                    style = st.selectbox("그래프 테마(Style)", plt.style.available, index=plt.style.available.index('default') if 'default' in plt.style.available else 0)
                    show_mean = st.checkbox("평균선 표시")

                # 컬럼별 스타일 설정 (색상 및 마커)
                st.write("🖌️ **컬럼별 스타일 지정**")
                column_styles = {}
                default_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
                marker_keys = list(MARKER_OPTIONS.keys())
                
                # 컬럼 수에 맞춰 동적으로 컬럼 레이아웃 생성
                cols_per_row = 4
                n_rows = (len(selected_columns) + cols_per_row - 1) // cols_per_row
                
                for row in range(n_rows):
                    st_cols = st.columns(cols_per_row)
                    for col_idx in range(cols_per_row):
                        idx = row * cols_per_row + col_idx
                        if idx < len(selected_columns):
                            col_name = selected_columns[idx]
                            with st_cols[col_idx]:
                                st.markdown(f"**{col_name}**")
                                # 색상 선택
                                color = st.color_picker(f"색상", default_colors[idx % len(default_colors)], key=f"color_{col_name}")
                                
                                # 마커 선택 (꺾은선, 산점도에서 사용)
                                marker_label = st.selectbox(f"점 모양", marker_keys, index=0, key=f"marker_{col_name}")
                                marker_code = MARKER_OPTIONS[marker_label]
                                
                                column_styles[col_name] = {'color': color, 'marker': marker_code}

                # 테마 설정 후 다시 한번 폰트 주입
                plt.style.use(style)
                set_korean_font(selected_font_file) 
                
                plt.close('all') 
                
                # 그래프 종류에 따라 Figure 생성 방식 다름 (박스 플롯, 히스토그램은 한 번에 그리기 용이)
                if graph_type in ["히스토그램", "박스 플롯"]:
                    # 이 종류들은 pandas plot이 더 간편할 수 있으나 폰트 유지를 위해 matplotlib ax 사용
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    if graph_type == "히스토그램":
                        # 여러 컬럼을 겹쳐 그리기 위해 반복문 사용
                        for col in selected_columns:
                            ax.hist(df[col], bins=20, alpha=0.5, label=col, color=column_styles[col]['color'], edgecolor='black')
                        ax.set_ylabel("빈도수")
                        ax.set_xlabel("값 범위")
                        ax.legend()
                    
                    elif graph_type == "박스 플롯":
                        # 1. 데이터셋을 순수한 파이썬 리스트로 강제 변환
                        clean_data = [list(df[col].dropna()) for col in selected_columns]
                        
                        # 2. 🔥 [핵심 수정] 라벨(컬럼명) 배열도 순수한 파이썬 문자열 리스트로 강제 변환
                        clean_labels = [str(col) for col in selected_columns]
                        
                        # 데이터가 존재하는지 안전 검사 후 그리기
                        if any(clean_data):
                            # labels에 순수 리스트인 clean_labels를 전달합니다.
                            bp = ax.boxplot(clean_data, labels=clean_labels, patch_artist=True)
                            
                            # 각 박스에 컬럼별 색상 적용
                            for patch, col in zip(bp['boxes'], selected_columns):
                                patch.set_facecolor(column_styles[col]['color'])
                                patch.set_alpha(0.7)
                            
                            # 중앙값 선 스타일 설정
                            plt.setp(bp['medians'], color='black', linewidth=1.5)
                            ax.set_ylabel("값 분포")
                        else:
                            st.warning("⚠️ 선택한 컬럼에 유효한 숫자 데이터가 없습니다.")
                else:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    x_data = df[df.columns[0]].astype(str).tolist()
                    n_cols = len(selected_columns)
                    
                    # 4. df.plot 대신 Matplotlib 순수 함수로 직접 제어 (테마 색상/폰트 꼬임 방지)
                    if graph_type == "막대 그래프":
                        import numpy as np
                        x_indexes = np.arange(len(x_data))
                        # 항목 간 간격 조정을 위해 너비 계산 수정
                        total_width = 0.8
                        width = total_width / n_cols
                        
                        for idx, col in enumerate(selected_columns):
                            offset = (idx - (n_cols - 1) / 2) * width
                            ax.bar(x_indexes + offset, df[col], width=width, label=col, color=column_styles[col]['color'])
                        
                        ax.set_xticks(x_indexes)
                        ax.set_xticklabels(x_data, rotation=45)
                    
                    elif graph_type == "꺾은선 그래프":
                        for col in selected_columns:
                            # 선택된 마커 모양 적용
                            ax.plot(x_data, df[col], marker=column_styles[col]['marker'], linewidth=2, markersize=8, label=col, color=column_styles[col]['color'])
                        plt.xticks(rotation=45)
                        
                    elif graph_type == "산점도 (Scatter)":
                        for col in selected_columns:
                            # 선택된 마커 모양 적용
                            ax.scatter(x_data, df[col], s=100, marker=column_styles[col]['marker'], label=col, color=column_styles[col]['color'], alpha=0.8, edgecolors='black')
                        plt.xticks(rotation=45)
                        
                    elif graph_type == "영역형 그래프":
                        # 누적되지 않고 각각 그리기 위해 fill_between 사용
                        for col in selected_columns:
                            ax.fill_between(x_data, df[col], label=col, color=column_styles[col]['color'], alpha=0.3)
                            # 테두리 선 추가
                            ax.plot(x_data, df[col], color=column_styles[col]['color'], linewidth=1)
                        plt.xticks(rotation=45)

                # 평균선 표시 (히스토그램, 박스플롯 제외)
                if show_mean and graph_type not in ["히스토그램", "박스 플롯"]:
                    for col in selected_columns:
                        ax.axhline(df[col].mean(), color=column_styles[col]['color'], linestyle='--', alpha=0.6)

                # 5. 제목 및 레이블에 폰트가 누락되지 않도록 명시적 설정
                if selected_font_file and os.path.exists(selected_font_file):
                    font_p = font_manager.FontProperties(fname=os.path.abspath(selected_font_file))
                    ax.set_title(graph_title, pad=15, fontproperties=font_p, fontsize=16)
                    
                    # 히스토그램, 박스플롯은 위에서 레이블 설정함
                    if graph_type not in ["히스토그램", "박스 플롯"]:
                        ax.set_ylabel("수치", fontproperties=font_p)
                        ax.set_xlabel(df.columns[0], fontproperties=font_p)
                    else:
                        # 이미 설정된 레이블 폰트 적용
                        ax.xaxis.label.set_fontproperties(font_p)
                        ax.yaxis.label.set_fontproperties(font_p)
                        
                    # 축 눈금 폰트 설정
                    for tick in ax.get_xticklabels():
                        tick.set_fontproperties(font_p)
                    for tick in ax.get_yticklabels():
                        tick.set_fontproperties(font_p)
                    
                    # 범례 폰트 설정 (존재할 경우)
                    if ax.get_legend():
                        plt.setp(ax.get_legend().get_texts(), fontproperties=font_p)
                        
                else:
                    # 시스템 폰트 사용 시 기본 설정
                    ax.set_title(graph_title, pad=15, fontsize=16)
                    if graph_type not in ["히스토그램", "박스 플롯"]:
                        ax.set_ylabel("수치")
                        ax.set_xlabel(df.columns[0])
                    
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
