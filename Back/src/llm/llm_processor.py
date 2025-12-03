import ollama
import json
import re

def get_text_from_item(item):
    """
    입력이 딕셔너리든 문자열이든 텍스트만 추출
    """
    if isinstance(item, dict):
        text = str(item.get('text', '') or item.get('product_name', '') or '').strip()
        conf = float(item.get('confidence', 0.0))
        # 신뢰도가 낮으면 (0.6 미만) [Low Conf] 마커를 붙여 LLM에게 힌트 제공
        marker = " [Low Conf]" if conf > 0 and conf < 0.6 else ""
        return text, marker
    return str(item).strip(), ""

def is_garbage_text(item):
    """
    1차 필터링: 명확한 비식재료 및 노이즈 제거
    """
    text, _ = get_text_from_item(item)
    if not text: return True
    
    # 2. 너무 짧은 비한글 텍스트 제외
    if len(text) < 2 and not re.search(r'[가-힣]', text): return True

    # 3. 비식재료 키워드
    GARBAGE_KEYWORDS = [
        "합계", "결제", "카드", "면세", "부가세", "포인트", "주소", "TEL", "대표", 
        "할인", "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
        "금액", "승인", "매출", "사업자", "품목", "봉투", "쇼핑백", "종량제", "비닐", "Trash", "단가", "수량",
        "POINT", "Point", "포인트", "적립", "사용", "소멸", "잔여", "누리", "에누리",
        "PL", "S-OIL", "L.POINT", "CASH", "CARD", "할인", "쿠폰", 
        "미사용", "개월", "문의", "안내", "영수증", "교환", "환불"
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

    # 2. 시스템 프롬프트 (★ 사용자님 버전으로 복구 완료)
    system_prompt = """
    너는 영수증 OCR 데이터를 정제하여 '식재료 및 식음료 목록'을 JSON으로 추출하는 AI다.
    입력된 텍스트 리스트를 분석하여 아래 규칙에 따라 정제하라.

    [핵심 규칙]
    1. **오타 교정 (매우 중요):**
       - 오타가 의심되면 문맥과 단어의 모양, 발음을 통해 '가장 유력한 식음료/식재료명'을 유추하여 수정하라.
       - 예: '임상추' -> '양상추', 'Ikg' -> '1kg'
       - '[Low Conf]' 표시가 있고, 한글 단어가 포함되어 있다면 추론을 통해 오타 교정을 시도하라.
       - 숫자만 있는 줄은 바로 윗줄 상품의 수량으로 합쳐라.
    2. **정제:**
       - 브랜드(농협, CJ)와 수식어(구이용, 맛있는)는 제거하고 핵심 명칭만 남겨라.
         - 단, 브랜드명, 수식어가 식재료명에 필수적인 경우는 예외로 한다.
       - '코카 콜라', '코카 콜라 제로' 등의 상품은 별개의 상품으로 인식하라.
    3. **명칭 분해 및 카테고리화:**
       - 상품명에서 '수량'과 '단위'를 분리하라.
       - 수량이 명시되지 않았으면 기본값으로 1을 설정하라.
       - 단위는 g, kg, ml, L, 개 등으로 표준화하라. 단위가 없으면 '개'로 설정하라.
       - 각 식재료에 대해 적절한 'category'를 지정하라
        - 다음과 같은 'category'만을 사용한다. (채소, 과일, 육류, 유제품, 음료, 가공식품, 조리식품).
    4. **식재료 여부 판단:**
       - 오타 교정 결과를 읽어들이고, 식재료/식음료가 아닌 항목은 결과에서 제외하라.
       - 영어 단어여도 식재료(음식)라면 포함하라. 단, F32, G_CODE 같은 무의미한 영문 코드는 삭제하라

    [출력 형식]
    - 반드시 아래 JSON 구조의 리스트만 반환하라. (설명 금지)
    - [{"product_name": "이름", "quantity": 1, "unit": "단위", "category": "카테고리"}]
    """

    try:
        response = ollama.chat(
            model='midm2', 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': input_text}
            ],
            options={'temperature': 0.1, 'num_ctx': 4096},
            keep_alive=-1
        )
        
        content = response['message']['content']
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        # 좀비 파싱
        restored_items = []
        item_pattern = r'\{\s*"product_name".*?\}'
        raw_items = re.findall(item_pattern, content, re.DOTALL)
        
        for raw_item in raw_items:
            try:
                item_obj = json.loads(raw_item)
                if item_obj.get("product_name"):
                    restored_items.append(item_obj)
            except:
                pass
        
        return restored_items

    except Exception as e:
        # 에러 발생 시 빈 리스트 반환 (디버그 프린트 제거)
        return []

def verify_and_fix_results(initial_results):
    """
    [2차 검증] 1차 추출된 결과를 비판적으로 검토하여 이상한 항목을 수정하거나 삭제
    """
    if not initial_results: return []

    input_json = json.dumps(initial_results, ensure_ascii=False, indent=2)

    # 2차 검증 프롬프트 (사용자님 버전 유지)
    system_prompt = """
    너는 '식재료 데이터 품질 관리자'다. 
    1차로 추출된 식재료 목록을 검토하여, 잘못된 항목을 수정하거나 삭제하고 최종 리스트를 반환하라.
    
    [검증 체크리스트]
    1. 오타 교정
    2. 카테고리 오류 수정
    3. 비식재료 제거 (의미를 알 수 없는 항목들 포함)
    4. 형식 유지: JSON 리스트

    [출력 형식]
    - 수정된 JSON 리스트만 출력하라. (설명 금지)
    """

    try:
        response = ollama.chat(
            model='midm2', 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': input_json}
            ],
            options={'temperature': 0.1, 'num_ctx': 4096},
            keep_alive=-1
        )
        
        content = response['message']['content']
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        try:
            verified_results = json.loads(content)
            if isinstance(verified_results, list): return verified_results
            elif isinstance(verified_results, dict) and "items" in verified_results: return verified_results["items"]
            else: return initial_results
        except:
            item_pattern = r'\{\s*"product_name".*?\}'
            raw_items = re.findall(item_pattern, content, re.DOTALL)
            restored = [json.loads(s) for s in raw_items]
            return restored if restored else initial_results

    except Exception:
        # 에러 시 원본 반환
        return initial_results

def refine_ingredients_with_llm(ocr_data_list):
    if not ocr_data_list: return []

    clean_candidates = [item for item in ocr_data_list if not is_garbage_text(item)]
    
    # 디버그 프린트 제거
    # print(f"⚡ LLM 정제 시작: {len(clean_candidates)}개 항목 처리 중...")

    CHUNK_SIZE = 30
    first_pass_items = []
    
    # 1. 1차 추출
    for i in range(0, len(clean_candidates), CHUNK_SIZE):
        chunk = clean_candidates[i:i + CHUNK_SIZE]
        items = refine_batch_items(chunk)
        if items:
            first_pass_items.extend(items)
            
    # 2. 2차 검증
    final_items = verify_and_fix_results(first_pass_items)
            
    return final_items