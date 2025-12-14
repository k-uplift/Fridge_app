<img width="250" height="250" alt="image" src="https://github.com/user-attachments/assets/f620542e-434b-4d0b-a794-834d999371ab" />



# 1. 프로젝트 개요
- 프로젝트 이름 : 프레시 킵 (Fresh Keep)
- 프로젝트 설명 : 효율적인 냉장고 식재료 관리 어플리케이션
<br><br><br>
# 2. 팀원 및 팀 소개
<table width="100%">
    <thead>
        <tr>
            <th width="25%">기세웅</th>
            <th width="25%">김혜성</th>
            <th width="25%">박준서</th>
            <th width="25%">배선아</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td align="center">BE</td>
            <td align="center">FE</td>
            <td align="center">FE</td>
            <td align="center">BE</td>
        </tr>
        <tr>
            <td align="center">
                <a href="(https://github.com/k-uplift)">GitHub</a>
            </td>
            <td align="center">
                <a href="(https://github.com/maeseong)">GitHub</a>
            </td>
            <td align="center">
                <a href="(https://github.com/junseo0b)">GitHub</a>
            </td>
            <td align="center">
                <a href="(https://github.com/Baeseona)">GitHub</a>
            </td>
        </tr>
    </tbody>
</table>
<br><br><br>

# 3. 주요 기능 소개
**🥑 식재료 관리 (Ingredients)**
- **통합 조회 및 필터링** : 보관 위치(냉장, 냉동, 상온) 및 카테고리별로 식재료 목록을 필터링합니다.
- **검색 및 정렬** : 식재료 이름으로 검색하고, 유통기한 임박순, 이름순, 수량순 등으로 정렬합니다.
- **유통기한 알림** : 유통기한이 임박한 식재료 목록을 따로 조회하여 낭비르 방지합니다.
- **상태 관리** : 식재료를 사용 완료(USED) 또는 폐기(DISCARDED) 상태로 변경하며 히스토리 목록을 제공합니다.
<br>
  
**📝 AI/OCR 처리 (AI/OCR Processing)**
- **고도화된 OCR** : "PaddleOCR (한국어 모델)"을 사용하여 영수증 이미지에서 텍스트를 고속으로 추출합니다.
- **이미지 전처리** : cv2.resize를 통한 높이 정규화 및 numpy 기반 이미지 처리로 인식률을 향상합니다.
- **줄 단위 그룹화** : OCR 결과의 좌표(x,y)를 기반으로 텍스트를 줄 단위로 정렬 및 그룹화하여 상품 목록을 정확히 분리합니다.
<br>
  
**🧠 LLM 기반 데이터 정제 및 레시피 추천 (AI Processing)**
- **1차 노이즈 제거** : 정규식(re.search(r'[가-힣0-9a-zA-Z]')) 및 불용어 필터링을 통해 OCR 결과의 헤더/쓰레기 텍스트를 선행적으로 제거합니다.
- **구조화된 데이터 추출**
  - **Ollama (exaone3.5:7.8b)** 모델을 사용하여 잔여 텍스트에서 핵심 식재료 명, 수량, 단위, 카테고리를 정확히 추출합니다.
  - **Keyword Spotting** 전략을 적용하여 브랜드명이나 오타를 무시하고 핵심 재료명만 추출하도록 프롬프트에 명시했습니다.
- **레시피 추천** : 보유 재료 목록(유통기한 정보 포함)을 기반으로 JSON 형식의 구조화된 레시피를 생성하여 제공합니다.
<br><br><br>

# 4. 작업 및 역할 분담

<table width="100%">
    <thead>
        <tr>
            <th width="20%">이름</th>
            <th width="80%">담당 역할</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td align="center">기세웅</td>
            <td>
                <ul>
                    <li>OCR 연동</li>
                    <li>LLM 프롬프트 엔지니어링</li>
                    <li>AI 서비스 연결 오류 처리 및 디버깅</li>
                    <li>레시피 JSON 정제</li>
                </ul>
            </td>
        </tr>
        <tr>
            <td align="center">김혜성</td>
            <td>
                <ul>
                    <li>영수증 인식 및 출력 화면 구현</li>
                    <li>로그인 화면 구현</li>
                    <li>레시피 출력 화면 구현</li>
                </ul>
            </td>
        </tr>
      <tr>
            <td align="center">박준서</td>
            <td>
                <ul>
                    <li>알림 시스템 구현</li>
                    <li>LLM 후처리 출력 화면 구현</li>
                    <li>레시피 등록 화면 구현</li>
                </ul>
            </td>
        </tr>
      <tr>
            <td align="center">배선아</td>
            <td>
                <ul>
                    <li>DB 관리</li>
                    <li>라우터 구현</li>
                    <li>유통기한 자동 설정, 알림 구현</li>
                    <li>재료 부족분 분류 로직 구현</li>
                </ul>
            </td>
        </tr>
        </tbody>
</table>
<br><br><br>

# 5. 기술 스택
## 5.1 Language
- Frontend
  - Dart
  - Java
  - Kotiln
  - Swift
- Backend
  - Python
## 5.2 Backend
- Framework: FastAPI
- Database: SQLite3
- AI/LM:
  - OCR : PaddleOCR
  - LLM Runtime : Ollama
  - LLM Model: deepseek-r1:8b(ocr 데이터 정제)
  - LLM Model: exaone3.5:7.8b(레시피 생성)
  - Image Processin: OpenCV(cv2) 및 Numpy
## 5.3 Frontend
- Framework: Flutter
## 5.4 Cooperation
- Version Control: Git, GtiHub
- API Testing: Postman
<br><br><br>

# 6. 프로젝트 구조

```
Fridge_app/
 ┣ Back/                            # [백엔드] FastAPI 서버
 ┃   ┣ src/
 ┃     ┣ db/                        # DB 초기화 및 연결 로직
 ┃     ┣ dishes/                    # 조리된 음식 CRUD 및 라우터
 ┃     ┣ ingredients/               # 식재료 CRUD, 라우터, 스키마
 ┃     ┣ llm/                       # LLM 데이터 정제 로직 및 라우터
 ┃     ┣ ocr/                       # OCR 이미지 처리 및 라우터
 ┃     ┣ recipes/                   # 레시피 관련 라우터 
 ┃     ┗ main.py                    # FastAPI 앱 엔트리 포인트
 ┣ Front/                           # [프론트엔드] Flutter 애플리케이션
 ┃   ┣ android/                     # 안드로이드 플랫폼 관련 파일
 ┃   ┣ ios/                         # iOS 플랫폼 관련 파일
 ┃   ┣ lib/                         # 핵심 Dart 코드
 ┃     ┗ main.dart                  # 엔트리 포인트
 ┃   ┣ assets/                      # 이미지, 폰트, 리소스 파일
 ┃   ┣ test/                        # 단위 테스트 및 위젯 테스트 코드
 ┃   ┣ pubspec.yaml                 # Dart/Flutter 종속성 및 설정 파일
 ┃   ┗ README.md                    # Flutter 프로젝트 기본 README
 ┣ .gitignore                       # Git 무시 파일 목록
 ┗ README.md                        # 프로젝트 개요 및 사용법

```
<br><br><br>

# 7. 개발 워크플로우
## 브랜치 전략 (Branch Strategy)
- main branch
  - 운영 환경 배포가 가능한 가장 안정적인 상태의 코드 유지
  - 개발 작업은 기능 브랜치에서 시작하고, 테스트가 완료된 후 Pull Request(PR)을 통해 main으로 병합(merge)
- feature Branch (새로운 기능 추가 및 개발)
  - feature/core-expiry-logic : 식재료 및 조리 음식의 유통기한을 자동 계산하는 모듈 개발 브랜치
  - feature/implement-ingredient-status : DB에 등록된 식재료에 '상태' 필드를 추가하고 관리하는 브랜치
  - feature/implement-notification : 식재료 알림 기능 구현 브랜치
  - feature/ocr-llm-post-processing : OCR 추출 텍스트를 LLM으로 정제하여 JSON으로 변환하는 핵심 로직 구현 브랜치
  - feature/ocr_add_Expiration-date : OCR로 인식된 식재료 정보에 유통기한을 자동으로 추가하는 기능을 구현 브랜치
  - feature/recipe-recommendation : LLM 기반 레시피 추천 및 필요 재료 분리 기능 구현 브랜치
  - feature/refactor-backend-structure : 기초 구조 확립, 안정화 브랜치

<br><br><br>

# 8. 설치 패키지 다운로드 주소
### 1. 필수 환경 설정

"프레시 킵" 실행을 위해 다음 도구들을 선행 설치

* **Python:** 3.9 이상 버전 (https://www.python.org/downloads/)
* **Ollama 서버:** LLM 구동을 위한 서버 (https://ollama.com/download)

### 2. LLM 모델 다운로드

"프레시 킵"은 Ollama 환경에서 특정 모델을 사용

* **사용 모델:** exaone3.5:7.8b
* **다운로드 명령어:**
    ```bash
    ollama pull exaone3.5:7.8b
    ```

### 3. OCR 엔진 설치

"프레시 킵"의 OCR 엔진은 **PaddleOCR** 기반

* **설치 필요 패키지:** PaddlePaddle 프레임워크 및 `paddleocr` 라이브러리
* **다운로드 명령어:**
    ```bash
    # pip install paddlepaddle -i [https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)
    # pip install paddleocr
    ```

