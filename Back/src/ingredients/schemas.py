from pydantic import BaseModel
from typing import Optional

# 1. API 요청 모델
class IngredientRegister(BaseModel):
    # 식재료 등록 시 클라이언트로부터 받는 데이터 모델
    name: str
    category_tag: str
    storage_location: str
    quantity: float
    unit: str

    # 유통기한 수동 지정 기능에 사용
    manual_days: Optional[int] = None


#2. 데이터베이스 응답 모델  
class Ingredient(IngredientRegister):
    # DB에서 조회 후 클라이언트에게 반환할 식재료 데이터 모델
    # 등록 시 받은 필드 외에 DB에서 생성된 필드가 추가
    id: int
    expiry_date: str
    registration_date: str

    class Config:
        # Pydantic이 ORM(DB 객체) 모드를 지원하도록 설정
        from_attributes = True


#3. 유통기한 매핑 데이터 모델  
class ExpirationMapping(BaseModel):
    # Expiration_Mapping 테이블의 데이터 구조 모델 (B1, B2 기능 관련)
    category_tag: str
    storage_location: str
    default_days: int