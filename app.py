# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import platform
import matplotlib.pyplot as plt

# 한글 폰트 설정
system_name = platform.system()

if system_name == "Windows":
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif system_name == "Darwin":  # macOS
    plt.rcParams['font.family'] = 'AppleGothic'
else:  # Linux (Streamlit Cloud 포함)
    plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="📊 CSV 데이터 분석기", layout="wide")

st.title("📊 CSV 데이터 분석기 (업그레이드 버전)")

# ==========================
# 사이드바 옵션
# ==========================
with st.sidebar:
    st.header("옵션 설정")

    encoding_option = st.selectbox(
        "파일 인코딩 선택",
        ["utf-8", "cp949", "euc-kr", "utf-8-sig"]
    )

    drop_na = st.checkbox("결측치 제거", value=True)
    use_plotly = st.checkbox("Plotly 그래프 사용", value=False)

# ==========================
# 파일 업로드
# ==========================
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding=encoding_option)
        if drop_na:
            df = df.dropna()

        # ==========================
        # 데이터 탭
        # ==========================
        tab1, tab2 = st.tabs(["데이터 미리보기", "그래프 분석"])

        with tab1:
            st.subheader("🔍 데이터 미리보기")
            st.dataframe(df.head())

            st.subheader("📌 데이터 정보")
            st.write(f"행 개수: {df.shape[0]}")
            st.write(f"열 개수: {df.shape[1]}")

            st.subheader("📈 통계 요약")
            st.dataframe(df.describe())

            # CSV 다운로드
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 CSV 다운로드",
                csv,
                "processed_data.csv",
                "text/csv"
            )

        # ==========================
        # 그래프 탭
        # ==========================
        with tab2:
            numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if numeric_columns:
                st.subheader("📊 그래프 생성")

                # 다중 컬럼 선택
                selected_columns = st.multiselect(
                    "컬럼 선택 (여러개 가능)",
                    numeric_columns,
                    default=numeric_columns[:1]
                )

                if selected_columns:
                    # 그래프 옵션
                    selected_graph_type = st.selectbox("그래프 선택", ["막대 그래프", "꺾은선 그래프"])
                    graph_color = st.color_picker("그래프 색상 선택", "#1f77b4")
                    graph_title = st.text_input("그래프 제목 입력", "데이터 그래프")
                    x_label = st.text_input("X축 레이블 입력", "Index")
                    y_label = st.text_input("Y축 레이블 입력", "값")
                    show_legend = st.checkbox("범례 표시", value=True)
                    show_mean = st.checkbox("평균선 표시")
                    log_scale = st.checkbox("로그 스케일 사용")
                    # Matplotlib 스타일
                    style = st.selectbox("그래프 스타일 선택", plt.style.available)
                    plt.style.use(style)
                    fig_width = st.slider("그래프 가로 크기", 5, 20, 10)
                    fig_height = st.slider("그래프 세로 크기", 3, 15, 5)
                    # 데이터 범위 선택
                    start, end = st.slider(
                        "데이터 범위 선택",
                        0,
                        len(df)-1,
                        (0, min(50, len(df)-1))
                    )
                    filtered_df = df.iloc[start:end]

                    # ==========================
                    # 그래프 생성
                    # ==========================
                    if use_plotly:
                        import plotly.express as px
                        fig = px.line(
                            filtered_df,
                            y=selected_columns,
                            title=graph_title,
                            labels={col: y_label for col in selected_columns},
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                        for col in selected_columns:
                            if selected_graph_type == "막대 그래프":
                                ax.bar(filtered_df.index, filtered_df[col], label=col, color=graph_color)
                            elif selected_graph_type == "꺾은선 그래프":
                                ax.plot(filtered_df.index, filtered_df[col], label=col, color=graph_color, marker='o')

                            if show_mean:
                                mean_val = filtered_df[col].mean()
                                ax.axhline(mean_val, linestyle='--', color=graph_color, alpha=0.7)

                        ax.set_title(graph_title)
                        ax.set_xlabel(x_label)
                        ax.set_ylabel(y_label)
                        if log_scale:
                            ax.set_yscale('log')
                        if show_legend:
                            ax.legend()
                        ax.grid(True)
                        st.pyplot(fig)

                        # PNG 다운로드
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png")
                        buf.seek(0)
                        st.download_button(
                            label="📥 그래프 PNG 다운로드",
                            data=buf,
                            file_name=f"{'_'.join(selected_columns)}_graph.png",
                            mime="image/png"
                        )
            else:
                st.warning("숫자형 컬럼이 없습니다 😢")

    except Exception as e:
        st.error(f"파일을 읽는 중 오류 발생 😢\n{e}")
