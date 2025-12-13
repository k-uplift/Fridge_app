# crud.py (DB 저장, 조회, 수정)

from datetime import datetime
import sqlite3
from typing import Any, Dict
from ..db.database import get_db_connection

# TEXT로 ID 조회
def get_id_by_name(conn: sqlite3.Connection, table_name: str, name: str) -> int:
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table_name} WHERE name = ?", (name, ))
    result = cursor.fetchone()
    if result:
        return result['id']

    raise ValueError(f"ID를 찾을 수 없습니다: {table_name} - {name}")

# DB 저장 로직
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


# 식재료 상태 업데이트
def update_ingredient_status(conn: sqlite3.Connection, ingredient_id: int, new_status: str) -> Dict[str, Any]:
    valid_statuses = ['ACTIVE', 'USED', 'DISCARDED']
    new_status = new_status.lower()

    if new_status not in [s.lower() for s in valid_statuses]:
        return{"success": False, "message": f"잘못된 상태 값입니다: {new_status}"}
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE Ingredients SET satus = ? WHERE id = ? 
            """,
            (new_status, ingredient_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return {"sucess": False, "message": f"ID {ingredient_id}를 가진 식재료를 찾을 수 없습니다."}
        
        return {"success": True, "message": f"식재료 ID {ingredient_id}의 상태가 {new_status.upper()}로 변경되었습니다."}

    except sqlite3.Error as e:
        return {"success": False, "message": f"상태 업데이트 DB 오류: {e}"}
    

# 히스토리 목록 조회(USED or DISCARDED 상태의 식재료만 조회)
def get_history_ingredients(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM Ingredients WHERE status IN ('used', 'discarded')
            ORDER BY id DESC            
            """
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"히스토리 조회 DB 오류: {e}")
        return []