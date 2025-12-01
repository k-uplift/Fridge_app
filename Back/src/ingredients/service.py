#service.py (핵심 비즈니스 로직 - 유통기한 계산)
# database.py를 사용하여 DB에 접근하고, 유통기한을 자동 계산 및 DB 등록

from datetime import datetime, timedelta
from ..db.database import get_db_connection
from typing import Optional, Any, Dict

# 분류 태그 및 보관 위치를 기반으로 유통기한 만료 날짜를 계산
# manual_days : 사용자가 직접 유통기한을 지정하면 그 값을 사용(옵션)
def calculate_expiry_date(category: str, storage: str, manual_days: Optional[int] = None) -> str:
    
    default_days: int

    # 1) 만약 사용자가 직접 일수를 입력하면 그 값을 우선 사용
    if manual_days is not None and manual_days >= 0:
        default_days = manual_days
    else:
        # 2) DB에서 카테고리 + 보관위치에 해당하는 default_days를 조회
        conn = get_db_connection()
        cursor = conn.cursor()

        # Expiration_Mapping 테이블에서 표준 일수 조회
        cursor.execute("""
                SELECT default_days FROM Expiration_Mapping
                WHERE category_tag = ? AND storage_location = ?
            """, (category, storage))
        
        result: Any = cursor.fetchone() # 결과는 한 행 (default_days 값)
        conn.close()

        if result:
            # row_factory가 sqlite3.Row라면 컬럼명으로 접근
            default_days = result['default_days']
        else:
            #매핑 데이터가 없는 경우, 임시로 기본값(3일)을 설정하거나 오류를 반환
            default_days = 3
            print(f"경고: {category}, {storage}에 대한 매칭 데이터가 없습니다. 3일 기본값 적용")

        # 3) 유통기한 만료 날짜 계산
        today = datetime.now()
        expiry_date = today + timedelta(days=default_days)

        return expiry_date.strftime("%Y-%m-%d")

# 계산된 유통기한 및 식재료 정보를 DB의 Ingredients 테이블에 최종 저장   
def register_ingredient_to_db(
        name: str, 
        category: str, 
        storage: str, 
        quantity: float, 
        unit: str, 
        expiry_date: str
    ) -> Dict[str, Any]:

    conn = get_db_connection()
    cursor = conn.cursor()

    # 등록 날짜 : 지금 시점의 날짜
    registration_date = datetime.now().strftime("%Y-%m-%d") 

    try:
        #유통기한 자동 설정 과정을 거친 최종 데이터 주입
        cursor.execute("""
            INSERT INTO Ingredients
            (name, category_tag, storage_location, quantity, unit, expiry_date, registration_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, category, storage, quantity, unit, expiry_date, registration_date))

        conn.commit()

        return {
            "message": "식재료 등록 완료",
            "id": cursor.lastrowid,
            "expiry_date": expiry_date #계산된 유통기한 날짜를 응답에 포함
            }
    except Exception as e:
        # DB 저장 중 오류 발생 시 롤백 (안전장치)
        conn.rollback()
        return {"message" : f"등록 실패: {e}"}
    finally:
        conn.close()