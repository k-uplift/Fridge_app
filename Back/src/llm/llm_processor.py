import ollama
import json
import re

def get_text_from_item(item):
    """
    입력이 딕셔너리든 문자열이든 텍스트만 추출
    Logic: 신뢰도가 0.6 미만인 경우 (불확실:...) 태그를 부착하여 LLM에게 힌트 제공
    """
    if isinstance(item, dict):
        text = str(item.get('text', '') or item.get('product_name', '') or '').strip()
        conf = float(item.get('confidence', 0.0))
        if 0 < conf < 0.6:
            return f"(불확실:{text})"
        return text
    return str(item).strip()

def is_garbage_text(item):
    """
    1차 필터링: 명확한 비식재료 및 노이즈 제거 (Hard Filtering)
    """
    if isinstance(item, dict):
        text = item.get('text', '')
        conf = item.get('confidence', 0.0)
        if conf > 0 and conf < 0.2:
            return True
    else:
        text = str(item)

    if not text: return True
    text = text.strip()
    
    if len(text) < 2 and not re.search(r'[가-힣]', text): return True

    GARBAGE_KEYWORDS = [
        "합계", "결제", "카드", "면세", "부가세", "포인트", "주소", "TEL", "대표", 
        "할인", "영수증", "Total", "내역", "배달", "반품", "교환", "가맹점", 
        "금액", "승인", "매출", "사업자", "품목", "봉투", "쇼핑백", "종량제", "비닐", "Trash", "단가", "수량",
        "POINT", "Point", "적립", "사용", "소멸", "잔여", "누리", "에누리",
        "PL", "S-OIL", "L.POINT", "CASH", "CARD", "쿠폰", 
        "미사용", "개월", "문의", "안내", "영수증확인", "서명"
    ]
    
    if any(k in text for k in GARBAGE_KEYWORDS): return True

    return False

def refine_batch_items(ocr_chunk):
    """
    LLM을 사용하여 OCR 청크를 정제.
    전략: Few-Shot (Domain Shift) + CoT (Chain of Thought)
    """
    input_lines = []
    for i, item in enumerate(ocr_chunk):
        text = get_text_from_item(item)
        input_lines.append(f"- {text}")
    
    input_text = "\n".join(input_lines)

    system_prompt = """
    당신은 OCR(광학 문자 인식) 에러를 수정하고 식재료 데이터를 구조화하는 AI 전문가입니다.
    입력된 텍스트는 영수증 데이터이며, EasyOCR 특유의 오탈자가 포함되어 있습니다.
    
    [작업 목표]
    1. 오타 수정: 시각적으로 유사한 문자('0'vs'O', '1'vs'l' 등)와 문맥상 오타를 복원하십시오.
    2. 데이터 추출: 유효한 식재료만 추출하여 JSON 리스트로 변환하십시오.
    3. 추론: '(불확실:...)' 태그가 있는 항목은 주변 문맥을 보고 올바른 단어로 추론하십시오.

    [주의 사항]
    - unit(단위)이 없으면 기본값 '개'를 사용하세요.
    - quantity(수량)가 없으면 기본값 1을 사용하세요.
    - category는 {'과일', '채소', '육류', '해산물', '유제품', '곡물', '음료', '가공식품', '조미료', '기타'} 중 선택하세요.

    ---
    [학습용 예시 - 내용 참조 금지 (논리만 학습하세요)]
    
    **Example 1 (도메인: PC 부품)**
    Input:
    - (불확실:지포스 RTX 3O60)
    - 1개
    - (불확실:삼성전자 DDR4 램 8GB)
    
    Reasoning:
    1. 'RTX 3O60'의 'O'는 모델명 문맥상 숫자 '0'이어야 함 -> "RTX 3060".
    2. '1개'는 위 그래픽카드의 수량임.
    3. '삼성전자...'는 오타 없음.
    
    Result:
    ```json
    [
      {"product_name": "지포스 RTX 3060", "quantity": 1, "unit": "개", "category": "PC부품"},
      {"product_name": "삼성전자 DDR4 램 8GB", "quantity": 1, "unit": "개", "category": "PC부품"}
    ]
    ```

    **Example 2 (도메인: 문구류)**
    Input:
    - (불확실:모나미 볼폔 1.0mm)
    - 1O자루
    
    Reasoning:
    1. '볼폔'은 '볼펜'의 오타임 -> "모나미 볼펜 1.0mm".
    2. '1O자루'의 'O'는 숫자 '0'이어야 함 -> 수량 10.
    
    Result:
    ```json
    [
      {"product_name": "모나미 볼펜 1.0mm", "quantity": 10, "unit": "자루", "category": "문구"}
    ]
    ```
    ---

    [실제 작업 데이터]
    위 예시의 내용(PC, 문구)을 절대 출력하지 마세요. 오직 아래 입력 데이터만 처리하세요.

    Input:
    """ + f"\n{input_text}\n" + """

    [출력 형식]
    먼저 **Reasoning:** 섹션에 수정 이유를 적고, 그 다음 **Result:** 섹션에 JSON을 작성하세요.
    """

    try:
        response = ollama.chat(
            model='mistral:latest', 
            messages=[
                {'role': 'system', 'content': system_prompt}
            ],
            options={
                'temperature': 0.1,  
                'num_ctx': 4096,
                'repeat_penalty': 1.1 
            },
            keep_alive=-1
        )
        
        content = response['message']['content']
        
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        content = content.replace("```json", "").replace("```", "").strip()
        
        restored_items = []
        
        json_pattern = r'\[\s*\{.*?\}\s*\]'
        match = re.search(json_pattern, content, re.DOTALL)
        
        if match:
            try:
                restored_items = json.loads(match.group())
            except json.JSONDecodeError:
                item_pattern = r'\{\s*"product_name".*?\}'
                raw_items = re.findall(item_pattern, content, re.DOTALL)
                for raw_item in raw_items:
                    try:
                        raw_item_fixed = re.sub(r',\s*\}', '}', raw_item) 
                        item_obj = json.loads(raw_item_fixed)
                        if item_obj.get("product_name"):
                            restored_items.append(item_obj)
                    except:
                        pass
        else:
            # 리스트를 못 찾은 경우 개별 객체 탐색
            item_pattern = r'\{\s*"product_name".*?\}'
            raw_items = re.findall(item_pattern, content, re.DOTALL)
            for raw_item in raw_items:
                try:
                    item_obj = json.loads(raw_item)
                    restored_items.append(item_obj)
                except:
                    pass
        
        return restored_items

    except Exception as e:
        print(f"Error in refine_batch_items: {e}")
        return []

def verify_and_fix_results(initial_results):
    """
    [2차 검증] 1차 결과에서 환각(Hallucination) 및 형식 오류 제거
    """
    if not initial_results: return []

    input_json = json.dumps(initial_results, ensure_ascii=False, indent=2)

    system_prompt = """
    당신은 '식재료 데이터 검수자'입니다.
    1차 추출된 JSON 리스트를 검토하여 다음 오류를 수정하고 최종 리스트만 출력하세요.

    [체크리스트]
    1. 비식재료 제거: '비닐봉투', '카드영수증', '포인트적립' 등이 포함되어 있다면 삭제하세요.
    2. 카테고리 교정: 품목명과 카테고리가 일치하는지 확인하세요.
    3. 오타 최종 확인: 아직도 깨진 글자가 있다면 문맥에 맞춰 수정하세요.

    [출력]
    설명 없이 오직 JSON 리스트만 출력하세요.
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
        
        # JSON 추출 시도
        try:
            verified_results = json.loads(content)
            if isinstance(verified_results, list): return verified_results
            elif isinstance(verified_results, dict) and "items" in verified_results: return verified_results["items"]
        except:
            pass
        # 실패 시 정규식으로 다시 추출
        item_pattern = r'\{\s*"product_name".*?\}'
        raw_items = re.findall(item_pattern, content, re.DOTALL)
        restored = []
        for s in raw_items:
            try:
                restored.append(json.loads(s))
            except:
                pass
                
        return restored if restored else initial_results

    except Exception:
        return initial_results

def refine_ingredients_with_llm(ocr_data_list):
    """
    메인 진입 함수
    """
    if not ocr_data_list: return []

    clean_candidates = [item for item in ocr_data_list if not is_garbage_text(item)]

    CHUNK_SIZE = 15
    first_pass_items = []
    
    for i in range(0, len(clean_candidates), CHUNK_SIZE):
        chunk = clean_candidates[i:i + CHUNK_SIZE]
        if not chunk: continue
        
        items = refine_batch_items(chunk)
        if items:
            first_pass_items.extend(items)
            
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
