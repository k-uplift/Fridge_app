import cv2
import numpy as np
import easyocr
import re
import os
import json

def preprocess_image(image_path):
    if not os.path.exists(image_path):
        return None

    img_array = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    scaled = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    kernel = np.ones((3, 3), np.uint8)
    closing = cv2.morphologyEx(scaled, cv2.MORPH_CLOSE, kernel)
    
    binary = cv2.adaptiveThreshold(
        closing, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        25, 10
    )
    return binary

def is_valid_korean_product(text):
    pure_text = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)
    
    if len(pure_text) < 2:
        return False
    
    IGNORE_KEYWORDS = ["단가", "수량", "금액", "상품명", "합계", "결제", "카드", "면세", "부가세", "대표", "전화", "주소", "가맹점", "반품", "포인트", "교환", "할인", "현금", "승인"]
    if any(k in pure_text for k in IGNORE_KEYWORDS):
        return False

    if not re.search(r'[가-힣]', pure_text):
        return False

    digit_count = len(re.sub(r'[^0-9]', '', pure_text))
    if (digit_count / len(pure_text)) >= 0.8:
        return False

    return True

def extract_receipt_data(image_array):
    reader = easyocr.Reader(['ko', 'en'], gpu=False) 
    results = reader.readtext(image_array)
    
    parsed_data = []
    
    i = 0
    while i < len(results):
        _, text, prob = results[i]
        
        if prob < 0.1:
            i += 1
            continue

        if not is_valid_korean_product(text):
            i += 1
            continue
            
        product_name = text
        quantity = 1
        
        # 1. 같은 줄 끝에 수량이 있는 경우
        match_inline = re.search(r'(\d+)$', product_name.strip())
        if match_inline:
            val = int(match_inline.group(1))
            if 0 < val < 50:
                quantity = val
                product_name = re.sub(r'\d+$', '', product_name).strip()

        # 2. 다음 줄에 수량이 있는 경우
        if quantity == 1 and i + 1 < len(results):
            _, next_text, _ = results[i+1]
            numbers = re.findall(r'\d+', next_text.replace(',', ''))
            
            for num_str in numbers:
                val = int(num_str)
                if 0 < val < 50:
                    quantity = val
                    break 
        
        clean_name = re.sub(r'^[^\w가-힣]+|[^\w가-힣]+$', '', product_name)

        parsed_data.append({
            "product_name": clean_name,
            "quantity": quantity
        })
        i += 1

    return parsed_data

if __name__ == '__main__':
    # 입력 파일 경로
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'test_image.jpg')
    output_json_path = os.path.join(base_path, 'receipt_data.json')
    
    processed_img = preprocess_image(file_path)
    
    if processed_img is not None:
        print("이미지 인식 중...")
        data_list = extract_receipt_data(processed_img)
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=4)
            
        print(f"완료! 결과가 '{output_json_path}' 파일로 저장되었습니다.")
        print(f"총 {len(data_list)}개의 품목이 검출되었습니다.")
    else:
        print("이미지 파일을 찾을 수 없습니다.")