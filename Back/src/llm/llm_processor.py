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
        "결제", "카드", "면세", "부가세", "포인트", "주소", "TEL", "대표", 
        "할인", "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
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
        if isinstance(item, dict):
            text = item.get('text', '')
        elif isinstance(item, list):
            text = " ".join(str(x) for x in item)
        else:
            text = str(item)
        input_lines.append(f"- {text}")
    
    input_text = "\n".join(input_lines)
    
    print(f"\n[Debug] LLM Input:\n{input_text[:100]}...\n")

    # [핵심] 모델에게 "생각"할 틈을 주지 않는 예시(Few-Shot) 제공
    system_prompt = """
    You are an AI expert specializing in OCR error correction and structured data extraction from Korean receipts.
    Your goal is to extract **food ingredients** suitable for refrigerator storage from the provided OCR text lines.

    [Primary Instructions]
    1. **Target:** Extract ONLY food ingredients. Ignore non-food items (e.g., plastic bags, fees, headers).
    2. **Extraction Strategy (CRITICAL):**
       - **2-a. Keyword Spotting (Priority):** First, scan the text for any recognizable Korean food noun (e.g., '두부', '우유', '삼겹살', '라면'). 
         - If a clear food noun is found inside the string, **EXTRACT IT IMMEDIATELY** and **STOP** analyzing the rest.
         - Ignore prefixes, suffixes, brand names, or gibberish surrounding the keyword. (e.g., '009풀/소가부침두부' -> Contains '두부'? -> YES -> Result: '두부').
       - **2-b. Typo Correction (Secondary):** Only if **NO** recognizable food noun is found, strictly then attempt to correct typos based on context and phonetic similarity (e.g., '면필' -> '연필').

    3. **Formatting:** Return the result strictly as a JSON List. Do not include markdown tags or explanations.

    [Data Extraction Rules]
    - **product_name**: Extract the core ingredient name. Remove brand names and adjectives unless necessary for identification.
    - **quantity**: Extract the numeric quantity. If not specified, default to 1.
    - **unit**: Use standard units: ['개' (pieces), 'g', 'kg', 'ml', 'L']. If unclear, use '개'.
    - **category**: Choose one from: ['육류' (Meat), '어패류' (Seafood), '채소' (Vegetable), '과일' (Fruit), '유제품' (Dairy), '가공식품' (Processed), '소스' (Sauce), '음료' (Beverage), '기타' (Others)].

    [Few-Shot Examples (Logic Demonstration Only)]
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
    Analyze the provided OCR text lines below and extract food ingredients following the rules above.
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
                user_message  # 수정된 메시지 객체 사용
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
        
        # [핵심 수정] 여기서 image_path를 refine_batch_items에 전달해야 함!
        items = refine_batch_items(chunk)
        
        if items:
            final_items.extend(items)
            
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
        model="deepseek-r1:8b",
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
