# aem_qa_station/app.py (Corrected Version)

import streamlit as st
import pandas as pd
import io
from typing import List, Dict, Optional
from datetime import datetime

# Import modules
from modules.connections import get_db
from modules.analyzer import PageAnalyzer, get_text_changes_only
from modules.searcher import TranslationSearcher, format_recommendation_for_display
from modules.version_manager import create_version_selector, display_version_summary

# Page configuration
st.set_page_config(
    page_title="AEM Translation QA Workstation",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    session_defaults = {
        'uploaded_pages': [],
        'selected_page': None,
        'analysis_results': {},
        'comparison_settings': {
            'source_version': None,
            'source_number': None,
            'target_version': None,
            'target_number': None
        },
        'selected_page_for_detail': None
    }
    
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def parse_csv_pages(uploaded_file) -> List[str]:
    """업로드된 CSV에서 페이지 URL 목록을 추출"""
    try:
        df = pd.read_csv(uploaded_file)
        
        # 컬럼 찾기 우선순위
        column_candidates = [
            'Page Path',  # 정확한 이름
            *[col for col in df.columns if col.lower() == 'page path'],  # 대소문자 무시
            *[col for col in df.columns if 'page' in col.lower() and 'path' in col.lower()],  # 부분 매칭
            *[col for col in df.columns if any(keyword in col.lower() for keyword in ['url', 'path', 'page', 'link'])]  # 관련 키워드
        ]
        
        # 첫 번째로 찾은 컬럼 사용
        selected_column = None
        for candidate in column_candidates:
            if candidate in df.columns:
                selected_column = candidate
                break
        
        if not selected_column:
            st.error("❌ 페이지 경로 컬럼을 찾을 수 없습니다.")
            with st.expander("사용 가능한 컬럼 목록"):
                for col in df.columns:
                    st.write(f"- {col}")
            return []
        
        # 페이지 목록 추출 및 검증
        pages = df[selected_column].dropna().astype(str).str.strip()
        pages = pages[pages != 'nan'].unique().tolist()
        
        # 유효한 페이지 경로만 필터링
        valid_pages = []
        for page in pages:
            if page and ('/content/' in page or page.startswith('/')):
                valid_pages.append(page)
        
        if selected_column != 'Page Path':
            st.warning(f"⚠️ '{selected_column}' 컬럼을 페이지 경로로 사용합니다.")
        
        st.success(f"✅ {len(valid_pages)}개 페이지 발견")
        return valid_pages
        
    except Exception as e:
        st.error(f"❌ CSV 파싱 오류: {str(e)}")
        return []

def create_version_comparison_settings() -> bool:
    """버전 비교 설정 UI - 성공 여부 반환"""
    st.subheader("⚙️ 버전 비교 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📤 소스 버전 (Source)**")
        source_version, source_number = create_version_selector("소스", "source")
    
    with col2:
        st.markdown("**📥 타겟 버전 (Target)**")
        target_version, target_number = create_version_selector("타겟", "target")
    
    # 설정 검증 및 저장
    if all([source_version, source_number, target_version, target_number]):
        st.session_state.comparison_settings.update({
            'source_version': source_version,
            'source_number': source_number,
            'target_version': target_version,
            'target_number': target_number
        })
        
        st.success(f"✅ 비교 설정: {source_version} v{source_number} ↔ {target_version} v{target_number}")
        return True
    else:
        st.error("❌ 소스와 타겟 버전을 모두 선택해주세요.")
        return False

def analyze_pages_with_progress(pages: List[str], settings: Dict) -> List[Dict]:
    """페이지 분석을 진행률과 함께 수행"""
    if not pages:
        return []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    dashboard_data = []
    analyzer = PageAnalyzer()
    
    for i, page in enumerate(pages):
        status_text.text(f"분석 중: {page} ({i+1}/{len(pages)})")
        progress_bar.progress((i + 1) / len(pages))
        
        try:
            # 캐시 키 생성
            cache_key = f"{page}_{settings['source_version']}_v{settings['source_number']}_{settings['target_version']}_v{settings['target_number']}"
            
            # 캐시 확인
            if cache_key not in st.session_state.analysis_results:
                analysis = analyzer.analyze_page_changes_with_versions(
                    page_path=page,
                    source_version=settings['source_version'],
                    source_version_number=settings['source_number'],
                    target_version=settings['target_version'],
                    target_version_number=settings['target_number']
                )
                st.session_state.analysis_results[cache_key] = analysis
            else:
                analysis = st.session_state.analysis_results[cache_key]
            
            # 대시보드 데이터 생성
            summary = analysis['analysis_summary']
            total_components = sum([
                summary['total_added'], summary['total_modified'], 
                summary['total_removed'], summary['total_unchanged']
            ])
            
            qa_items = summary['total_added'] + summary['total_modified']
            change_rate = (qa_items / total_components * 100) if total_components > 0 else 0
            
            dashboard_data.append({
                'Page Path': page,
                'Total': total_components,
                'Added': summary['total_added'],
                'Modified': summary['total_modified'], 
                'Deleted': summary['total_removed'],
                'Unchanged': summary['total_unchanged'],
                'QA Items': qa_items,
                'Change Rate': change_rate,
                'Status': get_page_status(summary),
                'Cache Key': cache_key
            })
            
        except Exception as e:
            st.error(f"❌ {page} 분석 실패: {str(e)}")
            dashboard_data.append({
                'Page Path': page,
                'Total': 0, 'Added': 0, 'Modified': 0, 'Deleted': 0, 'Unchanged': 0,
                'QA Items': 0, 'Change Rate': 0,
                'Status': f"오류: {str(e)}", 'Cache Key': None
            })
    
    status_text.text("✅ 분석 완료!")
    progress_bar.progress(100)
    
    return dashboard_data

def generate_excel_report(dashboard_data: List[Dict], settings: Dict) -> Optional[bytes]:
    """Excel 리포트 생성"""
    try:
        # 상세 변경사항 데이터 수집
        detailed_data = []
        for row in dashboard_data:
            cache_key = row['Cache Key']
            if cache_key and cache_key in st.session_state.analysis_results:
                analysis = st.session_state.analysis_results[cache_key]
                page_path = analysis['page_path']
                
                # 각 변경 유형별로 데이터 추가
                for change_type, change_list in analysis['changes'].items():
                    for change in change_list:
                        detailed_data.append({
                            'Page Path': page_path,
                            'Change Type': change_type.title(),
                            'Component Path': change.get('component_path', ''),
                            'Component Type': change.get('component_type', ''),
                            'Source Content': change.get('content', change.get('source_content', '')),
                            'Target Content': change.get('target_content', '')
                        })
        
        # Excel 파일 생성
        output = io.BytesIO()
        
        # openpyxl 사용을 위한 import 확인
        try:
            import openpyxl
        except ImportError:
            st.error("❌ openpyxl 라이브러리가 필요합니다. pip install openpyxl")
            return None
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 요약 시트
            summary_df = pd.DataFrame(dashboard_data)
            # Cache Key 컬럼 제거 (내부용)
            if 'Cache Key' in summary_df.columns:
                summary_df = summary_df.drop('Cache Key', axis=1)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # 상세 변경사항 시트
            if detailed_data:
                detail_df = pd.DataFrame(detailed_data)
                detail_df.to_excel(writer, sheet_name='Detailed Changes', index=False)
            
            # 리포트 정보 시트
            report_info = pd.DataFrame([{
                'Source Version': f"{settings['source_version']} v{settings['source_number']}",
                'Target Version': f"{settings['target_version']} v{settings['target_number']}",
                'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Total Pages': len(dashboard_data),
                'Pages with Changes': len([d for d in dashboard_data if d['QA Items'] > 0])
            }])
            report_info.to_excel(writer, sheet_name='Report Info', index=False)
        
        return output.getvalue()
        
    except Exception as e:
        st.error(f"❌ Excel 리포트 생성 실패: {str(e)}")
        return None

def display_dashboard_with_filters(dashboard_data: List[Dict]):
    """필터링 및 정렬 기능이 있는 대시보드 표시"""
    if not dashboard_data:
        st.info("표시할 데이터가 없습니다.")
        return
    
    df = pd.DataFrame(dashboard_data)
    
    # 필터 및 정렬 UI
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write("📊 **페이지 변경사항 요약**")
    
    with col2:
        status_filter = st.selectbox(
            "상태 필터:",
            ["전체", "QA 필요", "변경사항 있음", "변경사항 없음"],
            key="status_filter"
        )
    
    with col3:
        sort_option = st.selectbox(
            "정렬 기준:",
            ["QA 항목 많은 순", "QA 항목 적은 순", "전체 컴포넌트 순", "변경률 순"],
            key="sort_option"
        )
    
    # 필터 적용
    if status_filter != "전체":
        filter_mapping = {
            "QA 필요": lambda x: 'QA Required' in x,
            "변경사항 있음": lambda x: any(keyword in x for keyword in ['QA Required', 'Changes Detected']),
            "변경사항 없음": lambda x: 'No Changes' in x
        }
        
        if status_filter in filter_mapping:
            df = df[df['Status'].apply(filter_mapping[status_filter])]
    
    # 정렬 적용
    sort_mapping = {
        "QA 항목 많은 순": ('QA Items', False),
        "QA 항목 적은 순": ('QA Items', True),
        "전체 컴포넌트 순": ('Total', False),
        "변경률 순": ('Change Rate', False)
    }
    
    if sort_option in sort_mapping:
        sort_column, ascending = sort_mapping[sort_option]
        df = df.sort_values(sort_column, ascending=ascending)
    
    # 결과 표시
    display_page_results(df)

def display_page_results(df: pd.DataFrame):
    """페이지 결과를 카드 형태로 표시"""
    if df.empty:
        st.info("필터 조건에 맞는 페이지가 없습니다.")
        return
    
    for idx, row in df.iterrows():
        page_path = row['Page Path']
        cache_key = row['Cache Key']
        
        with st.container():
            col1, col2 = st.columns([6, 1])
            
            with col1:
                # 페이지 정보 표시
                short_path = page_path.replace('/content/illumina-marketing/', '.../')
                st.write(f"**{short_path}**")
                st.write(f"{row['Status']}")
                
                # 통계 정보
                info_parts = []
                if row['Total'] > 0:
                    info_parts.append(f"📊 {row['Total']} total")
                if row['Unchanged'] > 0:
                    info_parts.append(f"🟢 {row['Unchanged']} unchanged")
                if row['Added'] > 0:
                    info_parts.append(f"➕ {row['Added']} added")
                if row['Modified'] > 0:
                    info_parts.append(f"✏️ {row['Modified']} modified")
                if row['Deleted'] > 0:
                    info_parts.append(f"❌ {row['Deleted']} deleted")
                if row['Change Rate'] > 0:
                    info_parts.append(f"📈 {row['Change Rate']:.1f}% change")
                
                if info_parts:
                    st.write("  |  ".join(info_parts))
            
            with col2:
                # 상세보기 토글
                current_selected = st.session_state.selected_page_for_detail == cache_key
                button_text = "📤 닫기" if current_selected else "📋 상세보기"
                
                if st.button(button_text, key=f"detail_btn_{idx}"):
                    if current_selected:
                        st.session_state.selected_page_for_detail = None
                    else:
                        st.session_state.selected_page_for_detail = cache_key
                    st.rerun()
            
            # 상세 분석 표시
            if st.session_state.selected_page_for_detail == cache_key:
                with st.expander("📊 상세 분석", expanded=True):
                    show_detailed_analysis(cache_key)
            
            st.divider()

def show_detailed_analysis(cache_key: str):
    """캐시된 분석 결과의 상세 정보 표시"""
    if cache_key not in st.session_state.analysis_results:
        st.error("분석 결과를 찾을 수 없습니다.")
        return
    
    analysis = st.session_state.analysis_results[cache_key]
    page_path = analysis['page_path']
    settings = st.session_state.comparison_settings
    
    # AEM 편집 링크
    st.write("🔗 **AEM 편집 페이지 링크**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**소스 ({settings['source_version']} v{settings['source_number']})**")
        source_url = build_aem_url(page_path, settings['source_version'])
        if source_url:
            st.markdown(f"[📝 편집하기]({source_url})")
    
    with col2:
        st.write(f"**타겟 ({settings['target_version']} v{settings['target_number']})**")
        target_url = build_aem_url(page_path, settings['target_version'])
        if target_url:
            st.markdown(f"[📝 편집하기]({target_url})")
    
    st.write("---")
    
    # 변경사항 통계
    changes = analysis['changes']
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("추가됨", len(changes['added']))
    with col2:
        st.metric("수정됨", len(changes['modified']))
    with col3:
        st.metric("삭제됨", len(changes['removed']))
    with col4:
        st.metric("변경없음", len(changes['unchanged']))
    
    # 텍스트 변경사항
    text_changes = get_text_changes_only(analysis)
    if text_changes:
        show_ai_translation_recommendations(text_changes)
    else:
        st.info("번역 검토가 필요한 텍스트 변경사항이 없습니다.")

def show_ai_translation_recommendations(text_changes: List[Dict]):
    """AI 번역 추천 표시"""
    st.subheader("🤖 AI 번역 추천")
    
    # 언어 쌍 선택
    language_options = {
        "영어 → 한국어": "en_ko",
        "영어 → 일본어": "en_ja"
    }
    
    selected_lang = st.selectbox(
        "언어 쌍:",
        options=list(language_options.keys()),
        key="ai_lang_selection"
    )
    
    lang_pair = language_options[selected_lang]
    
    # AI 모델 초기화
    with st.spinner("🤖 AI 모델 로딩 중..."):
        try:
            searcher = TranslationSearcher(lang_pair)
            stats = searcher.get_stats()
            
            if "error" not in stats:
                st.success(f"🚀 AI 준비 완료! (DB: {stats['total_translations']:,}개 번역 예시)")
            else:
                st.error(f"❌ AI 연결 실패: {stats['error']}")
                return
                
        except Exception as e:
            st.error(f"❌ AI 초기화 실패: {str(e)}")
            return
    
    # 각 변경사항에 대한 AI 추천
    for i, change in enumerate(text_changes):
        with st.expander(f"📝 변경사항 {i+1}: {change['component_path']}", expanded=True):
            
            # 변경 내용 표시
            search_text = ""
            if change['change_type'] == 'added':
                st.write("**🆕 새로 추가된 텍스트:**")
                st.code(change['content'], language='text')
                search_text = change['content']
                
            elif change['change_type'] == 'modified':
                st.write("**✏️ 수정된 텍스트:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("*소스 (원본):*")
                    st.code(change['source_content'], language='text')
                with col2:
                    st.write("*타겟 (번역):*")
                    st.code(change['target_content'], language='text')
                search_text = change['source_content']
            
            # AI 추천
            if search_text.strip():
                with st.spinner("🔍 AI 검색 중..."):
                    recommendations = searcher.search_similar_translations(search_text, top_k=3)
                
                if recommendations:
                    st.write("**🤖 AI 추천 번역:**")
                    for j, rec in enumerate(recommendations):
                        st.markdown(f"**{j+1}.** {format_recommendation_for_display(rec)}")
                        
                        with st.expander(f"상세 정보 {j+1}", expanded=False):
                            st.write(f"**원문:** {rec['source_text']}")
                            st.write(f"**번역:** {rec['target_text']}")
                            st.write(f"**유사도:** {rec['similarity_score']:.1%}")
                            st.write(f"**신뢰도:** {rec['confidence_level']}")
                            st.write(f"**참고 페이지:** {rec['page_path']}")
                else:
                    st.warning("🔍 유사한 번역 예시를 찾지 못했습니다.")

def build_aem_url(page_path: str, version: str, host: str = "https://prod-author.illumina.com") -> str:
    """AEM 편집 페이지 URL 생성"""
    clean_path = page_path.replace('/content/illumina-marketing/', '')
    if not clean_path.startswith('/'):
        clean_path = '/' + clean_path
    
    path_templates = {
        "lm-en": f"/content/illumina-marketing/language-master/en{clean_path}.html",
        "lm-ko": f"/content/illumina-marketing/language-master/ko{clean_path}.html", 
        "spac-ko_KR": f"/content/illumina-marketing/spac/ko_KR{clean_path}.html",
        "apac-en": f"/content/illumina-marketing/apac/en{clean_path}.html",
        "apac-ja_JP": f"/content/illumina-marketing/apac/ja_JP{clean_path}.html"
    }
    
    url_path = path_templates.get(version, "")
    return f"{host}/editor.html{url_path}" if url_path else ""

def get_page_status(summary: Dict) -> str:
    """페이지 상태 결정"""
    qa_required = summary['total_added'] + summary['total_modified']
    
    if qa_required > 0:
        return f"🟡 QA Required ({qa_required} items)"
    elif summary['total_removed'] > 0:
        return "🟠 Changes Detected"
    else:
        return "🟢 No Changes"

def create_enhanced_dashboard(pages: List[str]):
    """향상된 대시보드 메인 함수"""
    settings = st.session_state.comparison_settings
    
    if not all([settings['source_version'], settings['target_version']]):
        st.warning("⚠️ 먼저 버전 비교 설정을 완료해주세요.")
        return
    
    st.subheader("📊 페이지 변경사항 분석 대시보드")
    st.caption(f"비교: {settings['source_version']} v{settings['source_number']} ↔ {settings['target_version']} v{settings['target_number']}")
    
    if not pages:
        st.warning("분석할 페이지가 없습니다.")
        return
    
    # 컨트롤 버튼들
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"📋 **{len(pages)}개 페이지 분석 대상**")
    
    with col2:
        if st.button("🔄 분석 새로고침"):
            st.session_state.analysis_results.clear()
            st.rerun()
    
    with col3:
        show_excel_download = st.button("📄 Excel 리포트 생성", type="primary")
    
    # 페이지 분석 수행
    dashboard_data = analyze_pages_with_progress(pages, settings)
    
    # Excel 리포트 생성 (버튼 클릭 시)
    if show_excel_download and dashboard_data:
        excel_data = generate_excel_report(dashboard_data, settings)
        if excel_data:
            filename = f"AEM_QA_Report_{settings['source_version']}v{settings['source_number']}_vs_{settings['target_version']}v{settings['target_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            st.download_button(
                label="📥 Excel 파일 다운로드",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success(f"✅ 리포트 생성 완료! {len(dashboard_data)}개 페이지 분석")
    
    # 대시보드 표시
    if dashboard_data:
        display_dashboard_with_filters(dashboard_data)

def create_sidebar():
    """사이드바 UI 생성"""
    with st.sidebar:
        st.header("📁 파일 업로드")
        uploaded_file = st.file_uploader(
            "검토할 페이지 목록 CSV 업로드",
            type=['csv'],
            help="Page Path 컬럼이 포함된 CSV 파일"
        )
        
        if uploaded_file is not None:
            pages = parse_csv_pages(uploaded_file)
            st.session_state.uploaded_pages = pages
            
        # 연결 상태 표시
        st.header("🔌 연결 상태")
        try:
            db = get_db()
            collections = db.list_collection_names()
            st.success(f"✅ MongoDB 연결됨 ({len(collections)} collections)")
        except Exception as e:
            st.error(f"❌ MongoDB 연결 실패: {str(e)}")
        
        # 버전 현황 표시
        if st.checkbox("📊 버전 현황 보기"):
            display_version_summary()

def show_welcome_screen():
    """환영 화면 표시"""
    st.info("👈 사이드바에서 CSV 파일을 업로드하여 시작하세요.")
    
    # 샘플 CSV 형식 가이드
    st.subheader("📋 CSV 파일 형식 예시")
    sample_data = {
        'Page Path': [
            '/content/illumina-marketing/en/products/sequencing',
            '/content/illumina-marketing/en/areas-of-interest/cancer',
            '/content/illumina-marketing/en/company/news'
        ],
        'Status': ['검토 필요', '번역 필요', '완료'],
        'Priority': ['높음', '보통', '낮음']
    }
    st.dataframe(pd.DataFrame(sample_data))
    st.info("💡 **'Page Path'** 컬럼명을 사용하면 자동으로 인식됩니다.")

def main():
    """메인 애플리케이션 로직"""
    # 페이지 제목
    st.title("🔍 AEM Translation QA Workstation")
    st.markdown("**AI-powered page change analysis and translation recommendation system**")
    
    # 세션 상태 초기화
    initialize_session_state()
    
    # 사이드바 생성
    create_sidebar()
    
    # 메인 컨텐츠
    if not st.session_state.uploaded_pages:
        show_welcome_screen()
    else:
        # 버전 비교 설정
        if create_version_comparison_settings():
            st.write("---")
            # 향상된 대시보드 표시
            create_enhanced_dashboard(st.session_state.uploaded_pages)

if __name__ == "__main__":
    main()