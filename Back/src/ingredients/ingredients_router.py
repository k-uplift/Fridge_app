# router.py (API 엔드포인트 분리)

from fastapi import APIRouter, Depends, HTTPException, Query
import sqlite3
from typing import Any, List
from datetime import datetime
from ..db.database import get_db_connection

from .schemas import IngredientRegister, Ingredient

from .crud import register_ingredient_to_db, get_id_by_name
from .expiry_calculator import calculate_expiry_date
from .labeling import calculate_remaining_days, get_visual_labeling_data
from .notifier import get_alert_ingredients

# API 객체 생성
router = APIRouter()

# POST /register (식재료 등록)
@router.post("/register", response_model=Ingredient, tags=["Ingredients"])
def register_ingredient(item: IngredientRegister, conn: sqlite3.Connection = Depends(get_db_connection)):

    # 1. 문자열 태그를 ID로 변환
    try:
        category_id = get_id_by_name(conn, 'Categories', item.category_tag)
        location_id = get_id_by_name(conn, 'Storage_Locations', item.storage_location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"등록 실패: {e}")

    # 2. 유통기한 계산 로직 추출
    calculated_date = calculate_expiry_date(
        category_tag=item.category_tag,
        storage_location=item.storage_location,
        manual_days=item.manual_days
    )

    # 3. DB에 최종 저장
    result = register_ingredient_to_db(
        name=item.name,
        category_id=category_id,
        storage_location_id=location_id,
        quantity=item.quantity,
        unit=item.unit,
        expiry_date=calculated_date
    )

    # 4. DB 저장 실페
    if "message" in result and "등록 실패" in result["message"]:
        raise HTTPException(status_code=500, detail=result["message"])

    # 5. 데이터 재구성 및 반환(Ingredient Respone Model에 맞게)
    return Ingredient(
        id = result.get("id", 0),
        name = item.name,
        quantity = item.quantity,
        unit = item.unit,
        category_id = category_id,
        storage_location_id = location_id,
        expiry_date = calculated_date,
        registration_date = datetime.now().strftime("%Y-%m-%d"),
        status = 'active',
        is_cooked = False,
        memo = None,
        source_image_id = None
    )


# GET/list (시각적 라벨링 포함 전체 목록 조회)
@router.get("/list", response_model=List[Any], tags=["Ingredients"])
def list_ingredients(conn: sqlite3.Connection = Depends(get_db_connection)):
    # 모든 활성화된 식재료 목록을 유통기한 임박 순으로 반환
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, expiry_date, quantity, unit, category_id, storage_location_id
        FROM Ingredients
        WHERE status = 'active'
        ORDER BY expiry_date ASC
    """)
    rows = cursor.fetchall()

    ingredients_list = []

    # 시각적 라벨링 데이터 계산 로직 반복 적용
    for row in rows:
        ingredient = dict(row)

        remaining_days = calculate_remaining_days(ingredient['expiry_date'])
        labeling_data = get_visual_labeling_data(remaining_days)

        ingredient.update(labeling_data)
        ingredients_list.append(ingredient)

    return ingredients_list


# GET/alerts (유통기한 임박 알림)
@router.get("/alerts", response_model=List[Any], tags=["Notifications"])
def get_expiry_alerts(
    alert_days: int = Query(7, description="오늘부터 며칠 이내의 유통기한 임박 식재료를 조회할지 (기본 7일)")
):
    # 유통기한 임박 알림 대상 식재료 목록을 반환
    if alert_days < 1:
        raise HTTPException(status_code=400, detail="alert_days는 1 이상의 값이어야 합니다.")
    
    alert_list = get_alert_ingredients(alert_days)

    return alert_list

