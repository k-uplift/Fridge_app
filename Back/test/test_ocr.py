import os
import sys
import json  # json 처리를 위한 모듈 추가
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ------------------------------------------------------------------
# 1. 경로 설정
# ------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__)) # Back/test
parent_dir = os.path.abspath(os.path.join(current_dir, "..")) # Back
sys.path.append(parent_dir)

# ------------------------------------------------------------------
# 2. 모듈 가져오기 & 앱 설정
# ------------------------------------------------------------------
from src.ocr.router import router as ocr_router

app = FastAPI()
app.include_router(ocr_router)
client = TestClient(app)

def test_ocr_endpoint():
    image_filename = "sample_receipt.jpg"
    image_path = os.path.join(current_dir, image_filename)
    
    # 결과 저장 경로
    output_filename = "ocr_result.json"
    output_path = os.path.join(current_dir, output_filename)

    if not os.path.exists(image_path):
        print(f"[Error] 이미지 파일이 없습니다: {image_path}")
        return

    print(f"\n[Test] OCR 분석 시작... ({image_filename})")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_filename, f, "image/jpeg")}
            response = client.post("/receipt", files=files)

        # HTTP 상태 코드 확인
        print(f"HTTP Status Code: {response.status_code}")

        if response.status_code == 200:
            result_data = response.json()
            
            # JSON 파일로 저장 (한글 깨짐 방지: ensure_ascii=False)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            
            print(f"\n[Success] 결과가 다음 파일에 저장되었습니다: {output_path}")
            
            # JSON 형식 출력
            print("\n--- JSON 결과 미리보기 ---")
            print(json.dumps(result_data, ensure_ascii=False, indent=4))
            
        else:
            print("\n[Fail] 요청 실패")
            print(json.dumps(response.json(), ensure_ascii=False, indent=4))

    except Exception as e:
        print(f"\n[Error] 테스트 중 예외 발생: {e}")

if __name__ == "__main__":
    test_ocr_endpoint()