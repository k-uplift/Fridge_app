import cv2
import numpy as np
import easyocr
import os
import re

def remove_shadows(image):
    """
    [핵심] 이미지의 배경(조명)을 추정하여 제거 (명암 보정)
    """
    dilated_img = cv2.dilate(image, np.ones((7, 7), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)
    diff_img = 255 - cv2.absdiff(image, bg_img)
    norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    return norm_img

def apply_clahe(image):
    """
    [핵심] CLAHE: 구겨진 종이의 국소적인 어두움을 개선하여 글자 대비 극대화
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)

def correct_skew_robust(image):
    """
    [기존 유지] 글자 덩어리들의 각도를 분석하여 이미지 기울기를 보정
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    angles = []
    for cnt in contours:
        if cv2.contourArea(cnt) < 1000:
            continue
        rect = cv2.minAreaRect(cnt)
        angle = rect[-1]
        width, height = rect[1]
        if width < height:
            angle = 90 + angle
        if abs(angle) < 45:
            angles.append(angle)

    if len(angles) == 0:
        return image
    
    median_angle = np.median(angles)
    if abs(median_angle) < 0.5:
        return image

    print(f"🔄 감지된 기울기: {median_angle:.2f}도 -> 보정 실행")

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    
    rotated = cv2.warpAffine(
        image, M, (w, h), 
        flags=cv2.INTER_CUBIC, 
        borderMode=cv2.BORDER_CONSTANT, 
        borderValue=(255, 255, 255)
    )
    return rotated

def preprocess_image(image_path):
    if not os.path.exists(image_path):
        return None

    img_array = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    try:
        img = correct_skew_robust(img)
    except Exception as e:
        print(f"⚠️ 기울기 보정 건너뜀: {e}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    no_shadow = remove_shadows(gray)
    enhanced = apply_clahe(no_shadow)
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

    binary = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        25, 
        5
    )
    
    return binary

def is_valid_text(text):
    """
    [수정된 필터링 규칙]
    1. 한글이 포함되어 있으면 무조건 통과 (상품명)
    2. 한글이 없는 경우(영어, 숫자, 특수문자 등):
       - 숫자가 있고 그 값이 100 미만이면 통과 (수량)
       - 그 외(큰 숫자, 순수 영어, 특수문자 등)는 모두 제거
    """
    text = text.strip()
    if not text:
        return False

    # 1. 한글이 한 글자라도 포함되어 있다면 -> 유효한 데이터(상품명)로 간주하고 통과
    if re.search(r'[가-힣]', text):
        return True

    # (영어, 숫자, 특수문자로만 구성된 문자열)
    # 2. 숫자만 추출해서 확인
    digits = re.sub(r'[^0-9]', '', text)
    if digits:
        try:
            # 숫자가 존재하고, 그 값이 100 미만인 경우 (예: "1", "2", "50") -> 수량으로 보고 통과
            if int(digits) < 100:
                return True
        except:
            pass

    # 3. 한글도 없고, 유효한 작은 숫자도 아니라면 (예: "13,450", "Coca-Cola", "(A)") -> 제거
    return False

def extract_receipt_data(image_array):
    """
    EasyOCR 실행 및 결과 필터링
    """
    reader = easyocr.Reader(['ko', 'en'], gpu=True) 
    
    results = reader.readtext(
        image_array, 
        detail=1, 
        canvas_size=3840, 
        mag_ratio=1.0,    
        contrast_ths=0.1, 
        adjust_contrast=0.5 
    )
    
    if not results:
        return []

    # Y축 정렬
    results.sort(key=lambda r: r[0][0][1])

    filtered_data = []
    
    for (bbox, text, prob) in results:
        # 1. 정확도(Confidence) 필터링: 0.1 미만 제거
        if prob < 0.05:
            continue
            
        # 2. 텍스트 내용 필터링: 특수문자/숫자만 있는 경우 (100미만 숫자 제외) 제거
        if not is_valid_text(text):
            continue
            
        # 통과한 데이터 저장
        filtered_data.append({
            "text": text,
            "confidence": float(prob) # JSON 직렬화를 위해 float 형변환
        })

    return filtered_data