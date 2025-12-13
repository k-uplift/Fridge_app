# expiry_calculator.py (유통기한 계산

from datetime import datetime, timedelta, date
from typing import Optional, Any
from ..db.database import get_db_connection
from .ingredients_crud import get_id_by_name

def calculate_expiry_date(category_tag: str, storage_location: str, manual_days: Optional[int] = None) -> str:

    # 유통기한 수동 지정
    if manual_days is not None and manual_days >= 0:
        default_days = manual_days
    else:
        # 유통기한 자동 설정(식재료 태그, 보관 위치 기반)
        conn = get_db_connection()
        try:
            category_id = get_id_by_name(conn, 'Categories', category_tag)
            location_id = get_id_by_name(conn, 'Storage_Locations', storage_location)

            cursor = conn.cursor()

            # 표준 일수 조회
            cursor.execute("""
                    SELECT default_days FROM Expiration_Mapping
                    WHERE category_id = ? AND storage_location_id = ?
            """, (category_id, location_id))

            result: Any = cursor.fetchone()

            if result:
                default_days = result['default_days']
            else:
                #매핑 데이터가 없는 경우
                default_days = 3
                print(f"경고: 매칭 데이터가 없습니다. 3일 기본값 적용: {category_tag}, {storage_location}")

        except ValueError as e:
            # ID를 찾지 못한 경우
            default_days = 3
            print(f"오류: {e}. 유통기한 기본값 3일 적용.")
        finally:
            conn.close()

    # 유통기한 만료 날짜 계산
    today = datetime.now()
    expiry_date = today + timedelta(days=default_days)

    return expiry_date.strftime("%Y-%m-%d")

# 조리 음식 종류에 따라 유통기한을 자동 계산
def calculate_dish_expiry_date(dish_type: str, manual_days: Optional[int] = None) -> str:
    if manual_days is not None and manual_days > 0:
        default_days = manual_days
    else:
        dish_type = dish_type.lower()
        if dish_type == '조리음식':
            default_days = 3
        elif dish_type == '냉동식품':
            default_days = 30
        elif dish_type == '그 외':
            default_days = 7
        else:
            default_days = 7

    # 오늘 날짜 + 기본 일수 계산
    expiry_date = date.today() + timedelta(days=default_days)
    return expiry_date.strftime("%Y-%m-%d")
        