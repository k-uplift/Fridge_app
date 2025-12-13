import os
import sys
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

try:
    from src.llm.llm_router import router as llm_router
except ImportError as e:
    print(f"Error importing router: {e}")
    sys.exit(1)

app = FastAPI()
app.include_router(llm_router)
client = TestClient(app)

def test_llm_refinement():
    input_filename = "ocr_result.json"
    output_filename = "llm_result.json"
  
    input_path = os.path.join(current_dir, input_filename)
    output_path = os.path.join(current_dir, output_filename)

    if not os.path.exists(input_path):
        print(f"[Error] '{input_filename}' 파일이 없습니다.")
        return

    print(f"Loading data from: {input_filename}")
    with open(input_path, "r", encoding="utf-8") as f:
        ocr_json = json.load(f)

    lines = ocr_json.get("lines", [])
    payload = {
        "line_count": len(lines),
        "lines": lines, # 이미 딕셔너리 리스트이므로 그대로 전달
    }
    
    try:
        response = client.post("/refine", json=payload)

        if response.status_code == 200:
            result_data = response.json() # 이것은 리스트([])입니다.
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            
            print(f"\n[Success] 정제 완료! (총 {len(result_data)}개 추출)")
            print(f"결과 파일: {output_path}")
            
            # [수정된 부분] 리스트에서 바로 슬라이싱
            print("\n--- 결과 미리보기 (Top 3) ---")
            if isinstance(result_data, list):
                preview = result_data[:3]
                print(json.dumps(preview, ensure_ascii=False, indent=4))
            else:
                print("결과 형식이 리스트가 아닙니다.")
                
        else:
            print(f"\n[Fail] HTTP {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n[Error] 테스트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    test_llm_refinement()