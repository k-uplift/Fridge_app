from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Union, Optional, Any
from .llm_processor import refine_ingredients_with_llm

router = APIRouter()

# ---------------------------------------------------------
# [수정] 입력 데이터 검증 모델 (관대하게 변경)
# ---------------------------------------------------------

class OCRItem(BaseModel):
    # Field(default=...)를 사용하여 값이 없어도 에러가 나지 않게 설정
    raw_text: str = Field(default="", description="OCR 인식 텍스트")
    confidence: List[float] = Field(default_factory=list, description="글자별 신뢰도")
    avg_confidence: float = Field(default=0.0, description="평균 신뢰도")
    
    # 혹시 모를 구버전 호환성 (text 필드가 들어올 경우를 대비)
    text: Optional[str] = None 

    class Config:
        # 모델에 정의되지 않은 추가 필드가 들어와도 에러 내지 않고 무시
        extra = "ignore" 

class OCRResultPayload(BaseModel):
    status: str = "unknown"
    count: int = 0
    data: List[OCRItem] = Field(default_factory=list)

# ---------------------------------------------------------
# [디버깅] 422 에러 상세 내용을 터미널에 출력하기 위한 핸들러
# main.py에 추가하면 좋지만, 여기서 로직으로 처리할 수도 있음
# ---------------------------------------------------------

@router.post("/refine")
async def refine_data(payload: Union[OCRResultPayload, List[Any]]):
    """
    Input: 
      - Case A: { "status": "...", "data": [...] } (전체 JSON)
      - Case B: [ ... ] (리스트만 직접 전송한 경우)
    Union을 사용하여 두 경우 모두 허용
    """
    try:
        input_data = []

        # 입력 데이터 구조 파악 및 정규화
        if isinstance(payload, OCRResultPayload):
            # Case A: 전체 JSON 객체로 들어온 경우
            raw_list = payload.data
        elif isinstance(payload, list):
            # Case B: 리스트만 들어온 경우
            raw_list = payload
        else:
            raw_list = []

        # Pydantic 모델 -> dict 변환 및 필드 매핑 보정
        for item in raw_list:
            if isinstance(item, OCRItem):
                # 객체를 dict로 변환
                item_dict = item.dict()
            elif isinstance(item, dict):
                # 딕셔너리 그대로 사용
                item_dict = item
            else:
                continue

            # (중요) llm_processor가 'text'를 요구할 수도 있으니 매핑
            # raw_text가 있으면 text로 복사해주거나 processor 로직을 따라감
            if 'raw_text' in item_dict and not item_dict.get('text'):
                item_dict['text'] = item_dict['raw_text']
            
            input_data.append(item_dict)

        print(f"✅ LLM Processor로 전달되는 아이템 수: {len(input_data)}")

        # LLM 프로세서 호출
        results = refine_ingredients_with_llm(input_data)
        
        return {
            "status": "success", 
            "count": len(results),
            "data": results
        }
        
    except Exception as e:
        import traceback
        print("❌ LLM 라우터 내부 에러:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))