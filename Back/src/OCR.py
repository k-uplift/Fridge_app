import cv2
import numpy as np
import os
import pytesseract
import re  # 정규표현식 모듈 추가


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'test_image.jpg')

def advanced_preprocess(image_path):
    # 1. 이미지 파일 읽기 (한글 경로 호환)
    if not os.path.exists(image_path):
        print(f"오류: 파일을 찾을 수 없습니다. -> {image_path}")
        return None
    
    file_data = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(file_data, cv2.IMREAD_COLOR)
    if img is None:
        print("오류: 이미지를 읽을 수 없습니다 (손상된 파일 등).")
        return None

    print(f"이미지 읽기 성공! 해상도: {img.shape}")

    # 2. 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. [중요] 이미지 2배 확대 (작은 글씨 인식률 향상)
    # 글자가 너무 작으면 OCR이 인식을 못합니다. 키우면 훨씬 잘 됩니다.
    scaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)

    # 4. [핵심] 배경 노이즈 및 그림자 제거 (Top-Hat 연산)
    # 밝은 글씨(영수증 배경)에서 어두운 부분(그림자)을 빼서 평탄화합니다.
    # 커널 크기(25, 25)는 글자보다 커야 합니다. 글자가 뭉개지면 크기를 조절하세요.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    tophat = cv2.dilate(scaled, kernel, iterations=1)

    # 5. 부드럽게 만들기 (Bilateral Filter)
    # 글자 획의 경계선은 살리면서 자잘한 노이즈만 뭉갭니다.
    # 인자: (이미지, 지름, 색상공간 시그마, 좌표공간 시그마) -> 75, 75 값을 조절해보세요.
    blurred = cv2.bilateralFilter(tophat, 5, 50, 50)

    # 6. 적응형 이진화 (Adaptive Threshold)
    # 그림자가 있어도 부분별로 임계값을 계산해서 깔끔하게 분리합니다.
    # blockSize(31): 이진화 계산 영역 크기 (홀수). 글자 크기에 맞춰 조절.
    # C(15): 계산된 임계값에서 뺄 상수. 값이 클수록 배경 노이즈가 줄지만 글자가 얇아짐.
    binary = cv2.adaptiveThreshold(
        tophat,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, # 블록 크기 (글자가 크면 키우세요 예: 41, 51)
        5  # 상수 C (배경이 지저분하면 키우고, 글자가 끊기면 줄이세요 예: 10~20)
    )

    # 7. [마무리] 글자 획 두껍게 만들기 (Morphology Close)
    # 이진화 과정에서 끊어진 획을 이어주고 구멍을 메워줍니다.
    # 커널 크기가 (3,3)이면 너무 두꺼워질 수 있으니 (2,2)나 (3,1) 등으로 조절해보세요.
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)

    return closed
# == 영수증 데이터 정제 함수 ============================================
def parse_receipt_text(text):
    clean_data = []
    found_date = None

    # 1. 제거할 키워드 (헤더, 결제정보, 세금 등)
    # 여기에 '상품', '수량' 같은 헤더 단어도 추가하여 첫 줄을 날립니다.
    ignore_keywords = [
        '단가', '금액', '수량', '구매금액', '받은금액', '거스름돈', '카드', '현금', 
        '면세', '과세', '부가세', '물품', '공급가액', 'POS', 'TEL', 
        '대표', '사업자', '가맹점', '주소', '반품', '교환', '안내', '할인',
        '합계', '결제', '신용', '승인', '전자', '서명', '매출'
    ]

    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 2. 날짜 추출 (YYYY-MM-DD 등)
        if not found_date:
            date_match = re.search(r'\d{4}[-./]\d{2}[-./]\d{2}', line)
            if date_match:
                found_date = date_match.group()
                continue 

# [추가] 구분선 제거 강력한 필터
        # 설명: 줄의 시작(^)부터 끝($)까지, 
        # [=], [-], [_], [공백], [.] 만으로 이루어진 줄은 무조건 삭제
        if re.match(r'^[=\-_ \.]+$', line):
            continue

        # [추가2] 반복되는 특수문자 패턴 제거 (예: == 상품 ==)
        # 줄에 =나 -가 3개 이상 연속으로 있으면 구분선으로 간주
        if re.search(r'[=\-]{3,}', line):
            continue

        # 4. 불필요한 키워드가 포함된 줄 제거
        if any(keyword in line for keyword in ignore_keywords):
            continue

        # 5. [중요] 상품 코드 및 가격 제거 로직 강화
        
        # 5-1. 가격 패턴 제거 (13,450 처럼 쉼표 포함 숫자)
        line_clean = re.sub(r'\d{1,3}(,\d{3})+', '', line)

        # 5-2. [추가] 상품 코드/바코드 제거 (5자리 이상 연속된 숫자)
        # 예: 200078, 8801007... 이런 숫자를 지워야 상품명으로 인식 안 함
        line_clean = re.sub(r'\d{5,}', '', line_clean)

        # 6. 수량 추출
        # 가격과 코드를 지우고 남은 숫자 중, 1~99 사이의 정수를 찾음
        numbers = re.findall(r'\d+', line_clean)
        qty = 1
        
        if numbers:
            # 보통 맨 뒤에 있는 숫자가 수량일 확률이 높음
            candidate_qty = int(numbers[-1])
            if 0 < candidate_qty < 100: 
                qty = candidate_qty
                # 수량으로 쓴 숫자도 텍스트에서 제거
                line_clean = line_clean.replace(str(qty), '', 1)

        # 7. 특수문자 제거 및 상품명 정제
        # 한글, 영문, 공백을 제외한 특수문자(*, ^, (, ) 등) 제거
        item_name = re.sub(r'[^\w\s가-힣]', ' ', line_clean).strip()

        # 8. 최종 필터링 (쓰레기 데이터 거르기)
        # 8-1. 글자수가 너무 적으면 패스 (예: "1", "A")
        if len(item_name) < 2:
            continue
        
        # 8-2. 숫자로만 구성되어 있으면 패스 (남은 찌꺼기 숫자)
        if item_name.replace(' ', '').isdigit():
            continue

        clean_data.append({'date': found_date, 'item': item_name, 'qty': qty})

    return clean_data
# ==============================================================================
# 실행 부분
# ==============================================================================
base_dir = os.path.dirname(os.path.abspath(__file__))
target_image_path = os.path.join(base_dir, 'test_image.jpg') 

final_image = advanced_preprocess(target_image_path)

cv2.imshow("전처리된 이미지", final_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
if final_image is not None:
    print("\n--- OCR 인식 중 ---")
    
    # [중요 해결책] lang='kor' -> lang='kor+eng'
    # 영수증에는 숫자와 영어가 많으므로 반드시 eng를 같이 써야 "드그그"가 사라집니다.
    config_options = '--oem 3 --psm 4'
    raw_text = pytesseract.image_to_string(final_image, lang='kor+eng', config=config_options)
    
    # 결과 확인용 출력 (원본 텍스트가 숫자로 잘 나오는지 확인)
    print("--- [디버깅] 원본 인식 텍스트 ---")
    print(raw_text)
    print("---------------------------------")
    # 결과 출력
    current_date = parsed_result[0]['date'] if parsed_result and parsed_result[0]['date'] else "날짜 미상"
    print(f"📅 구매 날짜: {current_date}\n")
    
    print(f"{'상품명':<15} | {'수량':<5}")
    print("-" * 25)
    
    for data in parsed_result:
        print(f"{data['item']:<15} | {data['qty']:<5}")