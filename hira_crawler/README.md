# HIRA 오픈데이터 포털 Selenium 크롤러

HIRA 보건의료빅데이터개방시스템(https://opendata.hira.or.kr)의 정보를 자동으로 수집하여 JSON 형식으로 규격화하는 Selenium 기반 크롤러입니다.

## 📋 기능

### 주요 기능
- ✅ **메뉴 구조 자동 수집**: 사이트의 전체 메뉴 및 링크 구조 파악
- ✅ **페이지 데이터 파싱**: 주요 페이지의 텍스트, 테이블, 링크 추출
- ✅ **통계 정보 수집**: 수집된 데이터의 통계 정보 생성
- ✅ **JSON 규격화**: 표준화된 JSON 형식으로 저장
- ✅ **403 우회**: User-Agent 및 헤드리스 모드로 접근 제한 우회

### 수집 데이터
1. **사이트 정보**: URL, 크롤링 시각, 버전
2. **메뉴 구조**: 메뉴 항목, 링크, 계층 구조
3. **페이지 데이터**: 제목, 본문, 테이블, 링크
4. **통계 정보**: 메뉴/페이지/링크/테이블 개수

## 🚀 사용 방법

### 1. 의존성 설치
```bash
pip install selenium beautifulsoup4 lxml
```

### 2. ChromeDriver 확인
```bash
which chromedriver
# /opt/node22/bin/chromedriver
```

### 3. 크롤러 실행
```bash
cd /home/user/bigdataptAI/hira_crawler
python3 hira_selenium_crawler.py
```

### 4. 결과 확인
```bash
# 생성된 JSON 파일 확인
ls -lh output/

# JSON 내용 미리보기
head -50 output/hira_summary_*.json
```

## 📂 출력 파일

### 1. 전체 데이터 (`hira_crawled_data_YYYYMMDD_HHMMSS.json`)
모든 수집된 데이터를 포함하는 완전한 JSON 파일

```json
{
  "site_info": {
    "url": "https://opendata.hira.or.kr",
    "crawled_at": "2025-11-18T12:34:56",
    "crawler_version": "1.0.0"
  },
  "menus": [...],
  "pages": [...],
  "statistics": {...}
}
```

### 2. 요약 데이터 (`hira_summary_YYYYMMDD_HHMMSS.json`)
크롤링 결과 요약 + 전체 데이터

```json
{
  "crawl_summary": {
    "site": "https://opendata.hira.or.kr",
    "statistics": {
      "total_menus": 15,
      "total_pages": 5,
      "total_links": 120,
      "total_tables": 8
    }
  },
  "menu_structure": [...],
  "pages_overview": [...],
  "full_data": {...}
}
```

## 📊 데이터 구조

### 메뉴 항목
```json
{
  "id": "menu_0",
  "text": "서비스 소개",
  "selector": "nav ul.menu",
  "links": [
    {
      "text": "데이터 소개",
      "url": "https://opendata.hira.or.kr/intro/data.do"
    }
  ]
}
```

### 페이지 데이터
```json
{
  "name": "홈",
  "url": "https://opendata.hira.or.kr/home.do",
  "title": "보건의료빅데이터개방시스템",
  "content_preview": "...",
  "tables_count": 2,
  "tables": [...],
  "links_count": 45,
  "links": [...]
}
```

### 테이블 데이터
```json
{
  "headers": ["구분", "데이터명", "기간"],
  "rows": [
    ["환자표본", "2009-2018 환자표본", "2009-2018"],
    ["맞춤형", "전체 데이터", "요청 가능"]
  ],
  "row_count": 2
}
```

## ⚙️ 커스터마이징

### 헤드리스 모드 끄기 (브라우저 표시)
```python
crawler = HIRACrawler(headless=False, timeout=10)
```

### 타임아웃 조정
```python
crawler = HIRACrawler(headless=True, timeout=30)  # 30초
```

### 크롤링할 페이지 추가
`_crawl_main_pages()` 메소드의 `main_pages` 리스트 수정:
```python
main_pages = [
    {"path": "/home.do", "name": "홈"},
    {"path": "/your/path.do", "name": "새 페이지"},  # 추가
]
```

### 데이터 추출 로직 수정
`_extract_page_data()` 메소드에서 CSS 선택자 조정

## 🔧 트러블슈팅

### Q1. 403 Forbidden 에러
**원인**: 사이트가 자동화 요청 차단
**해결**: User-Agent 및 헤드리스 모드 설정 (이미 적용됨)

### Q2. ChromeDriver 오류
**원인**: ChromeDriver가 설치되지 않았거나 PATH에 없음
**해결**:
```bash
which chromedriver
# 없으면 설치 필요
```

### Q3. 메뉴가 수집되지 않음
**원인**: CSS 선택자가 맞지 않음
**해결**: `_collect_menu_structure()`의 `menu_selectors` 리스트 수정

### Q4. 페이지 로딩이 느림
**원인**: 타임아웃 설정이 짧음
**해결**: 타임아웃을 늘리거나 `time.sleep()` 조정

## 📈 성능

### 예상 실행 시간
- 홈페이지 접속: 3-5초
- 메뉴 수집: 2-3초
- 페이지 크롤링 (5개): 10-15초
- **총 소요 시간**: 약 20-30초

### 수집 데이터 규모
- 메뉴: 10-20개
- 페이지: 5개 (확장 가능)
- 링크: 100-200개
- 테이블: 5-10개

## ⚖️ 법적 고려사항

### 주의사항
1. **robots.txt 확인**: 크롤링 허용 여부 확인 필요
2. **이용약관 준수**: 사이트 이용약관 검토
3. **서버 부하 최소화**: 요청 간격 조절
4. **개인정보 보호**: 개인정보가 포함된 데이터 수집 금지

### 권장 사항
- 크롤링 빈도를 최소화 (1일 1-2회)
- 수집한 데이터는 연구/학습 목적으로만 사용
- 상업적 이용 시 HIRA에 문의

## 📚 참고

### 프로젝트 구조
```
hira_crawler/
├── hira_selenium_crawler.py    # 메인 크롤러
├── README.md                    # 문서 (이 파일)
├── output/                      # 크롤링 결과 (JSON)
│   ├── hira_crawled_data_*.json
│   └── hira_summary_*.json
└── screenshots/                 # 디버깅용 스크린샷
    └── homepage.png
```

### 기존 프로젝트와 연동
이 크롤러는 `bigdata_portal_learning/` 프로젝트와 독립적으로 작동하며, 필요시 수집된 JSON 데이터를 학습 데이터 생성에 활용할 수 있습니다.

```bash
# 크롤링 결과를 학습 데이터로 변환 (추후 구현 가능)
python3 convert_crawled_to_training.py \
  --input output/hira_summary_*.json \
  --output ../bigdata_portal_learning/output/
```

## 📝 라이센스

본 크롤러는 HIRA 오픈데이터 포털의 공공 정보 수집 목적으로 제작되었습니다.
수집된 데이터의 저작권은 건강보험심사평가원에 있습니다.

---

**버전**: 1.0.0
**작성일**: 2025-11-18
**상태**: ✅ 테스트 준비 완료
