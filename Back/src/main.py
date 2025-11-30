#main.py (FastAPI 실행 및 API 경로 정의)

from fastapi import FastAPI
from database import initialize_database # DB 초기화 함수
from Fridge_app.Back.services import calculate_expiry_date, register_ingredient_to_db
from pydantic import BaseModel # 데이터 유효성 검사 및 모델링 도구
from typing import Optional 

# Pydantic 모델 정의 : 클라이언트(앱)로부터 받을 데이터의 구조와 타입을 정의
class IngredientRegister(BaseModel):
    name: str
    category_tag: str
    storage_location: str
    quantity: float
    unit: str
    manual_days: Optional[int] = None 

# FastAPI 서버 객체 생성
app = FastAPI()

# ---------- DB 초기화 이벤트 ----------

# FastAPI 서버가 시작될 때 (가장 처음에) 데이터베이스 초기화 함수를 호출
@app.on_event("startup")
def startup_event():
    print("FastAPI 서버 시작: 데이터베이스 초기화 작업 시작")
    initialize_database()

# ---------- API Endpoints (라우터) ----------

# 식재료 등록 API 
@app.post("/ingredients/register")
def register_ingredient(item: IngredientRegister):
    
    # 1. 유통기한 계산 로직 추출
    calculated_date = calculate_expiry_date(
        category=item.category_tag,
        storage=item.storage_location,
        manual_days=item.manual_days     
    )

    # 2. DB에 최종 저장
    # 계산된 유통기한을 포함하여 데이터를 DB에 저장
    result = register_ingredient_to_db(
        name=item.name,
        category=item.category_tag,
        storage=item.storage_location,
        quantity=item.quantity,
        unit=item.unit,
        expiry_date=calculated_date
    )

    return result