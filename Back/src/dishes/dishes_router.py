from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from ..db.database import get_db_connection
from datetime import datetime

from .schemas import DishRegister, CookedDish
from .crud import register_cooked_dish_to_db
from ..ingredients.expiry_calculator import calculate_dish_expiry_date

# API 객체 생성
router = APIRouter(prefix="/dishes", tags=["Cooked Dishes"])

# POST /dishes/register (조리된 음식 등록)
@router.post("/register", response_model=CookedDish, summary="조리 음식 등록 및 유통기한 자동 지정")
def register_dish(item: DishRegister, conn: sqlite3.Connection = Depends(get_db_connection)):

    # 1. 유통기한 계산 로직
    calculated_date = calculate_dish_expiry_date(
        dish_type=item.type,
        manual_days=item.manual_days
    )
    
    # 2. DB에 최종 저장
    result = register_cooked_dish_to_db(
        conn=conn,
        name=item.name,
        dish_type=item.type,
        expiry_date=calculated_date,
        memo=item.memo
    )

    # 3. DB 저장 실패 처리
    if "message" in result and "실패" in result["message"]:
        raise HTTPException(status_code=500, detail=result["message"])

    # 4. 데이터 재구성 및 반환
    return CookedDish(
        id=result.get("id", 0),
        name=item.name,
        type=item.type,
        registration_date=datetime.now().strftime("%Y-%m-%d"),
        expiry_date=calculated_date,
        memo=item.memo,
        status='ACTIVE'
    )
