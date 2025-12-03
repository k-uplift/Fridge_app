# test_service.py

import unittest
from datetime import datetime, timedelta
from src.ingredients.service import calculate_expiry_date, calculate_remaining_days, get_visual_labeling_data, register_ingredient_to_db
from src.db.database import get_db_connection, ensure_value_exists

class TestService(unittest.TestCase):

    def setUp(self):
        """테스트용 DB 초기화 및 샘플 데이터 준비"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

        # 테스트용 카테고리/저장위치 확보
        self.category = "테스트카테고리"
        self.storage = "테스트저장위치"

        self.category_id = ensure_value_exists(self.cursor, "Categories", self.category)
        self.storage_id = ensure_value_exists(self.cursor, "Storage_Locations", self.storage)
        self.conn.commit()

    def tearDown(self):
        """테스트 후 DB 커넥션 종료"""
        self.conn.close()

    def test_calculate_expiry_date_manual(self):
        """수동 유통기한 지정"""
        expiry = calculate_expiry_date(self.category, self.storage, manual_days=10)
        expected = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        self.assertEqual(expiry, expected)

    def test_calculate_expiry_date_auto(self):
        """자동 유통기한 계산"""
        # Expiration_Mapping에 임시 기본값 추가
        self.cursor.execute("""
            INSERT OR REPLACE INTO Expiration_Mapping (category_id, storage_location_id, default_days)
            VALUES (?, ?, ?)
        """, (self.category_id, self.storage_id, 7))
        self.conn.commit()

        expiry = calculate_expiry_date(self.category, self.storage)
        expected = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        self.assertEqual(expiry, expected)

    def test_calculate_remaining_days_and_label(self):
        """남은 일수 계산 및 라벨링"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        remaining = calculate_remaining_days(today_str)
        self.assertEqual(remaining, 0)

        label = get_visual_labeling_data(remaining)
        self.assertEqual(label['label_color'], 'orange')  # 0~3일은 orange

    def test_register_ingredient(self):
        """Ingredients 테이블에 등록"""
        expiry = calculate_expiry_date(self.category, self.storage, manual_days=5)
        result = register_ingredient_to_db(
            name="테스트식재료",
            category_id=self.category_id,
            storage_location_id=self.storage_id,
            quantity=1.0,
            unit="개",
            expiry_date=expiry
        )
        self.assertIn("id", result)
        self.assertEqual(result["expiry_date"], expiry)

if __name__ == "__main__":
    unittest.main()
