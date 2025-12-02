from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid

from .OCR_processor import preprocess_image, extract_receipt_data

router = APIRouter()

# 임시 저장소 설정
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/receipt", summary="영수증 이미지 OCR")
async def analyze_receipt(file: UploadFile = File(...)):
    """
    영수증 이미지를 업로드받아 상품명과 수량을 추출합니다.
    """
    # 파일명 충돌 방지
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # 서버에 임시 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 전처리 함수 호출 (경로 전달)
        processed_img = preprocess_image(file_path)

        if processed_img is None:
            raise HTTPException(status_code=400, detail="이미지를 읽을 수 없거나 파일이 손상되었습니다.")

        # 데이터 추출 함수 호출 (전처리된 이미지 객체 전달)
        receipt_data = extract_receipt_data(processed_img)

        return {
            "status": "success",
            "count": len(receipt_data),
            "data": receipt_data
        }

    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 처리 실패: {str(e)}")
        
    finally:
        # 임시 파일 삭제 (서버 용량 관리)
        if os.path.exists(file_path):
            os.remove(file_path)
