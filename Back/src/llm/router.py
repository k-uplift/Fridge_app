from fastapi import APIRouter, HTTPException, Body
from typing import List

try:
    from .llm_processor import refine_ingredients_with_llm
except ImportError:
    from src.llm.llm_processor import refine_ingredients_with_llm

router = APIRouter()

@router.post("/refine", summary="OCR 원시 데이터 LLM 정제")
async def refine_ingredients(data: List[str] = Body(..., embed=True)):
    """
    OCR로 추출된 문자열 리스트를 받아 LLM을 통해 정제합니다.
    """
    try:
        if not data:
            return {"status": "empty", "data": []}
        # 문자열 리스트를 딕셔너리 리스트로 변환
        formatted_input = [{"product_name": text} for text in data]

        refined_data = refine_ingredients_with_llm(formatted_input)
        
        return {
            "status": "success",
            "count": len(refined_data),
            "data": refined_data
        }

    except Exception as e:
        print(f"LLM 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))