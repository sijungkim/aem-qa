# src/utils/mappings.py

# "MyIllumina_Master_Translations.xlsx" 파일용 설계도
FOUNDATION_TM_MAP = {
    'English': 'source_text', 
    'Korean': 'target_text',
    'DevKey': 'context_devkey', 
    'Type of Text/Error': 'context_type',
    'Page': 'context_aem_url', 
    'Comments': 'notes'
}

# "KR_TM_update_request_14_Mar_2025.xlsx" 파일용 설계도
UPDATE_REQUEST_TM_MAP = {
    'Target (from EN)': 'source_text',
    'Korean (To be updated)': 'target_text',
    'Page': 'context_aem_url',
    'Note': 'notes',
    'TM Update Status': 'status'
}

# "Illumina_Korean Glossary_JH.xlsx" 파일용 설계도
GLOSSARY_MAP = {
    'en-US': 'source_text',
    'ko-KR': 'target_text'
}