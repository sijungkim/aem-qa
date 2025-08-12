# aem_qa_station/modules/version_manager.py

import streamlit as st
from typing import List, Dict, Tuple
from datetime import datetime
from .connections import get_db

class VersionManager:
    """버전 관리 및 선택을 위한 클래스"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db["page_components"]
    
    def get_available_versions(self) -> Dict[str, List[Dict]]:
        """모든 사용 가능한 버전명과 버전번호 정보를 반환"""
        pipeline = [
            {"$group": {
                "_id": {
                    "version_name": "$version_name",
                    "version_number": "$version_number"
                },
                "latest_date": {"$max": "$snapshot_timestamp"},
                "count": {"$sum": 1}
            }},
            {"$sort": {
                "_id.version_name": 1,
                "_id.version_number": -1
            }}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        # 버전명별로 그룹화
        versions_by_name = {}
        for result in results:
            version_name = result["_id"]["version_name"]
            version_number = result["_id"]["version_number"]
            latest_date = result["latest_date"]
            
            if version_name not in versions_by_name:
                versions_by_name[version_name] = []
            
            versions_by_name[version_name].append({
                "version_number": version_number,
                "latest_date": latest_date,
                "count": result["count"]
            })
        
        # 각 버전명에서 최신 버전 표시
        for version_name in versions_by_name:
            if versions_by_name[version_name]:
                # 첫 번째가 최신 버전 (내림차순 정렬됨)
                versions_by_name[version_name][0]["is_latest"] = True
                for i in range(1, len(versions_by_name[version_name])):
                    versions_by_name[version_name][i]["is_latest"] = False
        
        return versions_by_name
    
    def format_version_display(self, version_info: Dict) -> str:
        """버전 정보를 사용자 친화적 형식으로 포맷팅"""
        version_num = version_info["version_number"]
        date = version_info["latest_date"]
        is_latest = version_info.get("is_latest", False)
        count = version_info.get("count", 0)
        
        # 날짜 포맷팅
        if isinstance(date, datetime):
            date_str = date.strftime("%Y-%m-%d")
        else:
            date_str = str(date)[:10]  # ISO 문자열인 경우
        
        # 표시 형식 결정
        if is_latest:
            return f"v{version_num} (latest: {date_str}) - {count} pages"
        else:
            return f"v{version_num} ({date_str}) - {count} pages"
    
    def get_version_options(self, version_name: str) -> List[Tuple[str, int]]:
        """특정 버전명의 옵션 리스트 반환 (표시명, 버전번호) 튜플"""
        all_versions = self.get_available_versions()
        
        if version_name not in all_versions:
            return []
        
        options = []
        for version_info in all_versions[version_name]:
            display_name = self.format_version_display(version_info)
            version_number = version_info["version_number"]
            options.append((display_name, version_number))
        
        return options
    
    def get_latest_version_number(self, version_name: str) -> int:
        """특정 버전명의 최신 버전번호 반환"""
        pipeline = [
            {"$match": {"version_name": version_name}},
            {"$group": {"_id": None, "max_version": {"$max": "$version_number"}}}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        if result:
            return result[0]["max_version"]
        return 1

def create_version_selector(label: str, version_type: str = "source") -> Tuple[str, int]:
    """버전 선택 UI 컴포넌트 생성"""
    version_manager = VersionManager()
    all_versions = version_manager.get_available_versions()
    
    # 사용 가능한 버전명 리스트
    version_names = list(all_versions.keys())
    
    if not version_names:
        st.error("사용 가능한 버전이 없습니다.")
        return None, None
    
    # 기본값 설정
    default_names = {
        "source": ["lm-en", "apac-en", "sot-en"],
        "target": ["spac-ko_KR", "lm-ko", "apac-ja_JP", "lm-ja"]
    }
    
    default_name = None
    for name in default_names.get(version_type, version_names):
        if name in version_names:
            default_name = name
            break
    
    if not default_name:
        default_name = version_names[0]
    
    # 버전명 선택
    col1, col2 = st.columns([3, 2])
    
    with col1:
        selected_version_name = st.selectbox(
            f"{label} 버전명",
            options=version_names,
            index=version_names.index(default_name) if default_name in version_names else 0,
            key=f"{version_type}_version_name"
        )
    
    with col2:
        # 선택된 버전명의 버전번호 옵션
        version_options = version_manager.get_version_options(selected_version_name)
        
        if version_options:
            # 기본적으로 최신 버전(첫 번째) 선택
            display_names = [option[0] for option in version_options]
            version_numbers = [option[1] for option in version_options]
            
            selected_index = st.selectbox(
                f"{label} 버전번호",
                options=range(len(display_names)),
                format_func=lambda x: display_names[x],
                key=f"{version_type}_version_number"
            )
            
            selected_version_number = version_numbers[selected_index]
        else:
            st.error(f"{selected_version_name}에 사용 가능한 버전이 없습니다.")
            selected_version_number = 1
    
    return selected_version_name, selected_version_number

# 편의 함수들
@st.cache_data(ttl=300)  # 5분 캐시
def get_cached_versions():
    """캐시된 버전 정보 반환"""
    version_manager = VersionManager()
    return version_manager.get_available_versions()

def display_version_summary():
    """현재 사용 가능한 버전들의 요약 표시"""
    versions = get_cached_versions()
    
    st.subheader("📊 사용 가능한 버전 현황")
    
    for version_name, version_list in versions.items():
        with st.expander(f"🔍 {version_name} ({len(version_list)} versions)"):
            for version_info in version_list:
                display_name = VersionManager().format_version_display(version_info)
                if version_info.get("is_latest"):
                    st.success(f"✨ {display_name}")
                else:
                    st.info(f"📅 {display_name}")