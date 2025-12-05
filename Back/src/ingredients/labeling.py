# labeling.py (시작적 라벨링)

from datetime import datetime, timedelta
from typing import Dict, Any

# 유통기한 만료 날짜를 기준으로 오늘까지 남은 일수 계산
def calculate_remaining_days(expiry_date_str: str) -> int:
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except ValueError:
        return 0

    today = datetime.now().date()
    remaining_delta = expiry_date - today

    return remaining_delta.days

# 남은 일수에 따라 라벨링 정보 반환(색상 기준)
def get_visual_labeling_data(remaining_days: int) -> Dict[str, Any]:

    if remaining_days < 0:
        label_text = f"{abs(remaining_days)}일 지남"
        label_color = 'red'
    elif remaining_days <= 3:
        label_text = f"{remaining_days}일 남음"
        label_color = 'orange'
    elif remaining_days <= 7:
        label_text = f"{remaining_days}일 남음"
        label_color = 'yellow'
    else:
        label_text = f"{remaining_days}일 남음"
        label_color = 'green'

    return {
        "remaining_days": remaining_days,
        "label_text": label_text,
        "label_color": label_color
    }

