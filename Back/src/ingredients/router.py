# router.py (API 엔드포인트 분리)

from fastapi import APIRouter
from .schemas import IngredientRegister
from .service import calculate_expiry_date, register_ingredient_to_db

# API 객체 생성
# main.py에서 prefix="/ingredients"로 연결
router = APIRouter()

# 식재료 등록 API 엔드포인트
# 최종 경로는 main.py에서 설정한 prefix와 합쳐져 "/ingredients/register"
@router.post("/register")
def register_ingredient(item: IngredientRegister):

    # 1. 유통기한 계산 로직 추출
    calculated_date = calculate_expiry_date(
        category=item.category_tag,
        storage=item.storage_location,
        manual_days=item.manual_days
    )

    # 2. 계산된 유통기한을 포함하여 데이터를 DB에 저장
    result = register_ingredient_to_db(
        name=item.name,
        category=item.category_tag,
        storage=item.storage_location,
        quantity=item.quantity,
        unit=item.unit,
        expiry_date=calculated_date
    )

    return result
