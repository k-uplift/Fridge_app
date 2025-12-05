import os
import sys
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__)) # Back/test
parent_dir = os.path.abspath(os.path.join(current_dir, "..")) # Back
sys.path.append(parent_dir)
# 모듈 가져오기
try:

    from src.llm.llm_router import router as llm_router
except ImportError as e:
    print("라우터를 찾을 수 없습니다. 경로를 확인해주세요.")
    print(f"Error: {e}")
    sys.exit(1)

app = FastAPI()
app.include_router(llm_router)
client = TestClient(app)

# 테스트 실행
def test_llm_refinement():
    input_filename = "ocr_result.json"
    output_filename = "llm_result.json"
    
    input_path = os.path.join(current_dir, input_filename)
    output_path = os.path.join(current_dir, output_filename)

    # OCR 결과 읽기
    if not os.path.exists(input_path):
        print(f"[Error] '{input_filename}' 파일이 없습니다. 먼저 test_ocr.py를 실행하세요.")
        return

    print(f"Loading data from: {input_filename}")
    with open(input_path, "r", encoding="utf-8") as f:
        ocr_json = json.load(f)

    # "data" 키에서 문자열 리스트 추출 (예: ["상품1", "상품2", ...])
    raw_data_list = ocr_json.get("data", [])
    
    if not raw_data_list:
        print("[Warning] 정제할 데이터가 없습니다.")
        return

    print(f"\n[Test] LLM 정제 시작 (총 {len(raw_data_list)}개 항목)")
    print("Ollama가 생각하는 중입니다... (시간이 조금 걸릴 수 있습니다)")

    # 라우터에 요청 전송
    payload = {"data": raw_data_list}

    try:
        response = client.post("/refine", json=payload)

        if response.status_code == 200:
            result_data = response.json()
            
            # 결과 저장
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            
            print(f"\n[Success] 정제 완료!")
            print(f"결과 파일 저장됨: {output_path}")
            
            # 결과
            print("\n--- LLM 정제 결과 미리보기 (Top 3) ---")
            preview = result_data.get('data', [])[:3]
            print(json.dumps(preview, ensure_ascii=False, indent=4))
            
        else:
            print(f"\n[Fail] HTTP 오류: {response.status_code}")
            print("Response:", response.text)

    except Exception as e:
        print(f"\n[Error] 테스트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    test_llm_refinement()