from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from ..db.database import get_db_connection
from datetime import datetime
from typing import List

from .dishes_schemas import DishRegister, CookedDish, DishUpdate
from .dishes_crud import (register_cooked_dish_to_db, get_all_cooked_dishes, 
                          get_cooked_dish_by_id, update_cooked_dish_db, delete_cooked_dish_db)
from ..ingredients.expiry_calculator import calculate_dish_expiry_date

# API 객체 생성
router = APIRouter(prefix="", tags=["Cooked Dishes"])

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

# GET /dishes/list (조리된 음식 목록 조회)
@router.get("/list", response_model=List[CookedDish], summary="조리된 음식 목록 조회")
def list_dishes(conn: sqlite3.Connection = Depends(get_db_connection)):

    dishes = get_all_cooked_dishes(conn)

    return [CookedDish(**dict(row)) for row in dishes]

# PUT /dishes/{dish_id} (조리된 음식 수정)
@router.put("/{dish_id}", response_model=CookedDish, summary="조리 음식 정보 수정")
def update_dish(
    dish_id: int, 
    item: DishUpdate,
    conn: sqlite3.Connection = Depends(get_db_connection)
):
    update_data = item.model_dump(exclude_unset=True) 

    # 1. manual_days가 수정되었다면 expiry_date를 다시 계산
    if 'manual_days' in update_data:
        existing_dish = get_cooked_dish_by_id(conn, dish_id)
        if not existing_dish:
            raise HTTPException(status_code=404, detail=f"ID {dish_id}의 음식을 찾을 수 없습니다.")

        existing_dish_dict = dict(existing_dish)
        current_type = update_data.get('type', existing_dish_dict.get('type'))
        
        calculated_date = calculate_dish_expiry_date(
            dish_type=current_type,
            manual_days=update_data['manual_days']
        )
        update_data['expiry_date'] = calculated_date
        del update_data['manual_days'] 

    # 2. DB 업데이트
    result = update_cooked_dish_db(conn, dish_id, update_data)
    
    if not result["success"]:
        status_code = 404 if "찾을 수 없습니다" in result["message"] else 400
        raise HTTPException(status_code=status_code, detail=result["message"])

    # 3. 수정된 항목 재조회 및 반환
    updated_dish_row = get_cooked_dish_by_id(conn, dish_id)
    if not updated_dish_row:
         raise HTTPException(status_code=500, detail="수정 후 데이터 조회 실패")

    return CookedDish(**dict(updated_dish_row))


# DELETE /dishes/{dish_id} (조리된 음식 삭제)
@router.delete("/{dish_id}", summary="조리 음식 삭제")
def delete_dish(dish_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):

    result = delete_cooked_dish_db(conn, dish_id)

    if not result["success"]:
        status_code = 404 if "찾을 수 없습니다" in result["message"] else 500
        raise HTTPException(status_code=status_code, detail=result["message"])

    return {"message": f"ID {dish_id}의 음식이 성공적으로 삭제되었습니다."}