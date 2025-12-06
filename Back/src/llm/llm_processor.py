import ollama
import json
import re

def get_text_from_item(item):
    """
    [수정됨] JSON 구조(raw_text, avg_confidence)에 맞춰 텍스트 추출 및 불확실 태그 부착
    """
    if isinstance(item, dict):
        # 1. 텍스트 추출: raw_text 우선, 없으면 text -> product_name 순
        text = str(item.get('raw_text', '')).strip()
        # 2. 신뢰도 추출 로직 개선 (List vs Float 처리)
        avg_conf = 0.0
        # Case A: avg_confidence 키가 명시적으로 있는 경우 (가장 정확)
        if 'avg_confidence' in item:
            avg_conf = float(item['avg_confidence'])
        # Case B: avg_confidence가 없고 confidence(리스트)만 있는 경우
        elif 'confidence' in item:
            conf_data = item['confidence']
            if isinstance(conf_data, list) and conf_data:
                # 리스트 평균 계산
                avg_conf = sum(conf_data) / len(conf_data)
            elif isinstance(conf_data, (float, int)):
                # 혹시 단일 값으로 들어온 경우
                avg_conf = float(conf_data)
        # 3. 로직 적용: 평균 신뢰도가 0.6 미만이면 태그 부착
        if 0 < avg_conf < 0.6:
            return f"(불확실:{text})"
        return text
    return str(item).strip()

def is_garbage_text(item):
    """
    [수정됨] 1차 필터링 로직 개선
    - avg_confidence 활용
    - 숫자(수량/가격)와 영어(단위/코드)가 삭제되지 않도록 정규식 범위 확장
    """
    text = ""
    avg_conf = 0.0
    
    # 1. 텍스트 및 신뢰도 추출
    if isinstance(item, dict):
        text = str(item.get('raw_text', '') or item.get('text', '') or '').strip()
        
        # 신뢰도 추출 (List/Float 처리 호환)
        if 'avg_confidence' in item:
            avg_conf = float(item['avg_confidence'])
        elif 'confidence' in item:
            conf_data = item['confidence']
            if isinstance(conf_data, list) and conf_data:
                avg_conf = sum(conf_data) / len(conf_data)
            elif isinstance(conf_data, (float, int)):
                avg_conf = float(conf_data)
        
        # 신뢰도가 너무 낮으면(0.2 미만) 삭제
        if 0 < avg_conf < 0.2:
            return True
    else:
        text = str(item).strip()

    # 2. 빈 문자열 삭제
    if not text: return True
    
    # 3. [중요 수정] "의미 있는 문자"가 하나도 없으면 삭제
    # 기존: 한글이 없으면 삭제 (문제 발생)
    # 변경: 한글, 숫자(0-9), 영어(a-zA-Z) 중 하나라도 있으면 유지
    # -> 이렇게 하면 특수문자만 있는 경우(예: ".", "-", "*")는 걸러지고, "1", "100g", "mart" 등은 살아남음
    if not re.search(r'[가-힣0-9a-zA-Z]', text):
        return True

    # 4. 불용어(Garbage Keywords) 필터링
    # (헤더나 명백한 쓰레기 단어 삭제)
    GARBAGE_KEYWORDS = [
        "합계", "결제", "카드", "면세", "부가세", "포인트", "주소", "TEL", "대표", 
        "할인", "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
        "금액", "승인", "매출", "사업자", "품목", "봉투", "쇼핑백", "종량제", "비닐", "Trash", "단가", "수량",
        "POINT", "Point", "적립", "사용", "소멸", "잔여", "누리", "에누리",
        "PL", "S-OIL", "L.POINT", "CASH", "CARD", "쿠폰", 
        "미사용", "개월", "문의", "안내", "영수증확인", "서명"
    ]
    
    # 키워드가 텍스트에 포함되어 있으면 삭제
    if any(k in text for k in GARBAGE_KEYWORDS): return True

    return False

def refine_batch_items(ocr_chunk):
    """
    [통합됨] LLM을 사용하여 OCR 청크를 정제하고 JSON화 (One-Pass)
    - 기존 1차(정제) + 2차(검증) 로직을 하나의 프롬프트로 병합
    """
    input_lines = []
    for i, item in enumerate(ocr_chunk):
        text = get_text_from_item(item)
        input_lines.append(f"Line {i+1}: {text}")
    
    input_text = "\n".join(input_lines)

    # 프롬프트 강화: 정제와 검증을 동시에 수행하도록 지시
    system_prompt = """
    당신의 역할은 **'한국 마트 영수증 데이터 표준화 및 검수 시스템'**이다.
    입력된 OCR 텍스트를 분석하여 **'실제 요리에 사용 가능한 식재료'**만 추출하여 정형화된 JSON으로 변환해라.

    [수행 절차]
    1. **라인 병합 (Context Merging):** - 상품명과 가격/수량이 줄바꿈으로 나뉜 경우, 문맥을 파악하여 하나의 항목으로 합치십시오.
       - 예: "001 사과" (\n) "1,000", "1", "1000 -> {"product_name": "사과", "price": 1000}

    2. **표준화 (Standardization):**
       - 오타나 불완전한 텍스트는 **한국어 표준 식재료명**으로 변환하십시오. (예: '브로커리' -> '브로콜리')
       - 브랜드명이 포함된 경우, 핵심 식재료명 위주로 정리해도 좋습니다.

    3. **엄격한 필터링 (Strict Filtering) - 중요:**
       - **요리에 쓸 수 없는 항목은 절대 결과에 포함하지 마십시오.**
       - 제외 대상: '비닐봉투', '종량제봉투', '재사용봉투', '배달팁', '할인쿠폰', '카드승인내역', '멤버십포인트', '영수증', '합계'
       
    4. **데이터 정형화:**
       - quantity: 없으면 기본값 1.
       - category: [채소, 과일, 육류, 수산물, 유제품, 가공식품, 양념/오일, 음료, 기타] 중 택 1.

    [출력 포맷]
    - 설명, 인사말, 마크다운(```json) 없이 **오직 JSON 리스트**만 출력하십시오.

    ```json
    [
        {
            "product_name": "표준화된 상품명",
            "quantity": 1,
            "category": "카테고리"
        }
    ]
    ```

    Input Data:
    """ + f"\n{input_text}\n"

    try:
        response = ollama.chat(
            model='midm2', 
            messages=[
                {'role': 'system', 'content': system_prompt}
            ],
            options={
                'temperature': 0.1,   # 검증까지 포함하므로 창의성을 더 낮춤
                'num_ctx': 4096,
            },
            keep_alive=-1
        )
        
        content = response['message']['content']
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        # JSON 파싱 (기존 로직 유지)
        restored_items = []
        json_pattern = r'\[\s*\{.*?\}\s*\]'
        match = re.search(json_pattern, content, re.DOTALL)
        
        if match:
            try:
                restored_items = json.loads(match.group())
            except: pass
        
        if not restored_items:
            item_pattern = r'\{\s*"product_name".*?\}'
            raw_items = re.findall(item_pattern, content, re.DOTALL)
            for raw_item in raw_items:
                try:
                    clean_json = re.sub(r',\s*\}', '}', raw_item)
                    item_obj = json.loads(clean_json)
                    restored_items.append(item_obj)
                except: continue
        
        return restored_items

    except Exception as e:
        print(f"Error in refine_batch_items: {e}")
        return []

def refine_ingredients_with_llm(ocr_data_list):
    """
    [수정됨] 메인 진입 함수 - 2차 검증 과정 삭제
    """
    if not ocr_data_list: return []

    # 1. Regex 기반 1차 쓰레기 제거 (필수)
    clean_candidates = [item for item in ocr_data_list if not is_garbage_text(item)]

    CHUNK_SIZE = 15
    final_items = []
    
    # 2. 배치 처리 (LLM 호출 1회로 끝냄)
    for i in range(0, len(clean_candidates), CHUNK_SIZE):
        chunk = clean_candidates[i:i + CHUNK_SIZE]
        if not chunk: continue
        
        # 여기서 나온 결과가 곧 최종 결과가 됨
        items = refine_batch_items(chunk)
        if items:
            final_items.extend(items)
            
    # verify_and_fix_results 호출 삭제됨
    return final_items

# 레시피 추천용 LLM 함수
def run_recipe_llm(user_prompt: str):
   
    # 레시피 추천 LLM 호출
    system_prompt = """
    당신은 "최고급 요리 연구가이자 레시피 추천 전문가"입니다.
    당신의 목표는 사용자가 가진 재료를 최대한 활용하여 만들 수 있는 실용적이고 정확한 레시피를 추천하는 것입니다.

    [출력 규칙(아주 중요)]
    - 반드시 아래 JSON 형식만 줄력해야 합니다.
    - JSON 바깥에 설명, 문장, 코드블록( ```json ), 인사말 등 어떤 것도 포함하지 마십시오.
    - 모든 값은 한국어로 작성하십시오.
    - steps는 반드시 순서가 있는 배열로 출력하십시오.
    - ingredients_main은 사용자가 가진 재료 중 실제로 사용되는 재료만 포함하십시오.
    - ingredients_needed는 사용자가 가지지 않은 “추가로 필요한 재료”만 지정하십시오.
    - JSON 키 이름은 절대 수정하지 마십시오.

    [출력 형식{JSON}]
    {
        "recipe_name": "요리 이름",
        "difficulty": "쉬움/보통/어려움 중 하나",
        "time_required": "예: 20분",
        "ingredients_main": ["사용된 보유 재료1", "사용된 보유 재료2"],
        "ingredients_needed": ["추가로 필요한 재료1", ...],
        "steps": ["1단계 설명", "2단계 설명", ...]
    }

    [레시피 생성 지침]
   - 사용자가 가진 재료를 최대한 많이 활용하십시오.
    - 만약 유통기한 정보가 제공된다면, 유통기한이 가까운 재료를 우선적으로 사용하는 요리를 추천하십시오.
    - 재료 이름만 작성하고, '컵', 'g', 'ml', '숟가락' 등 단위는 절대 표시하지 마십시오.
    - 요리 이름은 한국인이 실제로 해먹을 법한 현실적인 요리 위주로 선택하십시오.
    - 요리 난이도는 반드시 '쉬움', '보통', '어려움' 중 하나로 제한하십시오.
    - 조리 시간은 실제 평균 기준으로 현실적으로 작성하십시오. (예: '20분')
    - ingredients_main은 보유 재료 중 실제로 레시피에 사용되는 재료만 포함하십시오.
    - ingredients_needed는 만들기 위해 추가로 필요한 재료만 포함하십시오.
    - steps는 3~7단계로 구성하고, 각 단계는 8~25자 사이로 구체적으로 작성하십시오.
    - 전문 셰프가 초보자에게 알려주듯 간단하고 이해하기 쉬운 설명을 제공하십시오.

    [절대 해서는 안 되는 것]
    - JSON 바깥에 어떤 텍스트도 출력 금지
    - 코드블록(```json, ``` 등) 사용 금지
    - JSON 형식 오류 금지 (콤마 누락, 따옴표 누락 등)
    - 모델 자신의 생각이나 메타 발언 포함 금지
    - "다음은 JSON입니다:" 같은 문장 금지   

    [마지막 규칙]
    - 출력하기 전에 JSON 구조가 올바른지 스스로 점검하고 출력하십시오.

    """

    response = ollama.chat(
        model="midm2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={"temperature": 0.4, "num_ctx": 4096},
        keep_alive=0
    )

    content = response["message"]["content"]
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except:
        try:
            pattern = r'\{.*\}'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            
        except:
            return{
                "recipe_name": "오류",
                "steps": ["LLM 응답 파싱 실패"],
                "ingredients_needed": []
            }
