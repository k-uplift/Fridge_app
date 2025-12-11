import cv2
import numpy as np
from paddleocr import PaddleOCR
import os
import json

class AdvancedOCRProcessor:
    def __init__(self, use_gpu=False):
        print("Loading PaddleOCR model...")
        self.ocr = PaddleOCR(lang='korean')   # CPU
        self.DEBUG_MODE = True

    def process(self, image_path: str) -> dict:
        # 1) 이미지 로드
        img_array = np.fromfile(image_path, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image is None:
            return {
                "status": "failure (Image load failed)",
                "line_count": 0,
                "lines": []
            }

        print("DEBUG: Starting OCR Process (PaddleOCR).")

        # 2) (일단 크롭 없이) 높이만 정규화
        target_process_height = 1200
        h, w = image.shape[:2]
        if h > 0:
            scale = target_process_height / h
            new_w = int(w * scale)
            image = cv2.resize(
                image, (new_w, target_process_height),
                interpolation=cv2.INTER_CUBIC
            )

        # 3) PaddleOCR 실행
        ocr_result = self.ocr.predict(image)
        if not ocr_result:
            return {
                "status": "success",
                "line_count": 0,
                "lines": []
            }

        res = ocr_result[0]
        texts = res["rec_texts"]
        boxes = res["rec_boxes"]   # [x1, y1, x2, y2]
        scores = res["rec_scores"]

        # 4) 각 텍스트에 x/y 중심 좌표 부여
        items = []
        for text, box, score in zip(texts, boxes, scores):
            x1, y1, x2, y2 = box
            x_center = (x1 + x2) / 2.0
            y_center = (y1 + y2) / 2.0
            items.append({
                "text": text,
                "x": x_center,
                "y": y_center,
                "score": float(score)
            })

        if not items:
            return {
                "status": "success",
                "line_count": 0,
                "lines": []
            }

        # 5) y 기준 정렬 후, 줄 단위로 묶기
        items.sort(key=lambda x: x["y"])
        lines_raw = []
        threshold = 12  # y 허용 오차

        for item in items:
            if not lines_raw:
                lines_raw.append([item])
                continue

            last_line = lines_raw[-1]
            last_y = np.mean([t["y"] for t in last_line])

            if abs(item["y"] - last_y) <= threshold:
                last_line.append(item)
            else:
                lines_raw.append([item])

        # 6) 줄 안에서 x 기준 정렬 후 텍스트 합치기
        lines = []
        for idx, line in enumerate(lines_raw, start=1):
            line_sorted = sorted(line, key=lambda x: x["x"])
            line_text = " ".join(t["text"] for t in line_sorted)
            avg_score = float(np.mean([t["score"] for t in line_sorted]))
            lines.append({
                "index": idx,
                "text": line_text,
                "avg_confidence": avg_score
            })

        print(f"DEBUG: PaddleOCR grouped {len(lines)} lines.")

        return {
            "status": "success",
            "line_count": len(lines),
            "lines": lines
        }
