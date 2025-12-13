import sqlite3
from typing import Any, Dict, Optional
from datetime import datetime

# 조리된 음식 등록 로직
def register_cooked_dish_to_db(
        conn: sqlite3.Connection,
        name: str,
        dish_type: str,
        expiry_date: str,
        memo: Optional[str]
    ) -> Dict[str, Any]:

    cursor = conn.cursor()
    registration_date = datetime.now().strftime("%Y-%m-%d")

    try:
        cursor.execute("""
            INSERT INTO Cooked_Dishes
            (name, type, registration_date, expiry_date, memo, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, dish_type, registration_date, expiry_date, memo, 'ACTIVE'))

        conn.commit()

        return {
            "message": "조리된 음식 등록 완료",
            "id": cursor.lastrowid,
            "expiry_date": expiry_date
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"message": f"조리된 음식 등록 실패: {e}"}
    except Exception as e:
        conn.rollback()
        return {"message": f"조리된 음식 등록 실패: {e}"}
    

# 등록된 모든 조리된 음식을 조회
def get_all_cooked_dishes(conn: sqlite3.Connection) -> list[sqlite3.Row]:

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, name, type, expiry_date, registration_date, memo, status 
            FROM Cooked_Dishes 
            WHERE status = 'ACTIVE' 
            ORDER BY expiry_date ASC
            """
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"조리 음식 조회 DB 오류: {e}")
        return []
    
# 특정 음식 ID로 조회
def get_cooked_dish_by_id(conn: sqlite3.Connection, dish_id: int) -> Optional[sqlite3.Row]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, type, expiry_date, registration_date, memo, status 
        FROM Cooked_Dishes 
        WHERE id = ?
    """, (dish_id,))
    return cursor.fetchone()

# 등록된 조리된 음식을 수정
def update_cooked_dish_db(
    conn: sqlite3.Connection, 
    dish_id: int, 
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    
    set_clauses = []
    params = []
    
    for key, value in update_data.items():
        if key not in ['id', 'registration_date'] and value is not None:
            set_clauses.append(f"{key} = ?")
            params.append(value)
    
    if not set_clauses:
        return {"success": False, "message": "수정할 데이터가 없습니다."}

    query = f"UPDATE Cooked_Dishes SET {', '.join(set_clauses)} WHERE id = ?"
    params.append(dish_id)

    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()

        if cursor.rowcount == 0:
            return {"success": False, "message": f"ID {dish_id}를 가진 음식을 찾을 수 없습니다."}
        
        return {"success": True, "message": f"ID {dish_id}의 음식이 성공적으로 수정되었습니다."}
        
    except sqlite3.Error as e:
        conn.rollback()
        return {"success": False, "message": f"DB 오류: {e}"}
    
# 조리된 음식을 삭제
def delete_cooked_dish_db(conn: sqlite3.Connection, dish_id: int) -> Dict[str, Any]:
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Cooked_Dishes WHERE id = ?", (dish_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return {"success": False, "message": f"ID {dish_id}를 가진 음식을 찾을 수 없습니다."}

        return {"success": True, "message": f"ID {dish_id}의 음식이 성공적으로 삭제되었습니다."}
    
    except sqlite3.Error as e:
        conn.rollback()
        return {"success": False, "message": f"DB 오류: {e}"}

