# [llm_router.py]

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Any
# [수정] refine_batch_items 대신 refine_ingredients_with_llm 임포트
from .llm_processor import refine_ingredients_with_llm

router = APIRouter()

# 1) OCR 결과 한 장에 대한 요청 스키마
class OCRLine(BaseModel):
    index: int
    text: str
    avg_confidence: Optional[float] = None

class OCRLinesPayload(BaseModel):
    line_count: int
    lines: List[OCRLine]
    image_path: Optional[str] = None

# 2) LLM이 돌려줄 식재료 결과 스키마
class IngredientItem(BaseModel):
    product_name: str
    category: str
    quantity: float
    unit: str

@router.post("/refine", response_model=List[IngredientItem])
async def refine_from_ocr(payload: OCRLinesPayload):
    """
    ocr_result.json 형식을 받아서
    필터링 -> 배치 처리 -> LLM 변환 과정을 거쳐 식재료 리스트 반환
    """
    
    # Pydantic 모델 리스트를 딕셔너리 리스트로 변환 (processor 호환용)
    ocr_data_list = [line.model_dump() for line in payload.lines]

    # [핵심 수정] 매니저 함수 호출 + image_path 전달
    refined_items = refine_ingredients_with_llm(
        ocr_data_list=ocr_data_list,
        image_path=payload.image_path  # 경로 전달
    )

    return refined_items