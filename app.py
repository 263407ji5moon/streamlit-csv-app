def set_korean_font(font_filename):
    """나눔고딕 충돌 우회 및 Matplotlib 메모리 완전 리셋 함수"""
    try:
        # 1. 캐시 디렉토리 삭제
        cache_dir = mpl.get_cachedir()
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
    except:
        pass

    if font_filename and os.path.exists(font_filename):
        try:
            # 2. 폰트 매니저 초기화
            font_manager.fontManager = font_manager.FontManager()
            font_abs_path = os.path.abspath(font_filename)
            
            # 3. 폰트 파일 정보 읽기
            prop = font_manager.FontProperties(fname=font_abs_path)
            font_name = prop.get_name()
            
            # 🔥 [핵심 추가] 오직 'NanumGothic'일 때만 발생하는 이름 충돌 우회
            if "nanumgothic" in font_filename.lower() or "nanumgothic" in font_name.lower():
                # 나눔고딕은 시스템 선점 이름과 겹치므로 완전히 새로운 임의의 이름으로 강제 명명합니다.
                font_name = "ForcedNanumGothic"
                prop.set_name(font_name)
            
            # 4. 매트플롯립에 새로운 이름과 경로로 강제 등록
            font_manager.fontManager.addfont(font_abs_path)
            
            # 5. 전역 설정 주입
            rc('font', family=font_name)
            plt.rcParams['font.family'] = font_name
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            
        except Exception as e:
            st.error(f"폰트 적용 실패: {e}")
            fallback_system_font()
    else:
        fallback_system_font()
        
    plt.rcParams['axes.unicode_minus'] = False
