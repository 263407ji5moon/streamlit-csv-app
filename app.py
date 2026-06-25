# -*- coding: utf-8 -*-
import os
import io
import platform
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# ==========================
# 📂 폰트 자동 감지 및 설정 로직
# ==========================
def get_local_fonts():
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
st.set_page_config(page_title="📊 CSV 데이터 대시보드", layout="wide")
st.title("📊 CSV 데이터 종합 분석 대시보드")

detected_fonts = get_local_fonts()

MARKER_OPTIONS = {
    '원형 (●)': {'mpl': 'o', 'plotly': 'circle'},
    '사각형 (■)': {'mpl': 's', 'plotly': 'square'},
    '삼각형 (▲)': {'mpl': '^', 'plotly': 'triangle-up'},
    '다이아몬드 (◆)': {'mpl': 'D', 'plotly': 'diamond'},
    '별형 (★)': {'mpl': '*', 'plotly': 'star'},
    'X형 (✖)': {'mpl': 'x', 'plotly': 'x'}
}

with st.sidebar:
    st.header("⚙️ 기본 설정")
    data_source = st.radio("데이터 소스 선택", ["직접 업로드", "예시 데이터 사용"])
    
    if detected_fonts:
        selected_font_label = st.selectbox("🔤 가져온 폰트 중 선택", list(detected_fonts.keys()), index=0, key="font_selector_stable")
        selected_font_file = detected_fonts[selected_font_label]
    else:
        st.warning("⚠️ 폴더 내에 폰트 파일이 없습니다.")
        selected_font_file = None
    
    encoding_option = st.selectbox("파일 인코딩 (업로드 시)", ["utf-8", "cp949", "euc-kr", "utf-8-sig"])
    drop_na = st.checkbox("결측치 제거", value=True)
    use_plotly = st.checkbox("Plotly 그래프 사용 (인터랙티브)", value=False)

set_korean_font(selected_font_file)

# 데이터 로드 기본 프레임
raw_df = None
if data_source == "예시 데이터 사용":
    raw_df = load_demo_data()
    st.info("💡 시연용 예시 데이터를 불러왔습니다.")
else:
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file, encoding=encoding_option)
            if drop_na:
                raw_df = raw_df.dropna()
        except Exception as e:
            st.error(f"파일 로드 오류: {e}")

if raw_df is not None:
    df = raw_df.copy()
    
    # 🧮 파생 변수 계산기
    st.sidebar.markdown("---")
    st.sidebar.header("🧮 파생 변수 추가")
    calc_on = st.sidebar.checkbox("새로운 계산 컬럼 만들기")
    if calc_on:
        num_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if len(num_cols) >= 2:
            col_a = st.sidebar.selectbox("첫 번째 컬럼", num_cols, key="calc_a")
            op = st.sidebar.selectbox("연산자", ["+", "-", "*", "/"], key="calc_op")
            col_b = st.sidebar.selectbox("두 번째 컬럼", num_cols, key="calc_b")
            new_col_name = st.sidebar.text_input("새 컬럼 이름", "파생_지표")
            
            if st.sidebar.button("⚙️ 계산 및 컬럼 적용"):
                try:
                    if op == "+": df[new_col_name] = df[col_a] + df[col_b]
                    elif op == "-": df[new_col_name] = df[col_a] - df[col_b]
                    elif op == "*": df[new_col_name] = df[col_a] * df[col_b]
                    elif op == "/": df[new_col_name] = df[col_a] / df[col_b]
                    st.sidebar.success(f"'{new_col_name}' 열이 성공적으로 추가되었습니다!")
                except Exception as e:
                    st.sidebar.error(f"계산 실패: {e}")
        else:
            st.sidebar.warning("파생 변수를 만들려면 최소 2개 이상의 숫자 컬럼이 필요합니다.")

    # 🔍 데이터 필터링
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 데이터 범위 필터")
    min_row, max_row = st.sidebar.slider("분석할 행 범위 선택", 0, len(df), (0, len(df)))
    df = df.iloc[min_row:max_row].reset_index(drop=True)

    tab1, tab2 = st.tabs(["🔍 데이터 미리보기 및 요약", "📈 그래프 고급 분석"])

    with tab1:
        st.subheader("📋 데이터셋 정보")
        col1, col2 = st.columns(2)
        col1.metric("전체 행 개수 (필터링 적용)", df.shape[0])
        col2.metric("열 개수", df.shape[1])
        st.dataframe(df, use_container_width=True)
        st.subheader("📊 통계 요약")
        st.dataframe(df.describe(), use_container_width=True)

    with tab2:
        all_columns = df.columns.tolist()
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if numeric_columns:
            st.subheader("🎨 그래프 대시보드 설정")
            
            col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
            with col_cfg1:
                graph_type = st.selectbox("그래프 종류", ["산점도 (Scatter)", "꺾은선 그래프", "막대 그래프", "영역형 그래프", "히스토그램", "박스 플롯"])
                graph_title = st.text_input("그래프 제목", "데이터 분석 결과")
                x_col = st.selectbox("X축 컬럼 선택 (히스토그램/박스플롯 제외)", all_columns, index=0)
            with col_cfg2:
                style = st.selectbox("그래프 테마(Style)", plt.style.available, index=plt.style.available.index('default') if 'default' in plt.style.available else 0)
                selected_columns = st.multiselect("Y축 분석할 컬럼(숫자형)을 선택하세요", numeric_columns, default=numeric_columns[:1])
                show_mean = st.checkbox("평균선 표시")
            with col_cfg3:
                marker_size = st.slider("점/마커 크기", min_value=4, max_value=24, value=10, step=2)
                show_labels = st.checkbox("데이터 레이블(값) 표시", value=False)
                show_legend = st.checkbox("범례(Legend) 표시", value=True)
                show_trend = st.checkbox("📈 추세선(Trendline) 표시", value=True)

            if selected_columns:
                st.write("🖌️ **컬럼별 디자인 지정**")
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

                # ==========================================
                # 🚀 개의 분기처리 [1] Plotly 인터랙티브 그래프
                # ==========================================
                if use_plotly:
                    import plotly.express as px
                    import plotly.graph_objects as go
                    
                    p_font_name = "sans-serif"
                    if selected_font_file and os.path.exists(selected_font_file):
                        try: p_font_name = font_manager.FontProperties(fname=os.path.abspath(selected_font_file)).get_name()
                        except: pass

                    fig = go.Figure()

                    if graph_type == "막대 그래프":
                        for col in selected_columns:
                            fig.add_trace(go.Bar(x=df[x_col], y=df[col], name=col, 
                                                 marker_color=column_styles[col]['color'],
                                                 text=df[col] if show_labels else None, textposition='auto'))
                        fig.update_layout(barmode='group')

                    elif graph_type == "꺾은선 그래프":
                        for col in selected_columns:
                            mode_choice = 'lines+markers+text' if show_labels else 'lines+markers'
                            fig.add_trace(go.Scatter(x=df[x_col], y=df[col], name=col, mode=mode_choice,
                                                 line=dict(color=column_styles[col]['color'], width=2),
                                                 marker=dict(symbol=column_styles[col]['plotly_marker'], size=marker_size),
                                                 text=df[col] if show_labels else None, textposition='top center'))

                    elif graph_type == "산점도 (Scatter)":
                        for col in selected_columns:
                            mode_choice = 'markers+text' if show_labels else 'markers'
                            fig.add_trace(go.Scatter(x=df[x_col], y=df[col], name=col, mode=mode_choice,
                                                 marker=dict(symbol=column_styles[col]['plotly_marker'], size=marker_size + 2, color=column_styles[col]['color'],
                                                            line=dict(width=1, color='Black')),
                                                 text=df[col] if show_labels else None, textposition='top center'))

                    elif graph_type == "영역형 그래프":
                        for col in selected_columns:
                            mode_choice = 'lines+text' if show_labels else 'lines'
                            fig.add_trace(go.Scatter(x=df[x_col], y=df[col], name=col, mode=mode_choice, fill='tozeroy',
                                                 line=dict(color=column_styles[col]['color']), fillcolor=column_styles[col]['color'],
                                                 text=df[col] if show_labels else None, textposition='top center'))

                    elif graph_type == "히스토그램":
                        for col in selected_columns:
                            fig.add_trace(go.Histogram(x=df[col], name=col, marker_color=column_styles[col]['color'], opacity=0.6))
                        fig.update_layout(barmode='overlay')
                        if show_labels: fig.update_traces(texttemplate="%{y}", textposition="outside")

                    elif graph_type == "박스 플롯":
                        for col in selected_columns:
                            fig.add_trace(go.Box(y=df[col], name=col, marker_color=column_styles[col]['color'], boxpoints='all' if show_labels else 'outliers'))

                    # Plotly 추세선 로직
                    if show_trend and graph_type in ["꺾은선 그래프", "산점도 (Scatter)"]:
                        try:
                            x_numeric = pd.to_numeric(df[x_col], errors='coerce')
                            if x_numeric.isna().any():
                                x_calc = np.arange(len(df))
                            else:
                                x_calc = x_numeric.values
                                
                            for col in selected_columns:
                                mask = ~np.isnan(x_calc) & ~df[col].isna()
                                z = np.polyfit(x_calc[mask], df[col][mask], 1)
                                p = np.poly1d(z)
                                fig.add_trace(go.Scatter(x=df[x_col], y=p(x_calc), name=f"{col} 추세선",
                                                         line=dict(color=column_styles[col]['color'], dash='dot', width=2)))
                        except: pass

                    if show_mean and graph_type not in ["히스토그램", "박스 플롯"]:
                        for col in selected_columns:
                            fig.add_hline(y=df[col].mean(), line_dash="dash", line_color=column_styles[col]['color'], 
                                          annotation_text=f"{col} 평균", annotation_position="top right")

                    fig.update_layout(
                        title=graph_title,
                        xaxis_title=x_col if graph_type not in ["히스토그램", "박스 플롯"] else "",
                        yaxis_title="수치" if graph_type not in ["히스토그램", "박스 플롯"] else "",
                        font=dict(family=p_font_name, size=13),
                        template="plotly_white",
                        showlegend=show_legend
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
                                if show_labels:
                                    for count, bin_edge in zip(counts, bins):
                                        if count > 0: ax.text(bin_edge + (bins[1]-bins[0])/2, count, f'{int(count)}', ha='center', va='bottom', fontsize=9)
                            ax.set_ylabel("빈도수")
                            ax.set_xlabel("값 범위")
                            if show_legend: ax.legend()
                        elif graph_type == "박스 플롯":
                            df_box = df[selected_columns].dropna()
                            if not df_box.empty:
                                bp_dict = df_box.boxplot(ax=ax, patch_artist=True, return_type='dict')
                                for idx, col in enumerate(selected_columns):
                                    if idx < len(bp_dict['boxes']):
                                        bp_dict['boxes'][idx].set_facecolor(column_styles[col]['color'])
                                        bp_dict['boxes'][idx].set_alpha(0.7)
                                        if show_labels:
                                            med = df_box[col].median()
                                            ax.text(idx + 1, med, f'{med:.1f}', ha='center', va='bottom', fontweight='bold', color='black', bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.2'))
                                for median in bp_dict['medians']:
                                    median.set_color('black')
                                    median.set_linewidth(1.5)
                                ax.set_ylabel("값 분포")
                                ax.grid(True, linestyle=':', alpha=0.6)
                    else:
                        # 🔥 [핵심 수정] X축이 숫자 컬럼일 때 문자열 강제 변환을 취소하고 원래 데이터 타입을 유지합니다.
                        x_numeric_check = pd.to_numeric(df[x_col], errors='coerce')
                        is_x_string = x_numeric_check.isna().any()
                        
                        if is_x_string:
                            x_data = df[x_col].astype(str).tolist()
                        else:
                            x_data = df[x_col].values  # 숫자형 스케일 그대로 좌표축 유지
                        
                        n_cols = len(selected_columns)
                        
                        if graph_type == "막대 그래프":
                            if is_x_string:
                                x_indexes = np.arange(len(x_data))
                                width = 0.8 / n_cols
                                for idx, col in enumerate(selected_columns):
                                    offset = (idx - (n_cols - 1) / 2) * width
                                    bars = ax.bar(x_indexes + offset, df[col], width=width, label=col, color=column_styles[col]['color'])
                                    if show_labels: ax.bar_label(bars, padding=3, fmt='%g', fontsize=9)
                                ax.set_xticks(x_indexes)
                                ax.set_xticklabels(x_data, rotation=45)
                            else:
                                # 숫자로 된 막대 그래프일 때 간격 자동 조정
                                width = (x_data.max() - x_data.min()) / len(x_data) * 0.2 if len(x_data) > 1 else 0.8
                                for idx, col in enumerate(selected_columns):
                                    offset = (idx - (n_cols - 1) / 2) * width
                                    bars = ax.bar(x_data + offset, df[col], width=width, label=col, color=column_styles[col]['color'])
                                    if show_labels: ax.bar_label(bars, padding=3, fmt='%g', fontsize=9)

                        elif graph_type == "꺾은선 그래프":
                            for col in selected_columns:
                                # X축과 Y축 정렬을 위해 정렬된 인덱스 기준으로 매핑
                                sort_idx = np.argsort(x_data) if not is_x_string else np.arange(len(x_data))
                                ax.plot(x_data[sort_idx], df[col].values[sort_idx], marker=column_styles[col]['mpl_marker'], linewidth=2, markersize=marker_size, label=col, color=column_styles[col]['color'])
                                if show_labels:
                                    for x, y in zip(x_data, df[col]): ax.text(x, y, f'{y:g}', ha='center', va='bottom', fontsize=9)
                            if is_x_string: plt.xticks(rotation=45)
                            
                        elif graph_type == "산점도 (Scatter)":
                            for col in selected_columns:
                                ax.scatter(x_data, df[col], s=marker_size**2, marker=column_styles[col]['mpl_marker'], label=col, color=column_styles[col]['color'], alpha=0.8, edgecolors='black')
                                if show_labels:
                                    for x, y in zip(x_data, df[col]): ax.text(x, y, f'{y:g}', ha='center', va='bottom', fontsize=9)
                            if is_x_string: plt.xticks(rotation=45)
                            
                        elif graph_type == "영역형 그래프":
                            for col in selected_columns:
                                sort_idx = np.argsort(x_data) if not is_x_string else np.arange(len(x_data))
                                ax.fill_between(x_data[sort_idx], df[col].values[sort_idx], label=col, color=column_styles[col]['color'], alpha=0.3)
                                ax.plot(x_data[sort_idx], df[col].values[sort_idx], color=column_styles[col]['color'], linewidth=1)
                                if show_labels:
                                    for x, y in zip(x_data, df[col]): ax.text(x, y, f'{y:g}', ha='center', va='bottom', fontsize=9)
                            if is_x_string: plt.xticks(rotation=45)

                        # 🔥 [Matplotlib 추세선 수정] 가상 인덱스가 아닌, 진짜 좌표 숫자를 대입하여 연산하도록 변경
                        if show_trend and graph_type in ["꺾은선 그래프", "산점도 (Scatter)"]:
                            try:
                                if is_x_string:
                                    x_calc = np.arange(len(df))
                                else:
                                    x_calc = x_data
                                    
                                for col in selected_columns:
                                    mask = ~np.isnan(x_calc) & ~df[col].isna()
                                    z = np.polyfit(x_calc[mask], df[col][mask], 1)
                                    p = np.poly1d(z)
                                    
                                    if is_x_string:
                                        ax.plot(x_data, p(x_calc), color=column_styles[col]['color'], linestyle=':', linewidth=2, label=f"{col} 추세선")
                                    else:
                                        # 숫자 스케일일 때는 정렬된 X좌표 범위로 추세선 출력
                                        x_line = np.linspace(x_calc.min(), x_calc.max(), 100)
                                        ax.plot(x_line, p(x_line), color=column_styles[col]['color'], linestyle=':', linewidth=2, label=f"{col} 추세선")
                            except: pass
                        
                        if show_legend: ax.legend()

                    if show_mean and graph_type not in ["히스토그램", "박스 플롯"]:
                        for col in selected_columns:
                            ax.axhline(df[col].mean(), color=column_styles[col]['color'], linestyle='--', alpha=0.6)

                    # 폰트 스타일 상속 매핑
                    if selected_font_file and os.path.exists(selected_font_file):
                        font_p = font_manager.FontProperties(fname=os.path.abspath(selected_font_file))
                        ax.set_title(graph_title, pad=15, fontproperties=font_p, fontsize=16)
                        if graph_type not in ["히스토그램", "박스 플롯"]:
                            ax.set_ylabel("수치", fontproperties=font_p)
                            ax.set_xlabel(x_col, fontproperties=font_p)
                        else:
                            ax.xaxis.label.set_fontproperties(font_p)
                            ax.yaxis.label.set_fontproperties(font_p)
                        for tick in ax.get_xticklabels(): tick.set_fontproperties(font_p)
                        for tick in ax.get_yticklabels(): tick.set_fontproperties(font_p)
                        if show_legend and ax.get_legend(): plt.setp(ax.get_legend().get_texts(), fontproperties=font_p)
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
