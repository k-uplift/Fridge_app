# filepath: Fridge_app/Back/DB_migrations/init_db.py
import sqlite3

# DB 파일 경로 지정
conn = sqlite3.connect('Fridge_app/Back/DB_migrations/refrigerator_manager.db')
c = conn.cursor()

c.execute('PRAGMA foreign_keys = ON;')

# category 테이블 생성
c.execute('''
    CREATE TABLE IF NOT EXISTS CATEGORY (
        category_id INTEGER PRIMARY KEY,
        category_name TEXT NOT NULL UNIQUE,
        is_cook BOOLEAN NOT NULL DEFAULT 0,
        description TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS STORAGE_LOCATION (
        location_id INTEGER PRIMARY KEY,
        location_name VARCHAR(50) NOT NULL,
        description VARCHAR(255)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS LOCATION_SHELF_LIFE (
        category_id INTEGER NOT NULL,
        location_id INTEGER NOT NULL,
        shelf_life_days INTEGER NOT NULL,
          
        PRIMARY KEY (category_id, location_id),
        
        FOREIGN KEY (category_id)
            REFERENCES category(category_id)
            ON DELETE CASCADE,
        FOREIGN KEY (location_id)
            REFERENCES storage_location(location_id)
            ON DELETE CASCADE
    )
''')

conn.commit()
conn.close()