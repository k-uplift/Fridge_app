from fastapi import APIRouter, UploadFile, File, HTTPException
from .OCR_processor import AdvancedOCRProcessor
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
        result = ocr_processor.process(file_path)

        if result is None:
            raise HTTPException(status_code=400, detail="이미지를 읽을 수 없거나 파일이 손상되었습니다.")

        # 3. [Fix] 안정적인 데이터 파싱: .get() 메서드를 사용하여 키가 없더라도 오류 없이 기본값을 반환
        # process 함수가 실패했을 때 'meta' 키가 없을 수 있으므로 안전장치 추가
        final_count = result.get('count', 0)
        
        # 'meta' 키 대신 'count' 키를 직접 사용하여 안정성을 높입니다.
        return {
            "status": result.get("status", "success"),
            "line_count": result.get("line_count", 0),
            "lines": result.get("lines", [])
        }

    except Exception as e:
        # OCR 처리 중 오류 발생 시, 원본 에러 메시지 출력
        print(f"OCR 처리 중 오류 발생: {e}")
        # 'meta' 에러는 여기서 발생한 것이므로, 일반적인 500 에러로 처리합니다.
        raise HTTPException(status_code=500, detail=f"OCR 처리 실패: {str(e)}")
        
    finally:
        # 4. 임시 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)