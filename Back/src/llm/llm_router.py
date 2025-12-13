# llm_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Union, Any
from .llm_processor import refine_ingredients_with_llm

router = APIRouter()

# ---------------------------------------------------------
# [수정] 입력 데이터 검증 모델 정의
# ---------------------------------------------------------

# 1. 개별 아이템 모델 (OCR 결과 1줄)
class OCRItem(BaseModel):
    text: str
    confidence: float

# 2. 요청 바디 모델
class LLMRequest(BaseModel):
    # data는 '문자열 리스트'일 수도 있고(구버전), 'OCRItem 리스트'일 수도 있음(신버전)
    # Union을 사용하여 두 형식을 모두 허용하도록 유연하게 설정
    data: List[Union[OCRItem, str, Any]]

@router.post("/refine")
async def refine_data(request: LLMRequest):
    try:
        # Pydantic 모델 리스트를 일반 딕셔너리 리스트로 변환
        # (llm_processor는 딕셔너리나 문자열을 처리할 수 있음)
        input_data = []
        for item in request.data:
            if isinstance(item, OCRItem):
                input_data.append(item.model_dump()) # 객체를 dict로 변환
            else:
                input_data.append(item) # 문자열이면 그대로

        # LLM 프로세서 호출
        results = refine_ingredients_with_llm(input_data)
        
        return {
            "status": "success", 
            "count": len(results),
            "data": results
        }
        
    except Exception as e:
        print(f"❌ LLM 라우터 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))