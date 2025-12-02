# app/ocr/OCR_processor.py

import cv2
import numpy as np
import easyocr
import os

def preprocess_image(image_path):
    if not os.path.exists(image_path):
        return None

    img_array = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 이미지 확대 및 전처리
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

def extract_receipt_data(image_array):
    reader = easyocr.Reader(['ko', 'en'], gpu=True) 
    results = reader.readtext(image_array)
    
    if not results:
        return []

    results.sort(key=lambda r: (r[0][0][1], r[0][0][0]))

    merged_lines = []
    
    current_line_y = results[0][0][0][1]
    current_line_text = [results[0][1]] 
    
    for i in range(1, len(results)):
        bbox, text, prob = results[i]
        y_top = bbox[0][1]
        
        if abs(y_top - current_line_y) < 15: 
            current_line_text.append(text)
        else:
            merged_lines.append(" ".join(current_line_text))
            
            current_line_text = [text]
            current_line_y = y_top
    
    merged_lines.append(" ".join(current_line_text))

    return merged_lines