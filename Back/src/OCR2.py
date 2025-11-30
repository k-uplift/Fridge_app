import os
import cv2
import numpy as np
import easyocr
import re
import pandas as pd

# --- 설정 ---
CONFIDENCE_THRESHOLD = 0.2  # 신뢰도 기준
DEBUG_MODE = True           # 디버깅 모드

# [1] 제거할 키워드 대폭 추가 (헤더, 푸터, 영수증 잡음)
IGNORE_KEYWORDS = [
    "단가", "수량", "금액", "상품명", "상품", 
    "구매", "구매금액", "카드", "받은금액", "받은", 
    "면세", "과세", "부가세", "합계", "결제", "거스름돈", "반품", "포인트",
    "대표", "매장", "전화", "사업자", "가맹점", "주소", "TEL", "POS",
    "품목", "입니다", "표시는", "안내"
]

def minimal_preprocess(image_path):
    if not os.path.exists(image_path): return None
    file_data = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(file_data, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=5, templateWindowSize=7, searchWindowSize=21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    return enhanced

def clean_name(text):
    """
    [요청사항 반영]
    1. 특수문자 {, [, (, ), *, ^, ., , 등 제거
    2. 앞뒤 공백 정리
    """
    # 제거할 특수문자들을 정규식으로 나열
    # [ ] { } ( ) * ^ . , ' " 등을 모두 공백으로 변경 후 strip
    text = re.sub(r'[\[\]\{\}\(\)\*\^\.\,\'\"_]', ' ', text)
    
    # 2개 이상의 연속된 공백을 하나로 줄임
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def is_garbage(text):
    """
    'O60', '구매', '품목입니다' 등을 걸러내는 강력한 필터
    """
    text = text.strip()
    
    # 1. 글자 길이 체크 (1글자 이하는 삭제)
    if len(text) < 2: return True

    # 2. 키워드 포함 여부 (헤더/푸터)
    for keyword in IGNORE_KEYWORDS:
        if keyword in text:
            return True

    # 3. [잡음 제거] 한글이 하나도 없는데...
    if not re.search(r'[가-힣]', text):
        # A. 그냥 숫자인 경우 (상품코드 파편) -> 삭제
        if re.match(r'^\d+$', text): return True
        
        # B. 'O60' 처럼 알파벳+숫자가 섞여있고 길이가 짧은 경우 -> 삭제
        # (상품명이라면 보통 영어가 길게 나오지, 3~4글자로 숫자랑 섞여 나오진 않음)
        if len(text) < 5 and re.search(r'\d', text):
            return True
            
        # C. 특수문자만 있는 경우 -> 삭제
        if not re.search(r'[a-zA-Z0-9]', text):
            return True

    return False

def get_quantity(text):
    parts = text.split()
    for part in parts:
        clean = re.sub(r'[^0-9]', '', part) # 숫자만 남기기
        if clean:
            val = int(clean)
            if 0 < val < 100: return val
    return 1

# --- 메인 실행 ---
if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'test_image.jpg')

    img = minimal_preprocess(file_path)

    if img is not None:
        reader = easyocr.Reader(['ko', 'en'], gpu=False) # CPU 모드
        
        # 파라미터는 유지
        result = reader.readtext(
            img, 
            detail=1, 
            mag_ratio=1.5, 
            contrast_ths=0.05, 
            adjust_contrast=0.8,
            text_threshold=0.5
        )

        parsed_data = []
        i = 0
        
        while i < len(result):
            bbox, text, prob = result[i]
            
            # 1. 기본 필터링 (신뢰도 & 쓰레기 문자)
            if prob < CONFIDENCE_THRESHOLD or is_garbage(text):
                if DEBUG_MODE: print(f"[삭제] {text} (신뢰도: {prob:.2f})")
                i += 1
                continue

            # 2. 상세정보(숫자로 시작하는 줄) 스킵
            # 특수문자 제거 후 순수 텍스트가 숫자로 시작하면 상세정보 라인
            clean_check = re.sub(r'[^0-9a-zA-Z가-힣]', '', text)
            if clean_check and clean_check[0].isdigit():
                if DEBUG_MODE: print(f"[삭제-숫자라인] {text}")
                i += 1
                continue

            # --- [통과] 상품명 정제 ---
            product_name = clean_name(text)
            
            # 정제 후에도 남은게 별로 없거나(빈 문자열), 숫자로만 되어있으면 스킵
            if len(product_name) < 2 or product_name.isdigit():
                 if DEBUG_MODE: print(f"[삭제-정제후] {product_name}")
                 i += 1
                 continue

            # 수량 찾기 (Look-ahead)
            quantity = 1
            if i + 1 < len(result):
                _, text_next, prob_next = result[i+1]
                # 다음 줄이 숫자로 시작하면 수량 정보로 간주
                clean_next = re.sub(r'[^0-9]', '', text_next) # 숫자만 추출해서 확인
                if clean_next and text_next.strip()[0].isdigit(): # 원본 텍스트의 첫 글자가 숫자여야 함
                    quantity = get_quantity(text_next)
                    
            parsed_data.append({"품목명": product_name, "수량": quantity})
            
            # DEBUG
            if DEBUG_MODE: print(f"[등록] {product_name} / {quantity}")
            
            i += 1

        print("-" * 50)
        if parsed_data:
            df = pd.DataFrame(parsed_data)
            print(df)
        else:
            print("데이터 없음")