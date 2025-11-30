import cv2
import numpy as np
import os
import pytesseract
import re
import pandas as pd

# --- 설정 ---
# Tesseract 경로 (반드시 본인 경로로 수정)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

DEBUG_MODE = True

# [필터] 제거할 키워드 (EasyOCR 코드에서 가져옴 + 추가)
IGNORE_KEYWORDS = [
    "단가", "수량", "금액", "상품명", "상품", 
    "구매", "구매금액", "카드", "받은금액", "받은", 
    "면세", "과세", "부가세", "합계", "결제", "거스름돈", "반품", "포인트",
    "대표", "매장", "전화", "사업자", "가맹점", "주소", "TEL", "POS",
    "품목", "입니다", "표시는", "안내", "교환", "환불", "할인", "승인"
]

def preprocess_for_tesseract(image_path):
    """
    Tesseract를 위한 최적의 전처리 (CLAHE + 이진화)
    """
    if not os.path.exists(image_path): return None
    
    file_data = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(file_data, cv2.IMREAD_COLOR)
    
    # 1. 그레이스케일
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. [핵심] CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # 흐릿한 영수증 글씨의 대비를 국소적으로 강화시킵니다. (EasyOCR보다 Tesseract에 효과적)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 3. 확대 (2배)
    scaled = cv2.resize(enhanced, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    # 4. 이진화 (Otsu Thresholding)
    # CLAHE로 대비를 높였으므로 Otsu가 잘 먹힙니다.
    _, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 5. 노이즈 제거 (Median Blur)
    denoised = cv2.medianBlur(binary, 3)
    
    return denoised

def fix_common_ocr_errors(text):
    """
    [Tesseract 전용] 자주 틀리는 오타 교정
    """
    # 1. 영어 O -> 숫자 0 (숫자 사이에 끼인 O, 문자열 끝의 O 등)
    # 예: 3OOg -> 300g, 20O -> 200
    text = re.sub(r'(?<=\d)O(?=\d)', '0', text)   # 숫자 사이 O
    text = re.sub(r'(?<=\d)O(?=[gmlL])', '0', text) # 단위 앞 O (30Og)
    text = re.sub(r'(?<=\d)[oO]$', '0', text)     # 끝나는 O

    # 2. 숫자 1, l, I, | 혼동 해결
    # 단위(ml, L) 앞의 1이나 l 처리
    text = re.sub(r'(?<=\d)[lI|](?=[gmlL])', '1', text, flags=re.IGNORECASE)
    
    # 3. 단위 보정 (m1 -> ml)
    text = re.sub(r'm1', 'ml', text)
    
    # 4. 특수문자 노이즈 제거 (괄호, 별표 등은 공백 처리)
    text = re.sub(r'[\[\]\{\}\(\)\*\^\.\,\'\"_~#]', ' ', text)
    
    return text.strip()
def parse_tesseract_result(raw_text):
    parsed_data = []
    lines = raw_text.split('\n')
    
    # [강력 필터] 공백을 무시하고 잡아낼 키워드 리스트
    IGNORE_KEYWORDS = [
        "단가", "수량", "금액", "상품", "구매", "카드", "받은", 
        "면세", "과세", "부가세", "합계", "결제", "거스름돈", "반품", "포인트",
        "대표", "매장", "전화", "사업자", "가맹점", "주소", "TEL", "POS",
        "품목", "안내", "교환", "환불", "할인", "승인", "전표", "서명"
    ]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 1. 빈 줄 제거
        if not line:
            i += 1
            continue
            
        # 2. [핵심] 공백 제거 후 키워드 검사 ("카 드" -> "카드"로 인식하여 삭제)
        # 띄어쓰기가 엉망인 영수증 잡음들을 여기서 다 잡습니다.
        line_no_space = line.replace(" ", "")
        is_ignore = False
        for keyword in IGNORE_KEYWORDS:
            if keyword in line_no_space:
                is_ignore = True
                break
        
        if is_ignore:
            i += 1
            continue

        # 3. [핵심] 글자(한글/영어)가 하나도 없는 줄 삭제 (상품 코드 제거)
        # 예: "200078", "88010...", "13,450" 등 숫자나 특수문자만 있는 줄은 무조건 스킵
        if not re.search(r'[가-힣a-zA-Z]', line):
            i += 1
            continue
        
        # 4. 구분선 제거 (---, ===)
        if re.match(r'^[\-=]+$', line):
            i += 1
            continue

        # --- 기존 데이터 추출 로직 유지 ---
        
        # 1차 오타 교정
        clean_line = fix_common_ocr_errors(line)
        
        # 가격(오른쪽 끝 숫자) 제거
        line_no_price = re.sub(r'\d{1,3}(,\d{3})*$', '', clean_line).strip()
        
        # 상품명 정제 (한글, 영문, 숫자, 공백만 남김)
        product_name = re.sub(r'[^가-힣a-zA-Z0-9\s\.]', '', line_no_price).strip()
        product_name = re.sub(r'\s+', ' ', product_name)

        # 정제 후 다시 한 번 체크: 글자가 없거나 너무 짧으면 스킵
        if len(product_name) < 2 or product_name.isdigit():
            i += 1
            continue
            
        # 수량 추출 로직
        quantity = 1
        qty_match = re.search(r'(\d+)$', product_name)
        
        if qty_match:
            val = int(qty_match.group(1))
            if 0 < val < 100:
                quantity = val
                product_name = product_name[:qty_match.start()].strip()
        elif i + 1 < len(lines):
            next_line = lines[i+1].strip()
            if re.match(r'^\d+$', next_line):
                val = int(next_line)
                if 0 < val < 100:
                    quantity = val
                    i += 1 

        parsed_data.append({"품목명": product_name, "수량": quantity})
        if DEBUG_MODE: print(f"[등록] {product_name} / {quantity}")

        i += 1
        
    return parsed_data
# --- 메인 실행 ---
if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'test_image.jpg')

    # 1. 전처리 (CLAHE 적용)
    img = preprocess_for_tesseract(file_path)

    if img is not None:
        # 확인용 이미지 출력 (주석 해제시 확인 가능)
        # cv2.imshow('Processed', cv2.resize(img, (0,0), fx=0.5, fy=0.5)); cv2.waitKey(0); cv2.destroyAllWindows()

        # 2. Tesseract 인식
        # --psm 6: 단일 텍스트 블록으로 가정 (영수증 리스트에 적합)
        config = '--oem 3 --psm 6'
        raw_text = pytesseract.image_to_string(img, lang='kor+eng', config=config)
        
        # 3. 데이터 파싱 및 정제
        result_data = parse_tesseract_result(raw_text)

        print("-" * 50)
        if result_data:
            df = pd.DataFrame(result_data)
            print(df)
        else:
            print("데이터 없음")