import cv2
import numpy as np
import easyocr
import os
import shutil
import re
import math
from datetime import datetime

class AdvancedOCRProcessor:
    def __init__(self, use_gpu=True):
        print("Loading EasyOCR model...")
        self.reader = easyocr.Reader(['ko', 'en'], gpu=use_gpu)
        self.temp_dir = "temp_lines"
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        self.DEBUG_MODE = True # 디버깅 모드 활성화

    def crop_receipt_area(self, image):
        """[Step 1] 작게 검출하고, 좌표를 환산하여 원본에서 자르기"""
        print("DEBUG: Step 1 - Detecting on resized, Cropping on Original...")
        
        orig_h, orig_w = image.shape[:2]
        
        # 1. 검출용 리사이징 (속도 및 검출률 향상)
        detect_height = 500
        ratio = orig_h / float(detect_height)
        resized = cv2.resize(image, (int(orig_w / ratio), detect_height))
        
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 75, 200)

        cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        screenCnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                screenCnt = approx
                break

        if screenCnt is None:
            print("DEBUG: Step 1 failed. Returning original image.")
            return image

        # 2. 좌표 환산 (검출된 좌표 * 비율)
        # screenCnt는 (4, 1, 2) 형태이므로 reshape 필요
        pts = screenCnt.reshape(4, 2) * ratio 

        # 3. 투시 변환 (원본 이미지 기준)
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0], rect[2] = pts[np.argmin(s)], pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1], rect[3] = pts[np.argmin(diff)], pts[np.argmax(diff)]
        
        (tl, tr, br, bl) = rect
        
        # 원본 해상도 기준의 폭/높이 계산
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # 원본 이미지(image)에서 잘라냄
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

        if self.DEBUG_MODE:
            cv2.imwrite(os.path.join(self.temp_dir, "debug_01_cropped_high_res.jpg"), warped)
            
        return warped

    def add_padding(self, image, pad_size=10):
        return cv2.copyMakeBorder(image, pad_size, pad_size, pad_size, pad_size, 
                                  cv2.BORDER_CONSTANT, value=(255, 255, 255))

    def resize_height(self, image, target_height=96):
        h, w = image.shape[:2]
        if h == 0 or w == 0: return image
        scale = target_height / h
        new_w = int(w * scale)
        return cv2.resize(image, (new_w, target_height), interpolation=cv2.INTER_CUBIC)

    def sharpen_image(self, image):
        kernel = np.array([[0, -1, 0],
                       [-1, 9, -1],
                       [0, -1, 0]]) / 5.0
        return cv2.filter2D(image, -1, kernel)

    def apply_clahe(self, image):
        """CLAHE: 국소 대비 강화"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)

    def correct_ocr_typos(self, text):
        """오타 보정 로직"""
        text = text.strip()
        
        if len(text) <= 3:
            replacements = {'|': '1', 'l': '1', 'I': '1', '!': '1', ']': '1', '[': '1', 'i': '1', '}': '1', '{': '1'}
            new_text = ""
            for char in text:
                new_text += replacements.get(char, char)
            if new_text.isdigit():
                return new_text

        return text

    def clean_price(self, price_str):
        """가격 문자열 정제 및 복구"""
        price_str = price_str.replace(')', '0').replace('(', '0').replace('O', '0').replace('o', '0')
        digits = re.sub(r'[^0-9]', '', price_str)
        if not digits:
            return 0
        return int(digits)

    def parse_line_data(self, text):
        """
        [Fix] 파싱 로직 제거: LLM에 텍스트와 정확도를 넘기기 위해 raw_text만 반환하도록 변경
        """
        # 이 함수는 이제 사용되지 않습니다. 로직이 process 함수로 옮겨졌습니다.
        return {"raw_text": text}


    def find_line_contours(self, image):
        """
        [Fix] Otsu Binary + Morphology로 글자 영역 검출 안정화
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. Otsu Threshold (가장 안정적인 전체 이미지 기반 이진화)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 2. Morphology Open (침식 후 팽창): 노이즈와 미세 획 제거 (글자 덩어리만 남김)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open, iterations=1)
                                     
        # 3. 팽창 연산 (가로로 길게 팽창시켜 획을 이어 붙임)
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (1000, 1))
        dilated = cv2.dilate(opened, kernel_dilate, iterations=1)

        # 디버깅 파일 저장
        if self.DEBUG_MODE:
            cv2.imwrite(os.path.join(self.temp_dir, "debug_02_binary.jpg"), binary)
            cv2.imwrite(os.path.join(self.temp_dir, "debug_03_dilated.jpg"), dilated)
        
        # 4. 윤곽선 찾기
        cnts, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

        if not cnts:
            print("DEBUG: Step 2 failed (No valid text contours found).")
        
        return cnts, image.copy() 

    def segment_and_process_lines(self, receipt_image):
        
        cnts, clean_image = self.find_line_contours(receipt_image)
        
        line_data = []
        line_counter = 0 # [New] 라인별 이미지 저장을 위한 카운터

        img_h, img_w = clean_image.shape[:2] # 이미지 높이/너비

        for c in cnts:
            # 1. 직사각형 좌표 획득
            x, y, w, h = cv2.boundingRect(c)
            
            # 2. [Final Fix] 유효성 검사 완화: 최소 높이 10픽셀 미만만 무시
            if h < 10: 
                continue
            
            # 3. 좌표 안전 클리핑 (여백 5px 추가)
            padding = 5
            
            # 인덱스 계산을 먼저 한 후, 최종 좌표를 클리핑합니다.
            x1 = x - padding
            y1 = y - padding
            x2 = x + w + padding
            y2 = y + h + padding

            # 4. 이미지 경계 내에서 좌표를 강제 조정 (Numpy 클리핑)
            x1_safe = int(np.clip(x1, 0, img_w).astype(np.int32))
            y1_safe = int(np.clip(y1, 0, img_h).astype(np.int32))
            x2_safe = int(np.clip(x2, 0, img_w).astype(np.int32))
            y2_safe = int(np.clip(y2, 0, img_h).astype(np.int32))

            # 5. 이미지 자르기 (안전 클리핑 적용)
            if y1_safe >= y2_safe or x1_safe >= x2_safe:
                print(f"DEBUG: Skipping invalid slice after clip: y={y1_safe}:{y2_safe}, x={x1_safe}:{x2_safe}")
                continue

            cropped_line = clean_image[y1_safe:y2_safe, x1_safe:x2_safe]
            
            if cropped_line is None or cropped_line.size == 0: continue
            
            # 6. 이미지 보정
            final_line = cropped_line 

            padded_line = self.add_padding(final_line, pad_size=10)
            resized_line = self.resize_height(padded_line, target_height=64)
            final_line_sharpened = self.sharpen_image(resized_line)
            
            # [New] 라인별 이미지 저장
            if self.DEBUG_MODE:
                filename = os.path.join(self.temp_dir, f"line_{line_counter:03d}_final.jpg")
                cv2.imwrite(filename, final_line_sharpened)
                line_counter += 1

            center_y = y + h / 2
            line_data.append((center_y, final_line_sharpened))

        line_data.sort(key=lambda x: x[0])
        return [img for _, img in line_data]

    def process(self, image_path):
        img_array = np.fromfile(image_path, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image is None: return None

        print("DEBUG: Starting OCR Process.")

        # 1. 고해상도 크롭 (원본 화질 유지)
        cropped_receipt = self.crop_receipt_area(image)
        
        # [중요] 2. 이미지 표준화 (Normalization)
        # 이미지가 너무 크면(3000px) 커널이 안 먹히고, 너무 작으면(500px) 글자가 깨짐.
        # 따라서 OCR하기 가장 좋은 "골든 사이즈"인 높이 1200px로 통일합니다.
        # 이렇게 하면 find_line_contours의 (130, 1) 설정이 모든 이미지에서 항상 완벽하게 작동합니다.
        
        target_process_height = 1200
        h, w = cropped_receipt.shape[:2]
        if h > 0:
            scale = target_process_height / h
            new_w = int(w * scale)
            # 고품질 리사이징 (INTER_AREA는 축소 시, CUBIC은 확대 시 좋음. 여기선 일반적인 CUBIC 사용)
            cropped_receipt = cv2.resize(cropped_receipt, (new_w, target_process_height), interpolation=cv2.INTER_CUBIC)
            print(f"DEBUG: Normalized image height to {target_process_height}px for consistent processing.")

        if self.DEBUG_MODE:
             cv2.imwrite(os.path.join(self.temp_dir, "debug_01_normalized.jpg"), cropped_receipt)

        # 3. 라인 분리 및 처리
        line_images = self.segment_and_process_lines(cropped_receipt)

        print(f"DEBUG: Step 3 (Line Segmentation) found {len(line_images)} lines.") 
        results = []
        
        if not line_images:
            return {
                "status": "failure (No lines found)",
                "count": 0,
                "data": [],
                "meta": {"total_valid_lines": 0}, 
                "debug_info": "Line segmentation failed. Check debug_01_cropped.jpg, debug_02_binary.jpg and debug_03_dilated.jpg in temp_lines folder."
            }

        for i, line_img in enumerate(line_images):
            
            # [Fix] detail=1로 변경하여 bounding box, text, confidence 모두 획득
            ocr_res_detailed = self.reader.readtext(line_img, detail=1)
            
            # 텍스트와 정확도를 저장할 임시 변수 초기화
            line_text = ""
            line_confidence = []
            
            if ocr_res_detailed:
                
                # 단어별 텍스트와 정확도를 분리
                tokens = []
                for (bbox, text, conf) in ocr_res_detailed:
                    tokens.append(text)
                    line_confidence.append(float(conf))
                    
                # [Fix] 오타 보정 적용 (LLM에 넘기기 전 1차 교정)
                corrected_tokens = [self.correct_ocr_typos(token) for token in tokens]
                line_text = " ".join(corrected_tokens)
                
                # 1. 유효성 검사 (아무것도 없으면 버림)
                if not re.search(r'[가-힣0-9]', line_text):
                    continue

                # 2. LLM에 넘길 구조 생성 (파싱 로직은 LLM으로 위임)
                results.append({
                    "raw_text": line_text,
                    "confidence": line_confidence,
                    # 평균 정확도 계산 (LLM이 참고할 수 있도록)
                    "avg_confidence": sum(line_confidence) / len(line_confidence) if line_confidence else 0 
                })

        print(f"DEBUG: Step 4 (Processing) kept {len(results)} raw text lines.")

        return {
            "status": "success",
            "count": len(results),
            "data": results,
            "meta": {"total_valid_lines": len(results)} 
        }