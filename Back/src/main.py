#main.py (FastAPI 실행 및 API 경로 정의)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # CORS 미들웨어 import
from anyio import to_thread

from .db.database import initialize_database # DB 초기화 함수
from contextlib import asynccontextmanager

from .ingredients.ingredients_router import router as ingredients_router
from .ocr.ocr_router import router as ocr_router
from .recipes.recipes_router import router as recipes_router
from .dishes.dishes_router import router as dishes_router
from .llm.llm_router import router as llm_router

# ---------- Lifespan Context Manager 정의 (Startup/Shutdown 관리) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI 서버 시작: 데이터베이스 초기화 작업 시작")

    # [수정] 동기 함수를 별도 스레드에서 실행하여 메인 루프 막힘 방지
    await to_thread.run_sync(initialize_database)
    
    print("FastAPI 서버 시작: 초기화 완료!")

    yield
    print("FastAPI 서버 종료")


# FastAPI 서버 객체 생성
app = FastAPI(lifespan=lifespan)

# ---------- CORS 설정 -----------
origins = [
    "http://localhost",
    "http://localhost:3000", # 프론트엔드 개발 서버 포트
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- API Endpoints (라우터) ----------

# 식재료관련 라우터
app.include_router(ingredients_router, prefix="/ingredients", tags=["Ingredients"])
# OCR 관련 라우터
app.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
# 레시피 관련 라우터
app.include_router(recipes_router, prefix="/recipes", tags=["Recipes"])
# 조리된 음식 관련 라우터
app.include_router(dishes_router, prefix="/dishes", tags=["Cooked Dishes"])
# LLM 관련 라우터
app.include_router(llm_router, prefix="/llm", tags=["AI Processing"])

