# llm_recipe_service.py

from typing import List, Dict, Any, Optional
from ..db.database import get_db_connection
from ..llm.llm_processor import run_recipe_llm as recipe_processor

# DB - 사용자 식재료 조회
def get_user_ingredients_list() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 유통기한이 오늘 이후인 식재료만 조회
        cursor.execute("""
            SELECT
                name,quantity,unit
            FROM Ingredients
            WHERE status = 'active' 
                AND expiry_date >= DATE('now')
            ORDER BY expiry_date ASC         
        """)

        ingredients = [
            f"{row['name']} ({row['quantity']}{row['unit']})"
            for row in cursor.fetchall()
        ]

        return ingredients
    
    except Exception as e:
        print(f"[DB ERROR] 식재료 조회 오류: {e}")
        return []

    finally:
        conn.close()


# LLM 요청 - 레시피 생성
def recommend_recipe_from_llm(ingredients_list: List[str]) -> Dict[str, Any]:
    # 보유 식재료 목록을 기반으로 LLM에 레시피를 요청하고 응답을 정제
    if not ingredients_list:
        return {
            "recipe_name": "재료 부족", 
            "steps": ["냉장고에 재료가 없습니다. 먼저 식재료를 등록해주세요."], 
            "ingredients_needed": []
        }
    
    ingredients_text = ", ".join(ingredients_list)

    # user prompt 구현
    user_prompt = f"""
    다음은 사용자가 현재 보유한 식재료 목록입니다:

    {ingredients_text}

    위 재료들을 최대한 많이 활용하여 만들 수 있는 현실적인 요리 레시피를 하나 추천해주세요.
    가능하면 유통기한이 임박한 재료를 우선적으로 사용해 주세요.

    반드시 system_prompt에서 요구한 JSON 형식에 맞춰 출력하세요.
    """

    try:
        response_json = recipe_processor(user_prompt)
        return response_json
    
    except Exception as e:
        print(f"[LLM ERROR] 레시피 생성 오류: {e}")
        return {
            "recipe_name": "오류", 
            "steps": [f"LLM 요청 중 오류 발생: {str(e)}"], 
            "ingredients_needed": []
        }
    
# 외부 진입점 - 최종 레시피 추천
def get_final_recipe_recommendation(ingredients_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    ingredients_list가 주어지면 그걸 쓰고, 
    없으면(None) DB에서 조회해서 추천한다.
    """
    
    # 1. 인자로 받은 리스트가 없으면 DB에서 조회 (기존 로직 하위 호환)
    if not ingredients_list:
        print("[Service] 입력된 재료가 없어 DB에서 조회합니다.")
        ingredients_list = get_user_ingredients_list()
    else:
        print(f"[Service] 앱에서 전달받은 재료 {len(ingredients_list)}개를 사용합니다.")

    # 2. LLM 호출
    return recommend_recipe_from_llm(ingredients_list)
    
