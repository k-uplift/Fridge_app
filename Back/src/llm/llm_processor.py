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
