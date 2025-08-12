# src/utils/excel_processor.py

import pandas as pd
import os
import glob
# 👇 위에서 만든 '설계도'를 가져옵니다.
from utils.mappings import FOUNDATION_TM_MAP, UPDATE_REQUEST_TM_MAP, GLOSSARY_MAP

# --- 2-A. MyIllumina Master 파일 변환 (변경 없음) ---
def _transform_myillumina_df(df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
    """
    'KR TM Update Request' 파일을 변환하며, 'source_file'을 포함합니다.
    """
    # ... (이전 제안과 유사하나, mapping을 인자로 받도록 수정)
    print("   -> 'MyIllumina Master' 파일 변환 중...")
    existing_cols_map = {orig: std for orig, std in column_mapping.items() if orig in df.columns}
    
    # 필요한 우너본 칼럼 목록 가져오기
    original_columns_to_keep = list(existing_cols_map.keys())

    # 원본 칼럼 목록에 'source_file' 필드를 추가
    df_processed = df[original_columns_to_keep + ['source_file']].copy()

    # 칼럼 이름을 표준 이름으로 변경
    df_processed.rename(columns=existing_cols_map, inplace=True)

    return df_processed

# --- 2-B. KR TM Update Request 파일 변환 (변경 없음) ---
def _transform_update_request_df(df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
    """
    'KR TM Update Request' 파일을 변환하며, 'source_file'을 포함합니다.
    """
    print("   -> 'KR TM Update Request' 파일 변환 중...")
    
    # 1. 실제 파일에 존재하는 컬럼에 대한 맵핑만 필터링
    existing_cols_map = {orig: std for orig, std in column_mapping.items() if orig in df.columns}
    
    # 2. 필요한 원본 컬럼 목록을 가져옴
    original_columns_to_keep = list(existing_cols_map.keys())
    
    # ▼▼▼▼▼ 여기가 수정된 부분입니다 ▼▼▼▼▼
    # 기존 컬럼 목록에 'source_file'을 추가하여 함께 선택
    df_processed = df[original_columns_to_keep + ['source_file']].copy()
    # ▲▲▲▲▲ 여기가 수정된 부분입니다 ▲▲▲▲▲
    
    # 3. 컬럼 이름을 표준 이름으로 변경
    df_processed.rename(columns=existing_cols_map, inplace=True)
    
    return df_processed


def create_base_tm_from_folder(input_folder: str, output_path: str):
    """하나의 폴더에서 여러 종류의 TM Excel을 지능적으로 식별하고 통합하여 base_tm.csv를 생성합니다."""
    print("🚀 기반 TM 생성을 시작합니다...")
    
    excel_files = glob.glob(os.path.join(input_folder, "*.xlsx"))
    if not excel_files:
        print("✅ 처리할 파일이 없어 종료합니다."); return

    all_dfs = []
    for file_path in excel_files:
        df_raw = pd.read_excel(file_path).assign(source_file=os.path.basename(file_path))
        
        # 파일 컬럼을 보고 어떤 '설계도'를 사용할지 결정
        if 'DevKey' in df_raw.columns:
            all_dfs.append(_transform_myillumina_df(df_raw, FOUNDATION_TM_MAP))
        elif 'Target (from EN)' in df_raw.columns:
            all_dfs.append(_transform_update_request_df(df_raw, UPDATE_REQUEST_TM_MAP))
        else:
            print(f"   - ⚠️ 경고: '{os.path.basename(file_path)}'는 알 수 없는 형식의 TM 파일입니다. 건너뜁니다.")

    if not all_dfs:
        print("✅ 처리 가능한 TM 파일이 없어 종료합니다."); return

    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.drop_duplicates(subset=['source_text'], keep='last', inplace=True)
    final_df.dropna(subset=['source_text', 'target_text'], inplace=True)
    
    final_df.insert(0, 'tm_id', range(1, 1 + len(final_df)))
    final_columns = ['tm_id', 'source_text', 'target_text', 'context_devkey', 'context_type', 'context_aem_url', 'status', 'notes', 'source_file']
    df_to_save = final_df.reindex(columns=final_columns)
    
    df_to_save.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n🎉 최종 기반 TM 생성 완료: '{output_path}' ({len(df_to_save)}개 행)")

def create_glossary_from_folder(input_folder: str, output_path: str):
    """용어집 폴더의 Excel 파일들을 처리하여 glossary.csv를 생성합니다."""
    print("📖 용어집 생성을 시작합니다...")
    
    excel_files = glob.glob(os.path.join(input_folder, "*.xlsx"))
    if not excel_files:
        print("✅ 처리할 파일이 없어 종료합니다."); return

    all_dfs = [pd.read_excel(f).assign(Source_File=os.path.basename(f)) for f in excel_files]
    df_raw = pd.concat(all_dfs, ignore_index=True)

    df_processed = _transform_df(df_raw, GLOSSARY_MAP)
    df_processed.drop_duplicates(subset=['source_text'], inplace=True)
    df_processed.dropna(subset=['source_text', 'target_text'], inplace=True)

    df_processed.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n🎉 용어집 생성 완료: '{output_path}' ({len(df_processed)}개 행)")