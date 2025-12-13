#main.py (FastAPI 실행 및 API 경로 정의)

from fastapi import FastAPI
from .db.database import initialize_database # DB 초기화 함수
from contextlib import asynccontextmanager

from .ingredients.ingredients_router import router as ingredients_router
from .ocr.ocr_router import router as ocr_router
from .recipes.recipes_router import router as recipes_router
from .dishes.dishes_router import  router as dishes_router

# from .llm.router import router as llm_internal_router

# ---------- Lifespan Context Manager 정의 (Startup/Shutdown 관리) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 (Startup) 실행
    print("FastAPI 서버 시작: 데이터베이스 초기화 작업 시작")
    initialize_database()
    yield


# FastAPI 서버 객체 생성
app = FastAPI(lifespan=lifespan)


# ---------- API Endpoints (라우터) ----------

# 식재료관련 라우터
app.include_router(ingredients_router, prefix="/ingredients", tags=["Ingredients"])
# OCR 관련 라우터
app.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
# 레시피 관련 라우터
app.include_router(recipes_router, prefix="/recipes", tags=["Recipes"])
# 조리된 음식 관련 라우터
app.include_router(dishes_router)


#app.include_router(llm_internal_router, prefix="/llm", tags=["Internal"])
