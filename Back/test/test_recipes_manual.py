import os
import sys
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

# -------------------------------------------------------------------------
# 1. 경로 설정
# -------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__)) # Back/test
parent_dir = os.path.abspath(os.path.join(current_dir, "..")) # Back
sys.path.append(parent_dir)

# -------------------------------------------------------------------------
# 2. 모듈 가져오기 및 앱 설정
# -------------------------------------------------------------------------
try:
    from src.recipes.recipes_router import router as recipes_router
except ImportError as e:
    print("라우터를 찾을 수 없습니다. 경로를 확인해주세요.")
    print(f"Error: {e}")
    sys.exit(1)

app = FastAPI()
app.include_router(recipes_router)
client = TestClient(app)

# -------------------------------------------------------------------------
# 3. 테스트 실행 함수
# -------------------------------------------------------------------------
def test_recipe_recommendation_real():
    output_filename = "recipe_result_real.json"
    output_path = os.path.join(current_dir, output_filename)

    print("\n[Test] 실제 LLM 기반 레시피 추천 테스트 시작")
    
    # [입력 데이터셋] 앱에서 보낼 것과 똑같은 형식의 데이터
    # 냉장고에 이런 재료가 있다고 가정하고 서버에 보냅니다.
    request_payload = {
        "ingredients": [
            {"name": "돼지고기 목살", "quantity": 300, "unit": "g"},
            {"name": "묵은지", "quantity": "반", "unit": "개"},
            {"name": "두부", "quantity": 1, "unit": "개"},
            {"name": "양파", "quantity": 1, "unit": "개"},
            {"name": "대파", "quantity": 1, "unit": "개"}
        ]
    }
    
    print(f"입력 재료: {[item['name'] for item in request_payload['ingredients']]}")

    try:
        # [핵심 변경] POST 요청으로 데이터 전송
        # GET -> POST /recommend
        print("API 요청 중... (POST /recommend)")
        # 타임아웃 방지를 위해 timeout을 넉넉하게 잡을 수도 있습니다 (TestClient는 기본적으로 긺)
        response = client.post("/recommend", json=request_payload)

        if response.status_code == 200:
            result_data = response.json()
            
            # 결과 저장
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            
            print(f"\n[Success] 테스트 성공!")
            print(f"결과 파일 저장됨: {output_path}")
            
            # 결과 미리보기
            print("\n--- LLM이 추천한 레시피 ---")
            print(f"🥘 요리명: {result_data.get('recipe_name')}")
            print(f"⏱️ 소요시간: {result_data.get('time_required')}")
            print(f"📊 난이도: {result_data.get('difficulty')}")
            print("\n[필요한 재료]")
            print(f"보유 재료: {', '.join(result_data.get('ingredients_main', []))}")
            print(f"추가 필요: {', '.join(result_data.get('ingredients_needed', []))}")
            
            print("\n[조리 순서]")
            for idx, step in enumerate(result_data.get('steps', []), 1):
                print(f"{idx}. {step}")
            
        else:
            print(f"\n[Fail] HTTP 오류: {response.status_code}")
            print("Response:", response.text)

    except Exception as e:
        print(f"\n[Error] 테스트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    test_recipe_recommendation_real()