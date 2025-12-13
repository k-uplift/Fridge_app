import sqlite3
from typing import Any, Dict, Optional, List
from datetime import datetime

# 조리된 음식 등록 
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
            "message": "조리 음식 등록 완료",
            "id": cursor.lastrowid,
            "expiry_date": expiry_date
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"message" : f"등록 실패: {e}"}
    

# 등록된 모든 조리된 음식을 조회
def get_all_cooked_dishes(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """상태가 'ACTIVE'인 모든 조리된 음식을 조회합니다."""
    cursor = conn.cursor()
    try:
        # 유통기한 임박 순으로 정렬하는 것이 일반적입니다.
        cursor.execute("""
            SELECT * FROM Cooked_Dishes 
            WHERE status = 'ACTIVE' 
            ORDER BY expiry_date ASC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"조리 음식 조회 DB 오류: {e}")
        return []
    

# 조리된 음식 수정
def update_cooked_dish_db(
    conn: sqlite3.Connection, 
    dish_id: int, 
    new_data: Dict[str, Any]
) -> Dict[str, Any]:
    """조리된 음식의 이름, 유통기한, 메모 등을 수정합니다."""
    
    # 쿼리 동적 생성
    set_clauses = []
    params = []
    
    # 'id', 'status', 'registration_date'는 수정하지 않습니다.
    for key, value in new_data.items():
        if key not in ['id', 'status', 'registration_date', 'type'] and value is not None:
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
    

# 조리된 음식 삭제
def delete_cooked_dish_db(conn: sqlite3.Connection, dish_id: int) -> Dict[str, Any]:
    """조리된 음식을 DB에서 물리적으로 삭제합니다."""
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