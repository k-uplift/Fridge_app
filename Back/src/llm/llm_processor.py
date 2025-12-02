import ollama
import json
import re

def get_text_from_item(item):
    """
    딕셔너리, 문자열에서 텍스트만 뽑는 함수
    """
    if isinstance(item, dict):
        return item.get('product_name', '') or ''
    return str(item)

def is_garbage_text(item):
    """
    LLM 전송 이전 전처리
    """
    text = get_text_from_item(item).strip()
    
    if not text: return True

    # 숫자가 80% 이상인 경우 (가격, 바코드) 제외
    digit_count = len(re.sub(r'[^0-9]', '', text))
    if len(text) > 0 and (digit_count / len(text)) > 0.6:
        return True

    # 한글/영어가 너무 적은 경우 (특수문자 덩어리) 제외
    char_count = len(re.sub(r'[^가-힣a-zA-Z]', '', text))
    if char_count < 2:
        return True

    # 제거할 키워드
    GARBAGE_KEYWORDS = [
        "합계", "결제", "카드", "면세", "부가세", "포인트", "주소", "TEL", "대표", 
        "할인", "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
        "금액", "승인", "매출", "사업자", "품목"
    ]
    if any(k in text for k in GARBAGE_KEYWORDS):
        return True

    return False

def refine_batch_items(ocr_chunk):
    """
    여러 항목을 한 번에 보내 맥락 제시
    """
    
    input_lines = []
    for i, item in enumerate(ocr_chunk):
        text = get_text_from_item(item)
        input_lines.append(f"{i+1}. {text}")
    
    input_text = "\n".join(input_lines)

    system_prompt = """
    너는 영수증 OCR 데이터를 정제하여 완벽한 '식재료 명단'을 만드는 AI다.
    입력된 텍스트 리스트를 분석하여, 불필요한 수식어를 제거하고 표준화된 식재료명으로 변환하여 JSON 리스트로 반환하라.

    [절대 규칙]
    1. **노이즈 및 비식재료 삭제 (Strict Filtering):**
       - '봉투', '쇼핑백', '종량제', '재사용', '비닐', '얼음컵' 등은 절대 식재료가 아니므로 결과에서 제외하라.
       - 가격 정보(숫자만 있는 줄), 바코드, 점포명 등은 무시하라.
    
    2. **강력한 오타 및 동의어 교정 (Correction Dictionary):** 모양이 비슷한 단어들은 모두 표준 단어로 교정하라.
       - "현통", "한돔", "한동" -> "한돈" (돼지고기)
       - "심겹실", "심겹", "삽겹" -> "삼겹살"
       - "부어스트", "비엔나" -> "소시지"
    
    3. **수식어 제거 (Clean Name):**
       - 조리 용도: '구이용', '찌개용', '국거리', '볶음용', '수육용' -> **삭제**
       - 상태/포장: '암돼지', '수입', '냉동', '냉장', '근사각', '슬라이스', '통', '4가지맛' -> **삭제**
       - 단순 브랜드명은 유지하되, 제품명을 가리면 안 됨. (예: "CJ 햇반" -> "햇반")
       - 청양고추, 적상추 등의 세부 품종명은 유지.
    
    4. **수량 및 단위 표준화:**
       - 텍스트 내의 용량(g, ml, kg, L)은 추출하여 'unit'에, 숫자는 'quantity'에 할당하고 **상품명에서는 제거**하라.
            - 단, 용량과 수량이 혼재된 경우 가장 그럴듯한 해석을 하라.
       - 단위가 없는 경우 기본값: quantity=1, unit="개"
    
    5. **카테고리 분류:** [채소, 육류, 유제품, 가공식품, 음료수, 기타] 중 하나로 정확히 분류하라.

    [Few-shot 예시 (반드시 참고할 것)]
    입력:
    1. 현통 생복실(구이용)
    2. 심겹실(암돼지)
    3. 종림 오일(재시용봉투)
    4. 근사각 햇반 300g
    5. 콤비부어스트4가지맛 285g

    출력:
    [
        {"product_name": "한돈 생목살", "quantity": 1, "unit": "개", "category": "육류"},
        {"product_name": "삼겹살", "quantity": 1, "unit": "개", "category": "육류"},
        {"product_name": "햇반", "quantity": 300, "unit": "g", "category": "가공식품"},
        {"product_name": "소시지", "quantity": 285, "unit": "g", "category": "가공식품"}
    ]
    (설명: 현통->한돈, 생복실-> 생목살(모양이 비슷함), 심겹실->삼겹살, 봉투->삭제, 근사각->삭제, 부어스트->소시지, 용량 분리)
    """

    try:
        response = ollama.chat(
            model='qwen2.5:7b',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': input_text}
            ],
            options={'temperature': 0.1, 'num_ctx': 4096},
            keep_alive=-1
        )
        
        content = response['message']['content']
        
        # 파싱
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            return []

    except Exception as e:
        print(f"[Batch Error] {e}")
        return []

def refine_ingredients_with_llm(ocr_data_list):
    if not ocr_data_list: return []

    clean_candidates = [item for item in ocr_data_list if not is_garbage_text(item)]
    
    print(f"⚡ 전처리 완료: 원본 {len(ocr_data_list)}개 -> 유효 후보 {len(clean_candidates)}개")
    # 배치 사이즈
    CHUNK_SIZE = 20
    final_results = []
    
    for i in range(0, len(clean_candidates), CHUNK_SIZE):
        chunk = clean_candidates[i:i + CHUNK_SIZE]
        print(f"   >>> 배치 처리 중 ({i+1}~{min(i+CHUNK_SIZE, len(clean_candidates))} 항목)...")
        
        batch_result = refine_batch_items(chunk)
        if batch_result:
            final_results.extend(batch_result)

    return final_results