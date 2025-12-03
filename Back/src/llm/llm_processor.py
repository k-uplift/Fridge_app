import ollama
import json
import re

def get_text_from_item(item):
    """
    입력 아이템에서 텍스트와 신뢰도를 추출하여 포맷팅된 문자열 반환
    """
    if isinstance(item, dict):
        text = str(item.get('text', '') or item.get('product_name', '') or '').strip()
        conf = float(item.get('confidence', 0.0))
        # 신뢰도가 낮으면 (0.6 미만) [Low Conf] 마커를 붙여 LLM에게 힌트 제공
        marker = " [Low Conf]" if conf > 0 and conf < 0.6 else ""
        return text, marker
    return str(item).strip(), ""

def is_garbage_text(item):
    text, _ = get_text_from_item(item)
    if not text: return True
    
    
    # 2. 너무 짧은 비한글 텍스트 제외
    if len(text) < 2 and not re.search(r'[가-힣]', text): return True

    # 3. 비식재료 키워드
    GARBAGE_KEYWORDS = [
        "합계", "결제", "카드", "면세", "부가세", "포인트", "주소", "TEL", "대표", 
        "할인", "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
        "금액", "승인", "매출", "사업자", "품목", "봉투", "쇼핑백", "종량제", "비닐", "Trash", "단가", "수량"
    ]
    if any(k in text for k in GARBAGE_KEYWORDS): return True

    return False

def refine_batch_items(ocr_chunk):
    # 1. 입력 텍스트 구성
    input_lines = []
    for i, item in enumerate(ocr_chunk):
        text, marker = get_text_from_item(item)
        input_lines.append(f"{i+1}. {text}{marker}")
    
    input_text = "\n".join(input_lines)

    # 2. 시스템 프롬프트 (단일화 및 명확화)
    system_prompt = """
    너는 영수증 OCR 데이터를 정제하여 '식재료 및 식음료 목록'을 JSON으로 추출하는 AI다.
    입력된 텍스트 리스트를 분석하여 아래 규칙에 따라 정제하라.

    [핵심 규칙]
    1. **오타 교정 (매우 중요):**
       - '[Low Conf]' 표시가 있거나 오타가 의심되면 문맥을 통해 '가장 유력한 식재료명'으로 수정하라.
       - 예: '임상추' -> '양상추', 'Koukakls' -> '그릭요거트', 'Ikg' -> '1kg'
    2. **식재료 여부 판단:**
       - 식재료/식음료가 아닌 항목은 결과에서 제외하라.
    3. **명칭 분해 및 카테고리화:**
       - 상품명에서 '수량'과 '단위'를 분리하라.
       - 수량이 명시되지 않았으면 기본값으로 1을 설정하라.
       - 단위는 g, kg, ml, L, 개 등으로 표준화하라. 단위가 없으면 '개'로 설정하라.
       - 각 식재료에 대해 적절한 'category'를 지정하라 (예: 채소, 과일, 육류, 유제품, 음료 등).
    4. **정제:**
       - 브랜드(농협, CJ)와 수식어(구이용, 맛있는)는 제거하고 핵심 명칭만 남겨라.
       - '코카 콜라', '코카 콜라 제로' 등은 각각 별개의 상품으로 인식하라.

    [출력 형식]
    - 반드시 아래 JSON 구조의 리스트만 반환하라. (설명 금지)
    - [{"product_name": "이름", "quantity": 1, "unit": "단위", "category": "카테고리"}]
    """

    try:
        response = ollama.chat(
            model='midm2', # 사용 중인 모델명
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': input_text}
            ],
            options={'temperature': 0.1, 'num_ctx': 4096}, # 컨텍스트 넉넉하게
            keep_alive=-1
        )
        
        content = response['message']['content']
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        # ---------------------------------------------------------
        # ★ [좀비 파싱] JSON이 깨져도 살려내는 로직
        # ---------------------------------------------------------
        restored_items = []
        
        # 1. 정규식으로 개별 객체({...}) 추출 시도
        # (리스트 전체 파싱보다 훨씬 안전함)
        item_pattern = r'\{\s*"product_name".*?\}'
        raw_items = re.findall(item_pattern, content, re.DOTALL)
        
        for raw_item in raw_items:
            try:
                item_obj = json.loads(raw_item)
                # 필수 필드 확인
                if item_obj.get("product_name"):
                    restored_items.append(item_obj)
            except:
                pass
        
        return restored_items

    except Exception as e:
        print(f"[Batch Error] {e}")
        return []

def refine_ingredients_with_llm(ocr_data_list):
    if not ocr_data_list: return []

    clean_candidates = [item for item in ocr_data_list if not is_garbage_text(item)]
    print(f"⚡ LLM 정제 시작: {len(clean_candidates)}개 항목 처리 중...")

    # 한 번에 보내는 양을 30개로 늘려서 문맥 파악 강화
    CHUNK_SIZE = 30
    final_items = []
    
    for i in range(0, len(clean_candidates), CHUNK_SIZE):
        chunk = clean_candidates[i:i + CHUNK_SIZE]
        items = refine_batch_items(chunk)
        if items:
            final_items.extend(items)
            
    return final_items