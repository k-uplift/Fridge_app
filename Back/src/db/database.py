# database.py (데이터베이스 연결 및 초기화 관리)

import os
import sqlite3
from typing import List, Tuple

# DB 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, "fridge_app.db")

# 1. Categories 테이블 (분류 태그)
CATEGORIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS Categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

# 2. Storage_Locations 테이블 (보관 위치)
STORAGE_LOCATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS Storage_Locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

# 3. Ingredients 테이블 (식재료 주 데이터)
INGREDIENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS Ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 고유 식별자
    name TEXT NOT NULL,                    -- 음식 또는 식재료 이름
    quantity REAL NOT NULL,                -- 수량 값
    unit TEXT NOT NULL,                    -- 수량 단위
    category_id INTEGER NOT NULL,          -- 분류 태그
    storage_location_id INTEGER NOT NULL,  -- 보관 위치
    expiry_date TEXT NOT NULL,             -- 유통기한 만료 날짜 (TEXT로 저장)
    registration_date TEXT NOT NULL,       -- 등록 날짜 (TEXT로 저장)
    status TEXT NOT NULL DEFAULT 'active', -- 상태 추적
    is_cooked BOOLEAN NOT NULL DEFAULT 0,  -- 0: 식재료, 1: 조리된 음식
    memo TEXT,                             -- 사용자 메모
    source_image_id INTEGER,               -- 영수증 이미지

    FOREIGN KEY (category_id) REFERENCES Categories(id),
    FOREIGN KEY (storage_location_id) REFERENCES Storage_Locations(id)
);
"""

# 4. Expiration_Mapping 테이블 (유통기한 자동 설정 기준)
EXPIRATION_MAPPING_SCHEMA = """
CREATE TABLE IF NOT EXISTS Expiration_Mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    storage_location_id INTEGER NOT NULL,
    default_days INTEGER NOT NULL,             -- 유통기한 기본 일수

    UNIQUE(category_id, storage_location_id),  -- 같은 태그와 위치 조합은 하나만 존재하도록 보장
    FOREIGN KEY (category_id) REFERENCES Categories(id),
    FOREIGN KEY (storage_location_id) REFERENCES Storage_Locations(id)
);
"""

# DB 연결
def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ID 조회
def get_id_by_name(cursor: sqlite3.Cursor, table_name: str, name: str) -> int:
    cursor.execute(f"SELECT id FROM {table_name} WHERE name = ?", (name,))
    result = cursor.fetchone()
    if result:
        return result['id']
    raise ValueError(f"ID를 찾을 수 없습니다: {table_name} - {name}")

# 값이 없으면 자동 추가 (이 함수는 현재 initialize_database에서는 사용되지 않지만 유틸리티로 남겨둠)
def ensure_value_exists(cursor, table, name):
    cursor.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row['id']

    cursor.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
    return cursor.lastrowid

# 초기 DB 세팅
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 테이블 생성
    cursor.execute(CATEGORIES_SCHEMA)
    cursor.execute(STORAGE_LOCATIONS_SCHEMA)
    cursor.execute(INGREDIENTS_SCHEMA)
    cursor.execute(EXPIRATION_MAPPING_SCHEMA)

    # 기본 카테고리 / 저장 위치
    initial_categories = [
        '유제품', '채소', '과일', '빵류', '떡류', '육류', '어묵',
        '두부', '묵류', '과일·채소류음료', '도시락', '김밥', '샌드위치', '햄버거',
        '건면', '비건조면류', '식용유', '참기름', '들기름', '마가린류', '달걀',
        '냉동식품', '조미료', '기타'
    ]

    initial_locations = ['냉장', '냉동', '상온', '진공-냉장']

    # Categories 초기 데이터 삽입
    cursor.execute("SELECT COUNT(*) FROM Categories")
    if cursor.fetchone()[0] == 0:
        category_data = [(name,) for name in initial_categories]
        cursor.executemany("INSERT INTO Categories (name) VALUES (?)", category_data)
        print("초기 분류(Categories) 데이터 삽입 완료.")

    # Storage_Locations 초기 데이터 삽입
    cursor.execute("SELECT COUNT(*) FROM Storage_Locations")
    if cursor.fetchone()[0] == 0:
        location_data = [(name,) for name in initial_locations]
        cursor.executemany("INSERT INTO Storage_Locations (name) VALUES (?)", location_data)
        print("초기 보관 위치(Storage_Locations) 데이터 삽입 완료.")

    # Expiration_Mapping 초기 데이터 정의 (TEXT 기준)
    text_mapping_data: List[Tuple[str, str, int]] = [
        # 유제품
        ('유제품', '냉장', 7),
        ('유제품', '냉동', 30),

        # 채소
        ('채소', '냉장', 7),
        ('채소', '상온', 3),

        # 과일
        ('과일', '냉장', 5),
        ('과일', '상온', 4),

        # 빵류
        ('빵류', '상온', 5),  # 크림빵, 단팥빵 평균
        ('빵류', '냉장', 4),  # 생크림빵

        # 떡류
        ('떡류', '상온', 1),

        # 육류
        ('육류', '냉장', 5),
        ('육류', '냉동', 90),

        # 어묵
        ('어묵', '냉장', 8),
        ('어묵', '냉동', 20),

        # 두부
        ('두부', '냉장', 3),   # 비포장
        ('두부', '냉동', 15),  # 살균제품

        # 묵류
        ('묵류', '냉장', 3),

        # 과일·채소류음료
        ('과일·채소류음료', '냉장', 3),

        # 즉석섭취, 편의식품류
        ('도시락', '냉장', 1),
        ('김밥', '냉장', 1),
        ('샌드위치', '냉장', 2),
        ('햄버거', '냉장', 3),

        # 면류
        ('건면', '상온', 730),    # 건조제품 2년
        ('비건조면류', '상온', 60), # 비건조 살균제품 2개월

        # 식용유지류
        ('식용유', '상온', 360),
        ('참기름', '상온', 270),
        ('들기름', '상온', 270),

        # 식용유지가공품
        ('마가린류', '냉장', 360),

        # 달걀
        ('달걀', '냉장', 45),

        # 냉동식품
        ('냉동식품', '냉동', 180),

        # 조미료
        ('조미료', '상온', 180),

        # 기타
        ('기타', '상온', 30),
    ]

    # Expiration_Mapping에 ID 기반 데이터 삽입
    cursor.execute("SELECT COUNT(*) FROM Expiration_Mapping")
    if cursor.fetchone()[0] == 0:

         id_mapping_data = []
         for category_name, location_name, days in text_mapping_data:
             try:
                 # 텍스트 이름으로 ID 조회
                 category_id = get_id_by_name(cursor, "Categories", category_name)
                 location_id = get_id_by_name(cursor, "Storage_Locations", location_name)

                 # ID 기반의 최종 데이터 리스트 구성
                 id_mapping_data.append((category_id, location_id, days))
             except ValueError as e:
                 print(f"경고: 매핑 데이터 준비 중 오류 발생 - {e}")
                 continue

         cursor.executemany("""
             INSERT INTO Expiration_Mapping (category_id, storage_location_id, default_days)
             VALUES (?, ?, ?)
         """, id_mapping_data)
         print("초기 유통기한 매핑 데이터 삽입 완료.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    print(f"'{DATABASE_FILE}' 데이터베이스 파일이 준비되었습니다.")