1. 프로젝트 소개 및 기술 스택
 - 프로젝트 명: 프레시 킵 (Fresh Keep) 백엔드 서버
 - 목적: OCR-LLM 기반 식재료 자동 등록 및 유통기한/레시피 추천 기능을 제공하는 핵심 API 서버
 - 주요 기술 스택:
    - 프레임워크: FastAPI (Python)
    - 데이터베이스: SQLite
    - AI/ML: Ollama (LLM 정제), PaddleOCR (영수증 인식)

2. 설치 및 실행 환경 설정
2.1 필수 환경 설정
    - Python: 3.9 이상 버전
    - Ollama 서버: LLM 구동을 위한 서버 설치
    - OCR 엔진: PaddlePaddle 및 PaddleOCR 라이브러리

2.2 종속성 설치
    ```bash
    pip install -r requirements.txt
    ```

2.3 AI 모델 다운로드
- 사용 모델: exaone3.5:7.8b
    ```bash
    ollama pull exaone3.5:7.8b
    ```

3. 서버 실행
- 로컬 환경에서 백엔드 서버를 구동하는 방법
    ```bash
    # Uvicorn을 사용하여 서버 실행
    uvicorn main:app --reload
    ```
- 서버 주소: 기본 실행 주소는 http://127.0.0.1:8000 

4. API 명세 확인
FastAPI의 자동 생성된 문서를 통해 모든 API 엔드포인트와 데이터 스키마를 확인 가능

- Swagger UI (Interactive Docs): http://127.0.0.1:8000/docs
- Redoc: http://127.0.0.1:8000/redoc

5. 참고: 개발 환경 설정
- .gitignore 파일 사용: .gitignore 파일은 프로젝트를 Git에 올릴 때 제외할 파일들(가상 환경 파일, DB 파일 등)을 필터링하기 위해 사용됩

- 가상 환경 폴더: 프로젝트에서는 app_venv 폴더를 가상 환경 폴더로 가정하고 .gitignore에 등록해 놓았습니다. 가상 환경 폴더를 프로젝트 폴더 밖에서 관리한다면 이 설정은 무시해도 무방



