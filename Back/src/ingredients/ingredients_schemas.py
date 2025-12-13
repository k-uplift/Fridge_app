from pydantic import BaseModel
from typing import Optional

# API 요청 모델
class IngredientRegister(BaseModel):
    # 식재료 등록 시 클라이언트로부터 받는 데이터 모델
    name: str
    category_tag: str
    storage_location: str
    quantity: float
    unit: str
    # 유통기한 수동 지정 기능에 사용
    manual_days: Optional[int] = None

# 데이터베이스 응답 모델  
class Ingredient(BaseModel):
    # DB에서 조회 후 클라이언트에게 반환할 식재료 데이터 모델
    # 등록 시 받은 필드 외에 DB에서 생성된 필드가 추가

    # DB에서 생성되는 필드
    id: int
    expiry_date: str
    registration_date: str

    # DB에서 저장되는 ID 필드
    category_id: int
    storage_location_id: int

    # 나머지 필수 입력 필드
    name: str
    quantity: float
    unit: str

    # 상태 필드
    status: str
    is_cooked: bool
    memo: Optional[str] = None
    source_image_id: Optional[int] = None

    class Config:
        from_attributes = True

# 유통기한 매핑 데이터 모델  
class ExpirationMapping(BaseModel):
    category_tag: str
    storage_location: str
    default_days: int