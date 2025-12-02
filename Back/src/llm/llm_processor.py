import ollama
import json
import re

def get_text_from_item(item):
    if isinstance(item, dict):
        return item.get('product_name', '') or ''
    return str(item)

def is_garbage_text(item):
    """
    [1차 필터] 명확한 쓰레기 데이터만 제거 (민감도 낮춤)
    """
    text = get_text_from_item(item).strip()
    if not text: return True

    # 1. 숫자로만 구성된 경우 제외 (가격 데이터일 확률 높음)
    # (주의: '1kg' 같은 건 살려야 하므로 순수 숫자만 거름)
    if re.fullmatch(r'[0-9,]+', text): 
        return True
    
    # 2. 텍스트 길이가 너무 짧은 특수문자/영어 덩어리 제외
    # 한글이 없어도 'Oreo' 같은 과자가 있을 수 있으므로 조건 완화
    if len(text) < 2:
        return True

    # 3. 비식재료 키워드 (확실한 것만 제거)
    GARBAGE_KEYWORDS = [
        "합계", "결제", "카드", "면세", "부가세", "포인트", "주소", "TEL", "대표", 
        "할인", "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
        "금액", "승인", "매출", "사업자", "품목", "봉투", "쇼핑백", "종량제", "비닐", "Trash"
    ]
    if any(k in text for k in GARBAGE_KEYWORDS):
        return True

    return False

def refine_batch_items(ocr_chunk):
    input_lines = []
    for i, item in enumerate(ocr_chunk):
        text = get_text_from_item(item)
        input_lines.append(f"{i+1}. {text}")
    
    input_text = "\n".join(input_lines)

    system_prompt = """
    너는 OCR 과정에서 손상된 영수증 데이터를 식재료 목록으로 복원시키는 역할을 맡았다.
    입력된 텍스트는 **줄바꿈(\n)**으로 구분된 목록이다. 모든 줄(Line)에 대해 빠짐없이 아래 과정을 수행하라
    
    [입력 데이터의 특성]
    - 영수증 특성 상, 단어의 앞 뒤에 무작위 특수문자, 영문 오인식, 숫자가 섞일 수 있다.
    - 브랜드명, 제조사명이 포함될 수 있다.
    - 단위 및 수량이 포함될 수 있다.
    - 비식재료, 가격, 바코드, 봉투, 얼음컵 등도 포함될 수 있다.
    - 일부 단어는 심각하게 훼손되어 있어 문맥상 유추가 필요하다.

    [제약 사항]
    1. 반드시 JSON 형식으로만 응답하라. (설명 금지)
    2. JSON 키: "items" (리스트), "debug_log" (리스트)
    3. unit 허용값: '개', 'kg', 'g', 'ml', 'L'. (기본값 '개')
    4. category 허용값: '과일', '채소', '육류', '생선', '유제품', '음료', '가공식품', '기타'.
    5. quantity는 반드시 숫자형(Integer/Float). 기본값 1.

    [작업 지시 - 단계별 수행]
    
    1. **노이즈 필터링:**
       - 한글 단어 사이나 앞뒤에 섞인 무의미한 특수문자, 영문, 숫자를 제거하라.
       - 단, 수량과 단위를 나타내는 숫자/문자는 유지한다.
       - 명확한 브랜드 명 역시 일단은 유지한다.
    2. **음운 유사성 기반 복원:**
       - 1단계에서 정제된 한글이 표준 국어사전에 존재하지 않는 단어라면, **음운 유사성**이 높은 가장 근접한 표준 한글 단어로 교정하라.
       - 텍스트의 모양보다 **발음**과 **문맥상 의미**를 우선적으로 고려한다.
       - 예) '임상추' -> '양상추', '그리요거트' -> '그릭요거트', '계찮' -> '케첩', '념다주믈력' -> '양념닭주물럭'
    3. **안전 장치:**
       - 이미 완벽한 단어(표준 국어사전에 존재하는 단어)라면, 2단계를 건너뛰고 그대로 유지한다.
    4. **카테고리 분류:**
       - 교정된 단어를 기반으로, 해당 식재료의 적절한 카테고리를 지정하라.
    5. **수량 및 단위 추출:**
       - 텍스트에 명시된 수량과 단위를 추출하라.
       - 수량이 명시되지 않았다면 기본값 1, 단위가 명시되지 않았다면 기본값 '개'로 설정하라.

    [출력 예시]
    {
        "items": [
            {"product_name": "그릭요거트", "quantity": 1, "unit": "개", "category": "유제품"},
            {"product_name": "양상추", "quantity": 2, "unit": "봉지", "category": "채소"},
            {"product_name": "치즈", "quantity": 1, "unit": "개", "category": "유제품"}
        ],
        "debug_log": [
            "정제: 'Koukakls 그리요거트' -> '그릭요거트' (브랜드 삭제 및 오타 수정)",
            "교정: '임상추' -> '양상추' (유사 식재료명으로 변경)",
            "정제: '하인즈 유기농 계찮' -> '케첩' (브랜드 삭제 및 오타 수정)"
        ]
    }
    """

    try:
        response = ollama.chat(
            model='exaone3.5:7.8b', # 또는 사용 중인 모델
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': input_text}
            ],
            options={'temperature': 0.1, 'num_ctx': 2048},
            keep_alive=-1
        )
        
        content = response['message']['content']
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        # ---------------------------------------------------------
        # ★ [강화된 파싱 로직] JSON이 깨져도 살려내는 좀비 파싱
        # ---------------------------------------------------------
        try:
            # 1. 정상적인 JSON 파싱 시도
            parsed_result = json.loads(content)
            return parsed_result.get("items", []), parsed_result.get("debug_log", [])
            
        except json.JSONDecodeError:
            print("⚠️ JSON 파싱 실패 -> 좀비 파싱 시도...")
            
            # 2. 정규식으로 "items": [ ... ] 안의 객체들만 강제 추출
            # {"product_name": ... } 패턴을 모두 찾음
            item_pattern = r'\{\s*"product_name".*?\}'
            raw_items = re.findall(item_pattern, content, re.DOTALL)
            
            restored_items = []
            for raw_item in raw_items:
                try:
                    # 개별 객체 단위로 파싱 (콤마가 없어도 이건 성공함)
                    item_obj = json.loads(raw_item)
                    restored_items.append(item_obj)
                except:
                    pass
            
            # 로그도 추출 시도
            log_pattern = r'"debug_log":\s*\[(.*?)\]'
            log_match = re.search(log_pattern, content, re.DOTALL)
            restored_logs = []
            if log_match:
                # 대충 문자열만 뽑음
                restored_logs = re.findall(r'"(.*?)"', log_match.group(1))

            return restored_items, restored_logs

    except Exception as e:
        print(f"[Batch Error] {e}")
        return [], []

def refine_ingredients_with_llm(ocr_data_list):
    if not ocr_data_list: return []

    clean_candidates = [item for item in ocr_data_list if not is_garbage_text(item)]
    print(f"⚡ LLM 정제 시작: {len(clean_candidates)}개 항목 처리 중...")

    CHUNK_SIZE = 20
    final_items = []
    
    for i in range(0, len(clean_candidates), CHUNK_SIZE):
        chunk = clean_candidates[i:i + CHUNK_SIZE]
        
        # items와 logs를 분리해서 받음
        items, logs = refine_batch_items(chunk)
        
        if items:
            final_items.extend(items)
        
        # 로그 출력
        if logs:
            for log in logs:
                print(f"  [Log] {log}")

    return final_items