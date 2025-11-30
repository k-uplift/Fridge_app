#databse.py (데이터베이스 연결 및 초기화 관리)

import sqlite3
from typing import List, Tuple

#DB 파일 경로 설정
DATABASE_FILE = "fridge_app.db"

# 1. Ingredients 테이블 스키마 (식재료 주 데이터)
INGREDIENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS Ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 식별자 (자동 증가)
    name TEXT NOT NULL,                   -- 음식 또는 식재료 이름 (예: 우유, 감자)
    quantity REAL NOT NULL,               -- 수량 값 (예: 1, 300)
    unit TEXT NOT NULL,                   -- 수량 단위 (예: 개, g, L)
    category_tag TEXT NOT NULL,           -- 분류 태그 (예: 유제품, 채소)
    storage_location TEXT NOT NULL,       -- 보관 위치 (예: 냉장, 상온)
    expiry_date TEXT NOT NULL,            -- 유통기한 만료 날짜 (YYYY-MM-DD)
    registration_date TEXT NOT NULL       -- 등록 날짜 (YYYY-MM-DD, 계산 기준)
);
"""

# 2. Expriration_Mapping 테이블 스키마 (유통기한 자동 설정 기준)
EXPIRATION_MAPPING_SCHEMA = """
CREATE TABLE IF NOT EXISTS Expiration_Mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_tag TEXT NOT NULL,
    storage_location TEXT NOT NULL,     
    default_days INTEGER NOT NULL,          -- 유통기한 기본 일수
    UNIQUE(category_tag, storage_location)  -- 같은 태그와 위치 조합은 하나만 존재하도록 보장
);
"""

# DB 연결 객체를 만들어 반환
def get_db_connection() -> sqlite3.Connection:
    
    # DB 파일예 연결, 파일이 없으면 자동 생성됨
    conn = sqlite3.connect(DATABASE_FILE)
    # 쿼리 결과를 딕셔너리처럼 컬럼 이름으로 접근할 수 있도록 설정 (예: row["name"])
    conn.row_factory = sqlite3.Row
    return conn

# DB 테이블을 생성하고, 매핑 초기 데이터를 주입하여 DB를 준비
def initialize_database():

    conn = get_db_connection() 
    cursor = conn.cursor() 

    cursor.execute(INGREDIENTS_SCHEMA) #Ingredients 테이블 생성
    cursor.execute(EXPIRATION_MAPPING_SCHEMA) #Expiration_Mapping 테이블 생성


    # Expiration_Mapping에 기본 데이터 넣기(비어 있을 때만) - 초기 매핑 데이터
    initial_data: List[Tuple[str, str, int]] = [
        ('유제품', '냉장', 7),
        ('육류', '냉동', 90),
        ('채소', '상온', 3),
        ('채소', '냉장', 7),
        ('과일', '상온', 5),
        ('냉동식품', '냉동', 180),
    ]

    cursor.execute("SELECT COUNT(*) FROM Expiration_Mapping")

    # fetchone() → 첫 번째(유일한) 결과 행을 가져옴
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO Expiration_Mapping (category_tag, storage_location, default_days)
            VALUES (?, ?, ?)              
        """, initial_data)
        print("초기 유통기한 매핑 데이터 삽입 완료.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    print(f"'{DATABASE_FILE}' 데이터베이스 파일이 준비되었습니다.")
