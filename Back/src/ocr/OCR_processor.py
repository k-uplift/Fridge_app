import cv2
import numpy as np
import easyocr
import os
import math

def correct_skew_robust(image):
    """
    [고급] 글자 덩어리들의 각도를 분석하여 이미지 기울기를 보정
    """
    # 1. 전처리: 그레이스케일 -> 반전 -> 이진화
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 배경은 검고 글자는 희게 만듭니다 (Thresholding)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # 2. 텍스트 라인 덩어리를 잡기 위해 가로로 긴 커널로 팽창(Dilate)
    # 글자들을 옆으로 붙여서 '문장 줄' 형태로 만듭니다.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    # 3. 윤곽선(Contours) 검출
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    angles = []
    for cnt in contours:
        # 너무 작은 덩어리(노이즈)는 무시
        if cv2.contourArea(cnt) < 1000:
            continue

        # 최소 면적 사각형(Min Area Rect)으로 각도 계산
        rect = cv2.minAreaRect(cnt)
        angle = rect[-1]
        
        # 가로/세로 비율을 보고 각도 보정 (OpenCV 버전에 따라 -90~0 또는 0~90 범위임)
        width, height = rect[1]
        if width < height:
            angle = 90 + angle
        
        # 각도가 너무 크면(수직선 등) 무시, 미세한 기울기만 수집
        if abs(angle) < 45:
            angles.append(angle)

    # 4. 각도 결정 (평균 대신 중앙값을 사용하여 이상치 제거)
    if len(angles) == 0:
        return image # 보정할 각도를 못 찾음
    
    median_angle = np.median(angles)
    
    if abs(median_angle) < 0.5: # 0.5도 미만은 보정 안 함
        return image

    print(f"🔄 감지된 기울기: {median_angle:.2f}도 -> 보정 실행")

    # 5. 회전 실행
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    
    rotated = cv2.warpAffine(
        image, 
        M, 
        (w, h), 
        flags=cv2.INTER_CUBIC, 
        borderMode=cv2.BORDER_CONSTANT, 
        borderValue=(255, 255, 255) # 빈 공간 흰색 채우기
    )

    return rotated

def preprocess_image(image_path):
    if not os.path.exists(image_path):
        return None

    # 이미지 로드
    img_array = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    # 1. ★ [핵심] 정교한 기울기 보정 먼저 수행
    try:
        img = correct_skew_robust(img)
    except Exception as e:
        print(f"⚠️ 기울기 보정 건너뜀: {e}")

    # 2. 그레이스케일 & 기존 전처리 계속...
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    binary = cv2.adaptiveThreshold(
        blurred, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        19, 5
    )
    
    return binary

def extract_receipt_data(image_array):
    """
    EasyOCR 실행 (Raw Text 반환)
    """
    # GPU 사용 권장
    reader = easyocr.Reader(['ko', 'en'], gpu=True) 
    
    results = reader.readtext(
        image_array, 
        detail=1, 
        canvas_size=2560, # 긴 영수증 대응을 위해 캔버스 크기 확보
        mag_ratio=1.5,    # 내부 확대 배율 (작은 글씨 인식률 향상)
        width_ths=0.7     # 가로 간격 허용치
    )
    
    if not results:
        return []

    # Y축(위->아래) 기준으로 정렬하여 리스트 순서 보정
    results.sort(key=lambda r: r[0][0][1])

    # 텍스트만 리스트로 반환 (LLM이 문맥을 보고 병합하도록 함)
    raw_text_lines = [text for (bbox, text, prob) in results]

    return raw_text_lines