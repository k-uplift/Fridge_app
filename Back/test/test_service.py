# tests/test_ingredients_api.py

import pytest
from fastapi.testclient import TestClient
from Fridge_app.Back.src.main import app

# TestClient 인스턴스 생성 (FastAPI 앱을 인수로 전달)
client = TestClient(app)

# ---------------------------------------------------
# Helper: 테스트 DB 사용 (선택 사항이나 권장)
# NOTE: 현재 코드는 실제 fridge_app.db를 사용하므로,
# 테스트 전에 DB를 삭제하고 테스트 후에 복원하는 작업이 필요합니다.
# ---------------------------------------------------

def test_01_register_automatic_expiry_success():
    """B1, B2: DB 매핑에 따른 유통기한 자동 설정 테스트 ('유제품'/'냉장' -> 7일)"""

    # 1. 오늘 날짜를 기준으로 예상 만료 날짜 계산
    from datetime import datetime, timedelta
    expected_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    # 2. API에 데이터 전송 (manual_days = None)
    response = client.post("/ingredients/register", json={
        "name": "서울우유",
        "category_tag": "유제품",
        "storage_location": "냉장",
        "quantity": 1.0,
        "unit": "팩",
        "manual_days": None
    })

    # 3. 응답 검증
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "식재료 등록 완료"
    # 계산된 expiry_date가 예상 날짜와 일치하는지 확인
    assert data["expiry_date"] == expected_date

def test_02_register_manual_expiry_success():
    """B3: 유통기한 수동 지정 테스트 (DB 매핑 값 무시)"""

    manual_days = 50 # 50일로 수동 지정
    expected_date = (datetime.now() + timedelta(days=manual_days)).strftime("%Y-%m-%d")

    # 육류/냉동은 DB에 90일로 매핑되어 있지만, 50일이 적용되어야 합니다.
    response = client.post("/ingredients/register", json={
        "name": "한우 안심",
        "category_tag": "육류",
        "storage_location": "냉동",
        "quantity": 300.0,
        "unit": "g",
        "manual_days": manual_days
    })

    assert response.status_code == 200
    data = response.json()
    assert data["expiry_date"] == expected_date

def test_03_register_invalid_category_failure():
    """정규화된 DB에 존재하지 않는 카테고리 입력 시 실패 테스트"""

    # '해산물'은 Categories 테이블에 없습니다.
    response = client.post("/ingredients/register", json={
        "name": "오징어",
        "category_tag": "해산물",
        "storage_location": "냉장",
        "quantity": 1.0,
        "unit": "개",
        "manual_days": None
    })

    # service.py의 ValueError를 router.py가 400 Bad Request로 반환해야 함
    assert response.status_code == 400
    assert "ID를 찾을 수 없습니다" in response.json().get("detail", "")