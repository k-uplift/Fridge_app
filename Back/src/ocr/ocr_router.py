# ocr_router.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from ..ocr.OCR_processor import AdvancedOCRProcessor # 기존 OCR 함수
from ..llm.llm_processor import refine_ingredients_with_llm # <--- [핵심] LLM 처리기 가져오기
import shutil
import os
import uuid

router = APIRouter()

# 임시 저장소 설정
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# [중요] OCR 프로세서 인스턴스 생성 (서버 시작 시 한 번만 로드)
# 전역 변수로 관리하여 매 요청마다 모델을 다시 로드하지 않게 합니다.
ocr_processor = AdvancedOCRProcessor(use_gpu=True) 

@router.post("/receipt", summary="영수증 이미지 OCR")
async def analyze_receipt(file: UploadFile = File(...)):
    """
    영수증 이미지를 업로드받아 상품명과 수량을 추출합니다.
    (AdvancedOCRProcessor 클래스 사용)
    """
    # 파일명 충돌 방지
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # 1. 서버에 임시 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. 통합 OCR 프로세서 실행 (.process 메서드 호출)
        ocr_result = ocr_processor.process(file_path)

        if ocr_result is None:
            raise HTTPException(status_code=400, detail="이미지를 읽을 수 없거나 파일이 손상되었습니다.")
        # OCR 결과에서 텍스트 라인 추출 (안전하게 가져오기)
        raw_lines = ocr_result.get("lines", [])
        
        # 만약 리스트 요소가 딕셔너리라면 'text' 키만 뽑아내고, 아니면 그대로 둠
        text_only_lines = [
            line['text'] if isinstance(line, dict) and 'text' in line else str(line)
            for line in raw_lines
        ]
        # ---------------------------------------------------------
        # [추가됨] 3. LLM 보정 수행
        # ---------------------------------------------------------
        print(f"[Debug] LLM에 전달되는 데이터: {text_only_lines[:3]}...") # 로그 확인 필수
        refined_data = refine_ingredients_with_llm(text_only_lines)
        
        print(f"[Server] LLM 보정 완료. {len(refined_data)}개 식재료 추출됨.")
        # ---------------------------------------------------------

        # 4. 최종 결과 반환
        return {
            "data": refined_data        # [핵심] LLM이 정제한 최종 식재료 JSON 리스트
        }

    except Exception as e:
        print(f"처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 처리 실패: {str(e)}")
        
    finally:
        # 5. 임시 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)