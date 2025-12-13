# recipes_router.py

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List
from pydantic import BaseModel
from .llm_recipe_service import get_final_recipe_recommendation

router = APIRouter()

class IngredientItem(BaseModel):
    name: str
    quantity: str | float | int = "" # 수량은 없을 수도 있으므로 유연하게
    unit: str = ""

class RecipeRequest(BaseModel):
    ingredients: List[IngredientItem] # 식재료 리스트

@router.post("/recommend", response_model=Dict[str, Any], summary="LLM 기반 레시피 추천", tags=["Recipes"])
def recommend_recipe(request: RecipeRequest):
    try:
        # Pydantic 모델을 딕셔너리나 문자열 리스트로 변환하여 서비스로 전달
        # 예: ["두부 (1개)", "양파 (2개)"] 형식으로 변환
        formatted_ingredients = [
            f"{item.name} ({item.quantity}{item.unit})".strip() 
            for item in request.ingredients
        ]

        if not formatted_ingredients:
            raise HTTPException(status_code=400, detail="식재료 목록이 비어있습니다.")

        # 서비스 함수 호출 (DB 조회 대신 받은 리스트 전달)
        recipe_data = get_final_recipe_recommendation(ingredients_list=formatted_ingredients)

        if "recipe_name" not in recipe_data:
            raise HTTPException(status_code=500, detail="LLM이 유효한 레시피 응답을 반환하지 않았습니다.")
        
        return recipe_data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"레시피 추천 API 오류: {e}")
        # 사용자에게 너무 자세한 에러는 숨기고 500 반환
        raise HTTPException(status_code=500, detail="레시피 추천 시스템 처리 중 오류가 발생했습니다.")