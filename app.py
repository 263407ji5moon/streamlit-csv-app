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
# 📂 폰트 자동 감지 및 설정 로직
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
    """화면 멈춤을 방지하며 한글 깨짐을 우회하는 안전 함수"""
    if font_filename and os.path.exists(font_filename):
        try:
            font_abs_path = os.path.abspath(font_filename)
            font_manager.fontManager.addfont(font_abs_path)
            prop = font_manager.FontProperties(fname=font_abs_path)
            font_name = prop.get_name()
            
            rc('font', family=font_name)
            plt.rcParams['font.family'] = font_name
            
            if font_name not in plt.rcParams['font.sans-serif']:
                plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
        except Exception as e:
            st.sidebar.error(f"⚠️ 폰트 로드 실패: {e}")
            fallback_system_font()
    else:
        fallback_system_font()
        
    plt.rcParams['axes.unicode_minus'] = False

def fallback_system_font():
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

detected_fonts = get_local_fonts()

# 마커 모양 매핑
MARKER_OPTIONS = {
    '원형 (●)': {'mpl': 'o', 'plotly': 'circle'},
    '사각형 (■)': {'mpl': 's', 'plotly': 'square'},
    '삼각형 (▲)': {'mpl': '^', 'plotly': 'triangle-up'},
    '다이아몬드 (◆)': {'mpl': 'D', 'plotly': 'diamond'},
    '별형 (★)': {'mpl': '*', 'plotly': 'star'},
    'X형 (✖)': {'mpl': 'x', 'plotly': 'x'}
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
                col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
                with col_cfg1:
                    graph_type = st.selectbox("그래프 종류", ["막대 그래프", "꺾은선 그래프", "산점도 (Scatter)", "영역형 그래프", "히스토그램", "박스 플롯"])
                    graph_title = st.text_input("그래프 제목", "데이터 분석 결과")
                with col_cfg2:
                    style = st.selectbox("그래프 테마(Style)", plt.style.available, index=plt.style.available.index('default') if 'default' in plt.style.available else 0)
                    show_mean = st.checkbox("평균선 표시")
                with col_cfg3:
                    # 🔥 [추가] 점 크기 조절 슬라이더 및 레이블(값) 표시 토글
                    marker_size = st.slider("점/마커 크기", min_value=4, max_value=24, value=10, step=2)
                    show_labels = st.checkbox("데이터 레이블(값) 표시", value=False)

                # 컬럼별 스타일 설정
                st.write("🖌️ **컬럼별 스타일 지정**")
                column_styles = {}
                default_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
                marker_keys = list(MARKER_OPTIONS.keys())
                
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
                                color = st.color_picker(f"색상", default_colors[idx % len(default_colors)], key=f"color_{col_name}")
                                marker_label = st.selectbox(f"점 모양", marker_keys, index=0, key=f"marker_{col_name}")
                                column_styles[col_name] = {
                                    'color': color, 
                                    'mpl_marker': MARKER_OPTIONS[marker_label]['mpl'],
                                    'plotly_marker': MARKER_OPTIONS[marker_label]['plotly']
                                }

                x_col = df.columns[0]

                # ==========================================
                # 🚀 개의 분기처리 [1] Plotly 인터랙티브 그래프
                # ==========================================
                if use_plotly:
                    import plotly.express as px
                    import plotly.graph_objects as go
                    
                    p_font_name = "sans-serif"
                    if selected_font_file and os.path.exists(selected_font_file):
                        try:
                            p_font_name = font_manager.FontProperties(fname=os.path.abspath(selected_font_file)).get_name()
                        except:
                            pass

                    fig = go.Figure()
                    
                    # 레이블 모드 텍스트 정의
                    text_template = "%{y}" if show_labels else None

                    if graph_type == "막대 그래프":
                        for col in selected_columns:
                            fig.add_trace(go.Bar(x=df[x_col], y=df[col], name=col, 
                                                 marker_color=column_styles[col]['color'],
                                                 text=df[col] if show_labels else None,
                                                 textposition='auto'))
                        fig.update_layout(barmode='group')

                    elif graph_type == "꺾은선 그래프":
                        for col in selected_columns:
                            line, = ax.plot(x_data, df[col], marker=column_styles[col]['mpl_marker'], linewidth=2, markersize=marker_size, label=col, color=column_styles[col]['color'])
                
                            # 꺾은선 레이블 부착 (🔥 %g -> :g 로 수정)
                            if show_labels:
                                for x, y in zip(x_data, df[col]):
                                    ax.text(x, y, f'{y:g}', ha='center', va='bottom', fontsize=9)
                        plt.xticks(rotation=45)
                            
                    elif graph_type == "산점도 (Scatter)":
                        for col in selected_columns:
                            ax.scatter(x_data, df[col], s=marker_size**2, marker=column_styles[col]['mpl_marker'], label=col, color=column_styles[col]['color'], alpha=0.8, edgecolors='black')
                                
                            # 산점도 레이블 부착 (🔥 %g -> :g 로 수정)
                            if show_labels:
                                for x, y in zip(x_data, df[col]):
                                    ax.text(x, y, f'{y:g}', ha='center', va='bottom', fontsize=9)
                            plt.xticks(rotation=45)
                            
                    elif graph_type == "영역형 그래프":
                            for col in selected_columns:
                                ax.fill_between(x_data, df[col], label=col, color=column_styles[col]['color'], alpha=0.3)
                                ax.plot(x_data, df[col], color=column_styles[col]['color'], linewidth=1)
                                
                                # 영역형 레이블 부착 (🔥 %g -> :g 로 수정)
                                if show_labels:
                                    for x, y in zip(x_data, df[col]):
                                        ax.text(x, y, f'{y:g}', ha='center', va='bottom', fontsize=9)
                            plt.xticks(rotation=45)
                    elif graph_type == "히스토그램":
                        for col in selected_columns:
                            fig.add_trace(go.Histogram(x=df[col], name=col, marker_color=column_styles[col]['color'], opacity=0.6))
                        fig.update_layout(barmode='overlay')
                        if show_labels:
                            fig.update_traces(texttemplate="%{y}", textposition="outside")

                    elif graph_type == "박스 플롯":
                        for col in selected_columns:
                            fig.add_trace(go.Box(y=df[col], name=col, marker_color=column_styles[col]['color'], boxpoints='all' if show_labels else 'outliers'))

                    # 공통 평균선 옵션
                    if show_mean and graph_type not in ["히스토그램", "박스 플롯"]:
                        for col in selected_columns:
                            m_val = df[col].mean()
                            fig.add_hline(y=m_val, line_dash="dash", line_color=column_styles[col]['color'], 
                                          annotation_text=f"{col} 평균", annotation_position="top right")

                    fig.update_layout(
                        title=graph_title,
                        xaxis_title=x_col if graph_type not in ["히스토그램", "박스 플롯"] else "",
                        yaxis_title="수치" if graph_type not in ["히스토그램", "박스 플롯"] else "",
                        font=dict(family=p_font_name, size=13),
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # ==========================================
                # 📊 개의 분기처리 [2] Matplotlib 기본 그래프
                # ==========================================
                else:
                    plt.style.use(style)
                    set_korean_font(selected_font_file) 
                    plt.close('all') 
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    if graph_type in ["히스토그램", "박스 플롯"]:
                        if graph_type == "히스토그램":
                            for col in selected_columns:
                                counts, bins, patches = ax.hist(df[col], bins=20, alpha=0.5, label=col, color=column_styles[col]['color'], edgecolor='black')
                                # 히스토그램 레이블 추가
                                if show_labels:
                                    for count, bin_edge in zip(counts, bins):
                                        if count > 0:
                                            ax.text(bin_edge + (bins[1]-bins[0])/2, count, f'{int(count)}', ha='center', va='bottom', fontsize=9)
                            ax.set_ylabel("빈도수")
                            ax.set_xlabel("값 범위")
                            ax.legend()
                        elif graph_type == "박스 플롯":
                            df_box = df[selected_columns].dropna()
                            if not df_box.empty:
                                bp_dict = df_box.boxplot(ax=ax, patch_artist=True, return_type='dict')
                                for idx, col in enumerate(selected_columns):
                                    if idx < len(bp_dict['boxes']):
                                        bp_dict['boxes'][idx].set_facecolor(column_styles[col]['color'])
                                        bp_dict['boxes'][idx].set_alpha(0.7)
                                        
                                        # 박스 플롯 값 레이블 추가 (중앙값 및 기본 통계치)
                                        if show_labels:
                                            med = df_box[col].median()
                                            ax.text(idx + 1, med, f'{med:.1f}', ha='center', va='bottom', fontweight='bold', color='black', bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.2'))
                                            
                                for median in bp_dict['medians']:
                                    median.set_color('black')
                                    median.set_linewidth(1.5)
                                ax.set_ylabel("값 분포")
                                ax.grid(True, linestyle=':', alpha=0.6)
                    else:
                        x_data = df[x_col].astype(str).tolist()
                        n_cols = len(selected_columns)
                        
                        if graph_type == "막대 그래프":
                            import numpy as np
                            x_indexes = np.arange(len(x_data))
                            width = 0.8 / n_cols
                            for idx, col in enumerate(selected_columns):
                                offset = (idx - (n_cols - 1) / 2) * width
                                bars = ax.bar(x_indexes + offset, df[col], width=width, label=col, color=column_styles[col]['color'])
                                
                                # 막대 그래프 레이블 부착
                                if show_labels:
                                    ax.bar_label(bars, padding=3, fmt='%g', fontsize=9)
                                    
                            ax.set_xticks(x_indexes)
                            ax.set_xticklabels(x_data, rotation=45)
                        
                        elif graph_type == "꺾은선 그래프":
                            for col in selected_columns:
                                line, = ax.plot(x_data, df[col], marker=column_styles[col]['mpl_marker'], linewidth=2, markersize=marker_size, label=col, color=column_styles[col]['color'])
                                
                                # 꺾은선 레이블 부착
                                if show_labels:
                                    for x, y in zip(x_data, df[col]):
                                        ax.text(x, y, f'{y:%g}', ha='center', va='bottom', fontsize=9)
                            plt.xticks(rotation=45)
                            
                        elif graph_type == "산점도 (Scatter)":
                            for col in selected_columns:
                                ax.scatter(x_data, df[col], s=marker_size**2, marker=column_styles[col]['mpl_marker'], label=col, color=column_styles[col]['color'], alpha=0.8, edgecolors='black')
                                
                                # 산점도 레이블 부착
                                if show_labels:
                                    for x, y in zip(x_data, df[col]):
                                        ax.text(x, y, f'{y:%g}', ha='center', va='bottom', fontsize=9)
                            plt.xticks(rotation=45)
                            
                        elif graph_type == "영역형 그래프":
                            for col in selected_columns:
                                ax.fill_between(x_data, df[col], label=col, color=column_styles[col]['color'], alpha=0.3)
                                ax.plot(x_data, df[col], color=column_styles[col]['color'], linewidth=1)
                                
                                if show_labels:
                                    for x, y in zip(x_data, df[col]):
                                        ax.text(x, y, f'{y:%g}', ha='center', va='bottom', fontsize=9)
                            plt.xticks(rotation=45)

                    if show_mean and graph_type not in ["히스토그램", "박스 플롯"]:
                        for col in selected_columns:
                            ax.axhline(df[col].mean(), color=column_styles[col]['color'], linestyle='--', alpha=0.6)

                    # 폰트 매핑 스타일 적용
                    if selected_font_file and os.path.exists(selected_font_file):
                        font_p = font_manager.FontProperties(fname=os.path.abspath(selected_font_file))
                        ax.set_title(graph_title, pad=15, fontproperties=font_p, fontsize=16)
                        if graph_type not in ["히스토그램", "박스 플롯"]:
                            ax.set_ylabel("수치", fontproperties=font_p)
                            ax.set_xlabel(x_col, fontproperties=font_p)
                        else:
                            ax.xaxis.label.set_fontproperties(font_p)
                            ax.yaxis.label.set_fontproperties(font_p)
                        for tick in ax.get_xticklabels():
                            tick.set_fontproperties(font_p)
                        for tick in ax.get_yticklabels():
                            tick.set_fontproperties(font_p)
                        if ax.get_legend():
                            plt.setp(ax.get_legend().get_texts(), fontproperties=font_p)
                    else:
                        ax.set_title(graph_title, pad=15, fontsize=16)
                        if graph_type not in ["히스토그램", "박스 플롯"]:
                            ax.set_ylabel("수치")
                            ax.set_xlabel(x_col)
                        
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
