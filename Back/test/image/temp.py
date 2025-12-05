import cv2
import numpy as np
import imutils
import os
import glob

def order_points(pts):
    # [좌상, 우상, 우하, 좌하] 정렬
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # 너비, 높이 최대값 계산
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def process_receipt_final(image_path):
    print(f"Processing: {os.path.basename(image_path)}")
    image = cv2.imread(image_path)
    if image is None:
        return

    # 이미지가 너무 크면 리사이즈 (속도 및 정확도 향상)
    ratio = image.shape[0] / 500.0
    orig = image.copy()
    image_resized = imutils.resize(image, height=500)

    # 1. 전처리 (Gray -> Blur -> Canny)
    gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 임계값을 조금 낮춰서 희미한 선도 잡도록 조정 (30, 150)
    edged = cv2.Canny(blurred, 30, 150)

    # **핵심 수정**: 끊어진 선을 아주 강력하게 이어붙임 (iterations=3~5)
    # 영수증 테두리가 없어도 글자 덩어리들을 하나로 뭉치게 함
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(edged, kernel, iterations=4) 

    # 디버깅용: 컴퓨터가 인식한 하얀색 덩어리를 보고 싶으면 아래 주석 해제
    # cv2.imwrite(image_path + "_debug.jpg", dilated)

    # 2. 윤곽선 찾기
    cnts = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    
    # 면적순 정렬
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    receiptCnt = None
    
    if len(cnts) > 0:
        # 가장 큰 덩어리 가져오기
        c = cnts[0]
        
        # 전략 A: 꼭짓점 4개 근사
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        if len(approx) == 4:
            receiptCnt = approx
            # print(" -> Found 4 corners.")
        else:
            # 전략 B: 4개가 아니면 그냥 박스 씌우기 (가장 강력함)
            # print(" -> Using Bounding Box.")
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            # np.int0 대신 int64 사용 (버전 호환성 해결)
            box = np.int64(box)
            receiptCnt = box

    if receiptCnt is None:
        print(f" -> Skipped (No contour found)")
        return

    # 3. 투시 변환
    if receiptCnt.ndim == 2: 
        pts = receiptCnt.astype("float32") * ratio
    else: 
        pts = receiptCnt.reshape(4, 2).astype("float32") * ratio

    warped = four_point_transform(orig, pts)

    # 결과가 너무 작으면(노이즈) 저장 안함 (기준: 100x100)
    if warped.shape[0] < 100 or warped.shape[1] < 100:
         print(" -> Result too small (Noise). Skipped.")
         return

    # 4. 저장
    filename, ext = os.path.splitext(os.path.basename(image_path))
    
    # 이미 처리된 파일(_warped)은 건너뛰기
    if "_warped" in filename:
        return

    output_path = os.path.join(os.path.dirname(image_path), f"{filename}_warped.jpg")
    cv2.imwrite(output_path, warped)
    print(f" -> Saved: {os.path.basename(output_path)}")

if __name__ == "__main__":
    # 현재 폴더 설정
    current_dir = os.getcwd()
    print(f"Target Directory: {current_dir}")
    print("Scanning for images...")

    # 폴더 내의 모든 jpg, png, jpeg 파일을 자동으로 찾음
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.PNG']
    image_files = []
    
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(current_dir, ext)))

    # 중복 제거 및 정렬
    image_files = sorted(list(set(image_files)))
    
    count = 0
    for file_path in image_files:
        # _warped가 붙은 결과 파일은 입력에서 제외
        if "_warped" in file_path:
            continue
            
        process_receipt_final(file_path)
        count += 1

    print("-" * 30)
    print(f"Completed processing {count} files.")