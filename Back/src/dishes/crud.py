import sqlite3
from typing import Any, Dict
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
            (name, type, registration_date, expiry_date, memo)
            VALUES (?, ?, ?, ?, ?)
        """, (name, dish_type, registration_date, expiry_date, memo))

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