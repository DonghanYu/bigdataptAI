#!/usr/bin/env python3
"""
HIRA 오픈데이터 포털 Selenium 크롤러
URL: https://opendata.hira.or.kr/home.do
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


class HIRACrawler:
    """HIRA 오픈데이터 포털 크롤러"""

    def __init__(self, headless: bool = True, timeout: int = 10):
        """
        Args:
            headless: 헤드리스 모드 사용 여부
            timeout: 페이지 로딩 대기 시간 (초)
        """
        self.base_url = "https://opendata.hira.or.kr"
        self.timeout = timeout
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, timeout)

        # 수집된 데이터 저장
        self.data = {
            "site_info": {
                "url": self.base_url,
                "crawled_at": datetime.now().isoformat(),
                "crawler_version": "1.0.0"
            },
            "menus": [],
            "pages": [],
            "statistics": {}
        }

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        """Chrome 드라이버 초기화"""
        options = Options()

        if headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

        # User-Agent 설정 (403 우회)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 기타 옵션
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def crawl(self):
        """전체 크롤링 실행"""
        print("="*80)
        print("HIRA 오픈데이터 포털 크롤링 시작")
        print("="*80)

        try:
            # 1. 홈페이지 접속
            print(f"\n[1/5] 홈페이지 접속: {self.base_url}/home.do")
            self._access_homepage()

            # 2. 메뉴 구조 수집
            print("\n[2/5] 메뉴 구조 수집 중...")
            self._collect_menu_structure()

            # 3. 주요 페이지 크롤링
            print("\n[3/5] 주요 페이지 크롤링 중...")
            self._crawl_main_pages()

            # 4. 통계 정보 수집
            print("\n[4/5] 통계 정보 수집 중...")
            self._collect_statistics()

            # 5. 데이터 정리
            print("\n[5/5] 데이터 정리 중...")
            self._finalize_data()

            print("\n" + "="*80)
            print("✅ 크롤링 완료!")
            print("="*80)

        except Exception as e:
            print(f"\n❌ 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.driver.quit()

    def _access_homepage(self):
        """홈페이지 접속"""
        self.driver.get(f"{self.base_url}/home.do")
        time.sleep(3)  # 페이지 로딩 대기

        # 페이지 제목 확인
        page_title = self.driver.title
        print(f"   페이지 제목: {page_title}")

        # 스크린샷 저장 (디버깅용)
        screenshot_path = Path("/home/user/bigdataptAI/hira_crawler/screenshots")
        screenshot_path.mkdir(exist_ok=True)
        self.driver.save_screenshot(str(screenshot_path / "homepage.png"))
        print(f"   스크린샷 저장: screenshots/homepage.png")

    def _collect_menu_structure(self):
        """메뉴 구조 수집"""
        try:
            # HTML 파싱
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # 메뉴 찾기 (여러 선택자 시도)
            menu_selectors = [
                'nav ul.menu',
                'div.gnb ul',
                'ul.nav',
                'header nav ul',
                'div[id*="menu"] ul',
                'div[class*="menu"] ul',
                'nav li',
            ]

            menus_found = []

            for selector in menu_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"   발견된 메뉴 요소: {selector} ({len(elements)}개)")

                    for idx, elem in enumerate(elements[:10]):  # 처음 10개만
                        menu_text = elem.get_text(strip=True)
                        menu_links = elem.find_all('a')

                        if menu_text and len(menu_text) < 100:  # 너무 긴 텍스트 제외
                            menu_item = {
                                "id": f"menu_{idx}",
                                "text": menu_text,
                                "selector": selector,
                                "links": []
                            }

                            for link in menu_links:
                                href = link.get('href', '')
                                link_text = link.get_text(strip=True)
                                if href and link_text:
                                    menu_item["links"].append({
                                        "text": link_text,
                                        "url": href if href.startswith('http') else f"{self.base_url}{href}"
                                    })

                            if menu_item["links"]:  # 링크가 있는 메뉴만 저장
                                menus_found.append(menu_item)

            # 중복 제거
            unique_menus = []
            seen_texts = set()

            for menu in menus_found:
                if menu["text"] not in seen_texts:
                    unique_menus.append(menu)
                    seen_texts.add(menu["text"])

            self.data["menus"] = unique_menus
            print(f"   수집된 메뉴: {len(unique_menus)}개")

            # 샘플 출력
            for menu in unique_menus[:3]:
                print(f"      - {menu['text']} ({len(menu['links'])}개 링크)")

        except Exception as e:
            print(f"   ⚠️ 메뉴 수집 오류: {e}")

    def _crawl_main_pages(self):
        """주요 페이지 크롤링"""
        # 주요 페이지 URL 목록
        main_pages = [
            {"path": "/home.do", "name": "홈"},
            {"path": "/data/datalist.do", "name": "데이터 목록"},
            {"path": "/stat/statlist.do", "name": "통계 목록"},
            {"path": "/openapi/list.do", "name": "Open API"},
            {"path": "/guide/guide.do", "name": "이용안내"},
        ]

        for page in main_pages:
            try:
                url = f"{self.base_url}{page['path']}"
                print(f"   크롤링: {page['name']} - {url}")

                self.driver.get(url)
                time.sleep(2)

                # 페이지 데이터 수집
                page_data = self._extract_page_data(page['name'], url)
                if page_data:
                    self.data["pages"].append(page_data)
                    print(f"      ✓ 수집 완료")

            except Exception as e:
                print(f"      ⚠️ 오류: {e}")
                continue

    def _extract_page_data(self, page_name: str, url: str) -> Optional[Dict]:
        """페이지 데이터 추출"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # 제목 추출
            title = self.driver.title

            # 본문 텍스트 추출
            content_selectors = [
                'div.content',
                'div.main-content',
                'div#content',
                'main',
                'article',
            ]

            content_text = ""
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    content_text = content.get_text(separator='\n', strip=True)[:2000]  # 처음 2000자
                    break

            # 테이블 추출
            tables = []
            for table in soup.find_all('table')[:5]:  # 최대 5개
                table_data = self._extract_table_data(table)
                if table_data:
                    tables.append(table_data)

            # 링크 추출
            links = []
            for link in soup.find_all('a', href=True)[:50]:  # 최대 50개
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if text and len(text) < 100:
                    links.append({
                        "text": text,
                        "url": href if href.startswith('http') else f"{self.base_url}{href}"
                    })

            return {
                "name": page_name,
                "url": url,
                "title": title,
                "content_preview": content_text[:500] if content_text else "",
                "tables_count": len(tables),
                "tables": tables,
                "links_count": len(links),
                "links": links[:10],  # 상위 10개만 저장
                "crawled_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"         페이지 데이터 추출 오류: {e}")
            return None

    def _extract_table_data(self, table) -> Optional[Dict]:
        """테이블 데이터 추출"""
        try:
            headers = []
            rows = []

            # 헤더 추출
            thead = table.find('thead')
            if thead:
                header_cells = thead.find_all(['th', 'td'])
                headers = [cell.get_text(strip=True) for cell in header_cells]

            # 데이터 행 추출
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr')[:10]:  # 최대 10행
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row = [cell.get_text(strip=True) for cell in cells]
                    rows.append(row)

            if rows:
                return {
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows)
                }

        except Exception as e:
            return None

    def _collect_statistics(self):
        """통계 정보 수집"""
        stats = {
            "total_menus": len(self.data["menus"]),
            "total_pages": len(self.data["pages"]),
            "total_links": sum(len(page.get("links", [])) for page in self.data["pages"]),
            "total_tables": sum(page.get("tables_count", 0) for page in self.data["pages"]),
        }

        self.data["statistics"] = stats
        print(f"   메뉴: {stats['total_menus']}개")
        print(f"   페이지: {stats['total_pages']}개")
        print(f"   링크: {stats['total_links']}개")
        print(f"   테이블: {stats['total_tables']}개")

    def _finalize_data(self):
        """데이터 정리 및 최종화"""
        # 중복 제거, 데이터 검증 등
        self.data["site_info"]["completed_at"] = datetime.now().isoformat()
        print("   데이터 정리 완료")

    def save_json(self, output_path: str):
        """JSON 파일로 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ JSON 저장 완료: {output_path}")
        print(f"   파일 크기: {output_path.stat().st_size:,} bytes")

    def save_pretty_json(self, output_path: str):
        """읽기 쉬운 JSON 저장 (요약 포함)"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 요약 데이터 생성
        summary = {
            "crawl_summary": {
                "site": self.base_url,
                "crawled_at": self.data["site_info"]["crawled_at"],
                "completed_at": self.data["site_info"].get("completed_at", ""),
                "statistics": self.data["statistics"]
            },
            "menu_structure": [
                {
                    "id": menu["id"],
                    "name": menu["text"],
                    "links_count": len(menu["links"])
                }
                for menu in self.data["menus"]
            ],
            "pages_overview": [
                {
                    "name": page["name"],
                    "url": page["url"],
                    "title": page["title"],
                    "tables": page["tables_count"],
                    "links": page["links_count"]
                }
                for page in self.data["pages"]
            ],
            "full_data": self.data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"✅ 요약 JSON 저장 완료: {output_path}")


def main():
    """메인 실행 함수"""
    print("\n" + "="*80)
    print("HIRA 오픈데이터 포털 Selenium 크롤러 v1.0")
    print("="*80 + "\n")

    # 크롤러 초기화
    crawler = HIRACrawler(headless=True, timeout=10)

    try:
        # 크롤링 실행
        crawler.crawl()

        # JSON 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("/home/user/bigdataptAI/hira_crawler/output")
        output_dir.mkdir(exist_ok=True)

        # 1. 전체 데이터
        crawler.save_json(output_dir / f"hira_crawled_data_{timestamp}.json")

        # 2. 요약 데이터
        crawler.save_pretty_json(output_dir / f"hira_summary_{timestamp}.json")

        print("\n" + "="*80)
        print("🎉 모든 작업 완료!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 실행 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
