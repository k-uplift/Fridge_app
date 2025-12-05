# notifier.py (알림 조회)

from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..db.database import get_db_connection
from .labeling import calculate_remaining_days, get_visual_labeling_data

# 유통기한이 임박한 식재료 목록 조회
def get_alert_ingredients(alert_days: int) -> List[Dict[str, Any]]:

    conn = get_db_connection()
    cursor = conn.cursor()

    # 알림 기준일 계산: 오늘 날짜 + alert_days
    alert_date = (datetime.now() + timedelta(days=alert_days)).strftime("%Y-%m-%d")
    today_date = datetime.now().strftime("%Y-%m-%d")

    try:
        #Ingredients 테이블에서 유통기한이 오늘 이후부터 alert_date 이내인 식재료 조회
        cursor.execute("""
            SELECT id, name, expiry_date, quantity, unit, category_id, storage_location_id
            FROM Ingredients
            WHERE status = 'active'
            AND expiry_date BETWEEN ? AND ?
            ORDER BY expiry_date ASC
        """, (today_date, alert_date))

        rows = cursor.fetchall()
        alert_list = []

        for row in rows:
            ingredient = dict(row)

            # 남은 일수 및 라벨링 정보 계산
            remaining_days = calculate_remaining_days(ingredient['expiry_date'])
            labeling_data = get_visual_labeling_data(remaining_days)

            # 기존 데이터에 라벨링 정보 병합
            ingredient.update(labeling_data)

            alert_list.append(ingredient)

        return alert_list



    except Exception as e:
        conn.rollback()
        return {"message" : f"등록 실패: {e}"}
    finally:
        conn.close()