import ollama
import json
import re
import os

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
    else:
        text = str(item).strip()

    # 2. 빈 문자열 삭제
    if not text: return True
    
    # 3. [중요 수정] "의미 있는 문자"가 하나도 없으면 삭제
    # -> 이렇게 하면 특수문자만 있는 경우(예: ".", "-", "*")는 걸러지고, "1", "100g", "mart" 등은 살아남음
    if not re.search(r'[가-힣0-9a-zA-Z]', text):
        return True

    # 4. 불용어(Garbage Keywords) 필터링
    # (헤더나 명백한 쓰레기 단어 삭제)
    GARBAGE_KEYWORDS = [
        "결제", "카드", "부가세", "포인트", "주소", "TEL", "대표", 
        "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
        "승인", "매출", "사업자", "품목", "봉투", "쇼핑백", "종량제", "비닐", "Trash",
        "POINT", "Point", "적립", "사용", "소멸", "잔여", "누리", "에누리",
        "PL", "S-OIL", "L.POINT", "CASH", "CARD", "쿠폰", "부가세", "바코드", "회원", "포인트"
        "미사용", "개월", "문의", "안내", "영수증확인", "서명", "사업자번호", "전화", "홈페이지"
    ]
    
    # 키워드가 텍스트에 포함되어 있으면 삭제
    if any(k in text for k in GARBAGE_KEYWORDS): return True

    return False

# 2. LLM 호출 함수 (One-Shot 프롬프트 적용)
def refine_batch_items(lines: list):
    input_lines = []
    for i, item in enumerate(lines):
        text = str(item).strip()
        if text:
            input_lines.append(f"Line {i+1}: {text}")
    
    input_text = "\n".join(input_lines)
    
    # 디버깅: 실제로 LLM에 들어가는 텍스트 확인
    print(f"\n[Debug Batch Input]\n{input_text}\n----------------")
    
    print(f"\n[Debug] LLM Input:\n{input_text[:100]}...\n")

    # [핵심] 모델에게 "생각"할 틈을 주지 않는 예시(Few-Shot) 제공
    system_prompt = """
    You are an AI expert specializing in OCR data extraction from Korean receipts.

    [Primary Instructions]
    1. **Process ALL Lines (CRITICAL):** You must iterate through **EVERY single line** provided in the input. Do NOT stop processing after finding the first ingredient. Check all lines from top to bottom.
    2. **Target:** Extract ONLY food ingredients. Ignore non-food items (e.g., plastic bags, fees, headers).

    3. **Extraction Strategy:**
        - **Step 1: Keyword Spotting:** Scan the current line for a recognizable Korean food noun (e.g., '두부', '우유', '삼겹살', '양파').
            - If a clear food noun is found: Extract it and **move to the next line immediately**. (Do NOT stop the entire task).
            - Ignore prefixes (e.g., '풀/', 'CJ'), suffixes, or brand names. 
            - *Example:* '009풀/소가부침두부' -> Keyword '두부' found -> Extract '두부' -> Next line.
        - **Step 2: Typo Correction:** If NO food noun is found, try to correct typos (e.g., '면필' -> '연필').
        - **Step 3: Skip:** If the line is definitely not food, skip to the next line.

    4. **Formatting:** Return the result strictly as a JSON List.

    [Data Extraction Rules]
    - **product_name**: Extract the core ingredient name only. (e.g., '풀/소가부침두부' -> '두부', '008 상추' -> '상추').
    - **quantity**: Numeric (default 1).
    - **unit**: ['개', 'g', 'kg', 'ml', 'L'] (default '개').
    - **category**: Choose exactly one from: ['채소', '과일', '육류', '수산물', '유제품/두부/알류', '면/빵/떡', '가공/냉동식품', '양념/오일', '음료', '기타'].

    [Few-Shot Examples (Structure Only)]
    *Note: These examples use non-food items to demonstrate the correction and formatting logic. Apply this same logic to FOOD ingredients in the actual task.*

    Input Lines:
    - 001. P 몽나미 볼팬 (Black)
    - 3M 스카치테이푸 1,500
    - 003. A4 용지 1Box

    Output JSON:
    [
        {"product_name": "볼펜", "quantity": 1, "unit": "개", "category": "기타"},
        {"product_name": "테이프", "quantity": 1, "unit": "개", "category": "기타"},
        {"product_name": "A4 용지", "quantity": 1, "unit": "개", "category": "기타"}
    ]

    [Task]
    Analyze ALL provided text lines below and extract every food ingredient found.
    """.strip()

    # 실제 사용자 입력
    user_content = f"User:\n{input_text}\n\nAssistant:"
    user_message = {
        "role": "user",
        "content": user_content
    }
    
    try:
        response = ollama.chat(
            model='deepseek-r1:8b', 
            messages=[
                {'role': 'system', 'content': system_prompt},
                user_message  
            ],
            format='json',
            options={
                'temperature': 0.0,
                'num_ctx': 8192,
                'num_predict': 4096,
            },
            keep_alive=-1
        )
        
        content = response['message']['content']
        
        print(f"[Debug] Model Thought:\n{response}...\n")
        # print(f"[Debug] Raw Output:\n{content[:200]}...") # 디버깅
        
        # JSON 추출 (Markdown 제거 및 파싱)
        restored_items = []
        try:
            # 1. 가장 넓은 범위의 대괄호 [] 찾기
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                restored_items = json.loads(json_str)
            else:
                # 2. 실패 시 개별 객체 {} 찾기
                matches = re.findall(r'\{.*?\}', content, re.DOTALL)
                for m in matches:
                    restored_items.append(json.loads(m))
        except Exception:
            pass

        # 구조 정리
        if isinstance(restored_items, dict):
            # {"items": [...]} 형태일 경우
            for val in restored_items.values():
                if isinstance(val, list):
                    restored_items = val
                    break
            else:
                restored_items = [restored_items]

        # 최종 정규화
        normalized = []
        if isinstance(restored_items, list):
            for item in restored_items:
                if isinstance(item, dict):
                    p_name = str(item.get("product_name", "")).strip()
                    if not p_name: continue
                    
                    normalized.append({
                        "product_name": p_name,
                        "quantity": float(item.get("quantity", 1) or 1),
                        "unit": str(item.get("unit", "개")).strip(),
                        "category": str(item.get("category", "기타")).strip(),
                    })
            
        return normalized
    
    except Exception as e:
        print(f"Error in refine_batch_items: {e}")
        return []
    
def refine_ingredients_with_llm(ocr_data_list):
    """
    """
    if not ocr_data_list: return []

    if isinstance(ocr_data_list, dict) and 'lines' in ocr_data_list:
        ocr_data_list = ocr_data_list['lines']
    # 1. Regex 기반 1차 쓰레기 제거 (필수)
    clean_candidates = [item for item in ocr_data_list if not is_garbage_text(item)]

    CHUNK_SIZE = 20
    final_items = []
    
    print(f"Processing {len(clean_candidates)} items (Filtered from {len(ocr_data_list)})...")
    # 2. 배치 처리
    for i in range(0, len(clean_candidates), CHUNK_SIZE):
        chunk = clean_candidates[i:i + CHUNK_SIZE]
        if not chunk: continue
        
        items = refine_batch_items(chunk)
        
        if items:
            final_items.extend(items)
            
    return final_items

# 레시피 추천용 LLM 함수
def run_recipe_llm(user_prompt: str):
   
    # 레시피 추천 LLM 호출
    system_prompt = """
    너는 가정용 레시피를 연구하는 "전문 요리 연구가"이다. 주어진 재료 목록을 바탕으로 가장 합리적이고 맛있는 레시피를 반환하라.

    [출력 규칙(아주 중요)]
    - 반드시 아래 JSON 형식만 줄력해야 한다.
    - JSON 바깥에 설명, 문장, 코드블록( ```json ), 인사말 등의 다른 데이터를 포함하지 않는다.
    - 모든 과정은 한국어로 작성한다.
    - steps는 조리 순서대로 작성한다.
    - ingredients_main은 사용자가 가진 재료 중 실제로 사용되는 재료만 포함한다.
    - ingredients_needed는 사용자가 가지지 않은 “추가로 필요한 재료”만 지정한다.
    - JSON 키 이름은 절대 수정하지 않는다.

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
    1. 절대 모든 재료를 사용하지 않는다. 제공된 재료는 냉장고 내의 전체 식재료 리스트일 뿐, 사용해야 할 재료가 아니다. 필요한 재료만 골라 사용하여라.
    2. 이미 조리 완료된 식재료나, 음료 등은 억지로 레시피에 사용하지 않는다. 추가 조리가 필요한 식재료를 위주로 사용한다.
    3. 전체 식재료 리스트 중, 메인 식재료(고기, 생선, 두부, 채소, 김치 등에서 선택한다.)를 하나 선택하고, 이에 어울리는 레시피를 만들어야 한다.
    4. 맛의 조화를 위해서 추가로 필요한 재료가 있다면 과감하게 사용하려라. 단, 추가 재료의 숫자는 5가지 이하여야 한다. 
    5. 요리의 난이도는 일반 가정집에서 수행할 수 있는 수준이어야 한다. 또, 난이도는 '쉬움', '보통', '어려움' 중 하나를 지정하여 출력한다.
    6. 재료 이름만 작성하고, '컵', 'g', 'ml' 등의 상세 단위는 표기하지 않는다.
    7. 조리 시간이 60분 이내인 레시피를 제공한다.
    8. steps는 3~7단계로 구성하고, 각 단계는 8~25자 사이로 구체적으로 작성한다.
        - 이 때, 요리를 처음 하는 사람도 이해할 수 있도록 쉽게 설명한다.
    - ingredients_main은 보유 재료 중 실제로 레시피에 사용되는 재료를 모두 포함한다.
    - ingredients_needed는 만들기 위해 추가로 필요한 재료를 모두 포함한다.

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
        model="exaone3.5:7.8b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={"temperature": 0.6, "num_ctx": 4096},
        keep_alive=0
    )

    content = response["message"]["content"]
    content = content.replace("```json", "").replace("```", "").strip()

    # 1. JSON 파싱 시도
    data = None
    try:
        # 1-1. 순수 JSON 파싱 시도
        data = json.loads(content)
    except:
        try:
            # 1-2. 실패 시 정규식으로 JSON 부분만 추출 시도
            pattern = r'\{.*\}'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                raise ValueError("JSON 패턴을 찾을 수 없음")
        except:
            # 1-3. 모든 파싱 실패 시 에러 반환
            return {
                "recipe_name": "오류",
                "steps": ["LLM 응답 파싱 실패"],
                "ingredients_needed": []
            }

    # 2. [공통 로직] steps 번호 제거 (파싱 성공한 data에 대해 수행)
    if "steps" in data and isinstance(data["steps"], list):
        cleaned_steps = []
        for step in data["steps"]:
            # "1. 끓인다", "1) 끓인다" -> "끓인다" 제거
            clean_step = re.sub(r'^\d+[\.\)]\s*', '', str(step))
            cleaned_steps.append(clean_step)
        data["steps"] = cleaned_steps

    # 3. 최종 반환
    return data