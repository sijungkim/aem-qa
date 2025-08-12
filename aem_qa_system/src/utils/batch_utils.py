# src/utils/batch_utils.py

import os
import math
import re
import pandas as pd

def create_text_file_batches(input_file: str, output_dir: str, batch_size: int = 500):
    """
    거대한 .txt 목록 파일을 읽어 작은 배치(.list) 파일들로 분할합니다.
    """
    print(f"🔄 텍스트 파일 배치 생성 중: '{os.path.basename(input_file)}'")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not lines:
            print("   - ✅ 파일이 비어있어 처리할 내용이 없습니다.")
            return

        total_batches = math.ceil(len(lines) / batch_size)
        print(f"   - 총 {len(lines)}개 항목을 {total_batches}개 배치로 분할합니다.")

        for i in range(total_batches):
            batch_lines = lines[i * batch_size : (i + 1) * batch_size]
            batch_filename = f"aem_batch_{i+1:03d}.list"
            batch_path = os.path.join(output_dir, batch_filename)
            with open(batch_path, 'w', encoding='utf-8') as bf:
                bf.write("\n".join(batch_lines))
        
        print(f"   - ✅ AEM 배치 파일 {total_batches}개 생성 완료.")
    except Exception as e:
        print(f"   - ❌ 오류 발생: {e}")

def create_csv_file_batches(input_file: str, output_dir: str, batch_size: int = 500):
    """
    거대한 .csv 목록 파일을 읽어 작은 배치(.csv) 파일들로 분할합니다.
    언어 쌍은 입력 파일명에서 자동으로 추출합니다.
    
    Args:
        input_file: 입력 CSV 파일 경로 (예: pdf_list_master_en_ko.csv)
        output_dir: 출력 디렉토리
        batch_size: 배치 크기
    """
    # 파일명에서 언어 쌍 추출
    language_pair = _extract_language_pair_from_filename(input_file)
    if not language_pair:
        print(f"❌ 파일명에서 언어 쌍을 추출할 수 없습니다: {os.path.basename(input_file)}")
        print("   예상 파일명 형식: pdf_list_master_en_ko.csv")
        return
        
    source_lang, target_lang = language_pair
    filename_suffix = f"{source_lang}_{target_lang}"
    
    print(f"🔄 CSV 파일 배치 생성 중: '{os.path.basename(input_file)}' ({source_lang.upper()}-{target_lang.upper()})")
    
    try:
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        df = pd.read_csv(input_file)
        if df.empty:
            print("   - ✅ 파일이 비어있어 처리할 내용이 없습니다.")
            return

        total_batches = math.ceil(len(df) / batch_size)
        print(f"   - 총 {len(df)}개 항목을 {total_batches}개 배치로 분할합니다.")

        for i in range(total_batches):
            batch_df = df.iloc[i * batch_size : (i + 1) * batch_size]
            batch_filename = f"pdf_batch_{filename_suffix}_{i+1:03d}.csv"
            batch_path = os.path.join(output_dir, batch_filename)
            batch_df.to_csv(batch_path, index=False, encoding='utf-8-sig')
        
        print(f"   - ✅ PDF 배치 파일 {total_batches}개 생성 완료.")
        
    except FileNotFoundError:
        print(f"   - ❌ 입력 파일을 찾을 수 없습니다: {input_file}")
    except pd.errors.EmptyDataError:
        print(f"   - ❌ CSV 파일이 비어있거나 형식이 잘못되었습니다: {input_file}")
    except Exception as e:
        print(f"   - ❌ 오류 발생: {e}")

def _extract_language_pair_from_filename(filepath: str) -> tuple:
    """
    파일명에서 언어 쌍을 추출합니다.
    
    Args:
        filepath: 파일 경로
        
    Returns:
        tuple: (source_lang, target_lang) 또는 None
        
    Examples:
        pdf_list_master_en_ko.csv -> ('en', 'ko')
        pdf_list_master_en_ja.csv -> ('en', 'ja')
        other_file.csv -> None
    """
    filename = os.path.basename(filepath)
    
    # 언어 쌍 패턴 매칭 (en_ko, en_ja 등)
    pattern = r'_([a-z]{2})_([a-z]{2})\.csv$'
    match = re.search(pattern, filename)
    
    if match:
        source_lang = match.group(1)
        target_lang = match.group(2)
        return (source_lang, target_lang)
    else:
        return None