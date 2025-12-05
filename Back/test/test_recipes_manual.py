import os
import sys
import json
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# -------------------------------------------------------------------------
# 1. 경로 설정 (test_llm.py와 동일한 방식)
# -------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__)) # Back/test
parent_dir = os.path.abspath(os.path.join(current_dir, "..")) # Back
sys.path.append(parent_dir)

# -------------------------------------------------------------------------
# 2. 모듈 가져오기 및 앱 설정
# -------------------------------------------------------------------------
try:
    # src 패키지 하위의 router를 가져옵니다.
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
def test_recipe_recommendation():
    output_filename = "recipe_result.json"
    output_path = os.path.join(current_dir, output_filename)

    print("\n[Test] 레시피 추천 API 테스트 시작")
    print("가상의 DB 데이터와 LLM 응답을 설정하여 테스트합니다...")

    # Mocking: 실제 DB와 LLM을 호출하지 않고 가짜 데이터를 주입합니다.
    # (실제 DB 연결 없이 로직이 잘 도는지 확인하기 위함)
    with patch('src.recipes.llm_recipe_service.get_db_connection') as mock_get_db, \
         patch('src.recipes.llm_recipe_service.recipe_processor') as mock_llm_processor:

        # [상황 1] DB Mock 설정 (냉장고에 재료가 있다고 가정)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 가짜 식재료 리스트 반환
        mock_cursor.fetchall.return_value = [
            {'name': '삼겹살', 'quantity': '300', 'unit': 'g'},
            {'name': '김치', 'quantity': '1/2', 'unit': '포기'},
            {'name': '두부', 'quantity': '1', 'unit': '모'}
        ]

        # [상황 2] LLM Mock 설정 (AI가 레시피를 만들어줬다고 가정)
        expected_llm_response = {
            "recipe_name": "돼지고기 김치찌개",
            "steps": [
                "김치와 돼지고기를 먹기 좋은 크기로 썬다.",
                "냄비에 김치와 고기를 넣고 볶는다.",
                "물을 붓고 끓이다가 두부를 넣는다."
            ],
            "ingredients_needed": ["삼겹살", "김치", "두부", "대파", "마늘"]
        }
        mock_llm_processor.return_value = expected_llm_response

        # -----------------------------------------------------------
        # API 요청 전송 (GET /recommend)
        # -----------------------------------------------------------
        try:
            print("API 요청 중... (GET /recommend)")
            response = client.get("/recommend")

            if response.status_code == 200:
                result_data = response.json()
                
                # 결과 저장
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=4)
                
                print(f"\n[Success] 테스트 성공!")
                print(f"결과 파일 저장됨: {output_path}")
                
                # 결과 미리보기
                print("\n--- 레시피 추천 결과 미리보기 ---")
                print(f"요리명: {result_data.get('recipe_name')}")
                print("조리 순서:")
                for step in result_data.get('steps', []):
                    print(f"- {step}")
                
            else:
                print(f"\n[Fail] HTTP 오류: {response.status_code}")
                print("Response:", response.text)

        except Exception as e:
            print(f"\n[Error] 테스트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    test_recipe_recommendation()