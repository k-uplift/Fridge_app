# schemas.py

from pydantic import BaseModel
from typing import Optional

# 조리 음식 등록 요청을 위한 스키마
class DishRegister(BaseModel):
    name: str
    type: str
    memo: Optional[str] = None
    manual_days: Optional[int] = None # 수동 지정 시 기본값 덮어쓰기용


# 조리 음식 응답/조회를 위한 스키마
class CookedDish(BaseModel):
    id: int
    name: str
    type: str
    registration_date: str
    expity_date: str
    memo: Optional[str] = None
    status: str
