#service.py (유통기한 계산 및 시각적 라벨링)

from datetime import datetime, timedelta
import sqlite3
from typing import Optional, Any, Dict
from ..db.database import get_db_connection

#  TEXT로 ID 조회
def get_id_by_name(conn: sqlite3.Connection, table_name: str, name: str) -> int:
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table_name} WHERE name = ?", (name, ))
    result = cursor.fetchone()
    if result:
        return result['id']

    raise ValueError(f"ID를 찾을 수 없습니다: {table_name} - {name}")

# --- 유통기한 계산 로직 ---
def calculate_expiry_date(category_tag: str, storage_location: str, manual_days: Optional[int] = None) -> str:
    default_days: int

    # 유통기한 수동 지정
    if manual_days is not None and manual_days >= 0:
        default_days = manual_days
    else:
        # 유통기한 자동 설정(식재료 태그, 보관 위치 기반)
        conn = get_db_connection()
        try:
            category_id = get_id_by_name(conn, 'Categories', category_tag)
            storage_location_id = get_id_by_name(conn, 'Storage_Locations', storage_location)

            cursor = conn.cursor()

            # 표준 일수 조회
            cursor.execute("""
                    SELECT default_days FROM Expiration_Mapping
                    WHERE category_id = ? AND storage_location_id = ?
            """, (category_id, storage_location_id))

            result: Optional[sqlite3.Row] = cursor.fetchone()

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

# --- 시각적 라벨링 로직 ---

# 유통기한 만료 날짜를 기준으로 오늘까지 남은 일수 계산
def calculate_remaining_days(expiry_date_str: str) -> int:
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"유효하지 않은 날짜 포맷: {expiry_date_str}")
        return 0

    today = datetime.now().date()
    remaining_delta = expiry_date - today

    return remaining_delta.days

# 남은 일수에 따라 라벨링 정보 반환(색상 기준)
def get_visual_labeling_data(remaining_days: int) -> Dict[str, Any]:

    if remaining_days < 0:
        label_text = f"{abs(remaining_days)}일 지남"
        label_color = 'red'
    elif remaining_days <= 3:
        label_text = f"{remaining_days}일 남음"
        label_color = 'orange'
    elif remaining_days <= 7:
        label_text = f"{remaining_days}일 남음"
        label_color = 'yellow'
    else:
        label_text = f"{remaining_days}일 남음"
        label_color = 'green'

    return {
        "remaining_days": remaining_days,
        "label_text": label_text,
        "label_color": label_color
    }

# --- DB 저장 로직 ---
def register_ingredient_to_db(
        name: str, 
        category_id: int,
        storage_location_id: int,
        quantity: float, 
        unit: str, 
        expiry_date: str
    ) -> Dict[str, Any]:

    # 유통기한, 식재료 정보 Ingredients 테이블에 저장
    conn = get_db_connection()
    cursor = conn.cursor()
    registration_date = datetime.now().strftime("%Y-%m-%d") 

    try:
        cursor.execute("""
            INSERT INTO Ingredients
            (name, category_id, storage_location_id, quantity, unit, expiry_date, registration_date, status, is_cooked, memo, source_image_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, category_id, storage_location_id, quantity, unit, expiry_date, registration_date, 'active', 0, None, None))

        conn.commit()

        return {
            "message": "식재료 등록 완료",
            "id": cursor.lastrowid,
            "expiry_date": expiry_date
        }
    except Exception as e:
        conn.rollback()
        return {"message" : f"등록 실패: {e}"}
    finally:
        conn.close()