# recipes_router.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from .llm_recipe_service import get_final_recipe_recommendation

router = APIRouter()

@router.get("/recommend", response_model=Dict[str, Any], summary="LLM 기반 레시피 추천", tags=["Recipes"])
def recommend_recipe():
    # 현재 냉장고에 있는 식재료를 기반으로 LLM이 추천하는 레시피를 반환
    try:
        recipe_data = get_final_recipe_recommendation()

        if "recipe_name" not in recipe_data:
            raise HTTPException(status_code=500, detail="LLM이 유효한 레시피 응답을 반환하지 않았습니다.")
        
        return recipe_data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"레시피 추천 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"레시피 추천 시스템 처리 실패: ")