import easyocr
import os
import glob
import json
import time

def run_ocr_and_save_json(output_filename="ocr_results.json"):
    # 1. EasyOCR Reader 초기화 (최초 한 번만 실행됨)
    print("Initializing EasyOCR model... (This may take a while initially)")
    # 한국어('ko'), 영어('en') 모델 로드.
    # GPU가 있다면 gpu=True로 변경 시 속도가 매우 빨라집니다.
    reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)
    print("Model loaded successfully.")

    # 2. 처리할 이미지 파일 찾기 (_warped.jpg 파일만 대상)
    current_dir = os.getcwd()
    # 현재 폴더에서 _warped.jpg로 끝나는 모든 파일을 찾아서 정렬
    target_files = sorted(glob.glob(os.path.join(current_dir, "*_warped.jpg")))

    if not target_files:
        print("No '*_warped.jpg' files found. Please run the preprocessing script first.")
        return

    print(f"Found {len(target_files)} warped images to process.")
    print("-" * 30)

    # 결과를 저장할 딕셔너리
    all_results = {}

    start_time = time.time()

    # 3. 각 이미지에 대해 OCR 수행
    for file_path in target_files:
        file_name = os.path.basename(file_path)
        print(f"Reading text from: {file_name}...")

        try:
            # --- EasyOCR 핵심 함수 ---
            # image_path: 이미지 파일 경로
            # detail=0: 복잡한 좌표 정보 없이 인식된 '텍스트'만 리스트로 반환합니다.
            # (예: ['영수증', '2024-03-23', '금액 5,000원', ...])
            result_text_list = reader.readtext(file_path, detail=0)
            
            # 결과 딕셔너리에 저장 (파일명이 키, 텍스트 리스트가 값)
            all_results[file_name] = result_text_list
            print(f" -> Success. Extracted {len(result_text_list)} lines of text.")

        except Exception as e:
            print(f" -> Error processing {file_name}: {e}")
            all_results[file_name] = {"error": str(e)}

    # 4. 결과를 JSON 파일로 저장
    output_path = os.path.join(current_dir, output_filename)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False: 한글이 유니코드 코드가 아닌 읽을 수 있는 문자로 저장됨
            # indent=4: 들여쓰기를 하여 보기 좋게 저장됨
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        
        end_time = time.time()
        print("-" * 30)
        print(f"Completed in {end_time - start_time:.2f} seconds.")
        print(f"All OCR results saved to: {output_path}")

    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    # 스크립트 실행
    # 전처리된 이미지가 있는 폴더에서 실행해야 합니다.
    print(f"Current Working Directory: {os.getcwd()}")
    run_ocr_and_save_json()