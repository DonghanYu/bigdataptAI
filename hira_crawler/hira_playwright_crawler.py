#!/usr/bin/env python3
"""
HIRA 오픈데이터 포털 Playwright 크롤러
URL: https://opendata.hira.or.kr/home.do
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup


class HIRACrawler:
    """HIRA 오픈데이터 포털 크롤러 (Playwright)"""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Args:
            headless: 헤드리스 모드 사용 여부
            timeout: 페이지 로딩 대기 시간 (밀리초)
        """
        self.base_url = "https://opendata.hira.or.kr"
        self.timeout = timeout
        self.headless = headless

        # 수집된 데이터 저장
        self.data = {
            "site_info": {
                "url": self.base_url,
                "crawled_at": datetime.now().isoformat(),
                "crawler_version": "1.0.0",
                "engine": "Playwright"
            },
            "menus": [],
            "pages": [],
            "statistics": {}
        }

    def crawl(self):
        """전체 크롤링 실행"""
        print("="*80)
        print("HIRA 오픈데이터 포털 크롤링 시작 (Playwright)")
        print("="*80)

        with sync_playwright() as p:
            # 브라우저 시작
            browser = p.chromium.launch(headless=self.headless)

            # SSL 인증서 오류 무시
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.set_default_timeout(self.timeout)

            try:
                # 1. 홈페이지 접속
                print(f"\n[1/5] 홈페이지 접속: {self.base_url}/home.do")
                self._access_homepage(page)

                # 2. 메뉴 구조 수집
                print("\n[2/5] 메뉴 구조 수집 중...")
                self._collect_menu_structure(page)

                # 3. 주요 페이지 크롤링
                print("\n[3/5] 주요 페이지 크롤링 중...")
                self._crawl_main_pages(page)

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
                browser.close()

    def _access_homepage(self, page: Page):
        """홈페이지 접속"""
        try:
            page.goto(f"{self.base_url}/home.do", wait_until="networkidle")
            time.sleep(2)  # 추가 대기

            # 페이지 제목 확인
            page_title = page.title()
            print(f"   페이지 제목: {page_title}")

            # 스크린샷 저장
            screenshot_path = Path("/home/user/bigdataptAI/hira_crawler/screenshots")
            screenshot_path.mkdir(exist_ok=True)
            page.screenshot(path=str(screenshot_path / "homepage.png"))
            print(f"   스크린샷 저장: screenshots/homepage.png")

        except Exception as e:
            print(f"   ⚠️ 홈페이지 접속 오류: {e}")
            # 403이어도 계속 진행
            try:
                page.goto(f"{self.base_url}/home.do")
                time.sleep(3)
            except:
                pass

    def _collect_menu_structure(self, page: Page):
        """메뉴 구조 수집"""
        try:
            # HTML 파싱
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # 메뉴 찾기 (여러 선택자 시도)
            menu_selectors = [
                'nav ul.gnb',
                'nav ul',
                'div.gnb ul',
                'ul.menu',
                'header nav ul',
                'div[id*="menu"] ul',
                'div[class*="menu"] ul',
                '#header ul',
                '.header ul',
            ]

            menus_found = []

            for selector in menu_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"   발견된 메뉴 요소: {selector} ({len(elements)}개)")

                    for idx, elem in enumerate(elements[:15]):
                        menu_text = elem.get_text(strip=True)
                        menu_links = elem.find_all('a')

                        # 메뉴로 보이는 것만 (텍스트가 적당히 짧고 링크가 있음)
                        if menu_text and 5 < len(menu_text) < 200 and menu_links:
                            menu_item = {
                                "id": f"menu_{len(menus_found)}",
                                "text": menu_text[:100],
                                "selector": selector,
                                "links": []
                            }

                            for link in menu_links:
                                href = link.get('href', '')
                                link_text = link.get_text(strip=True)
                                if href and link_text and len(link_text) < 50:
                                    full_url = href
                                    if not href.startswith('http'):
                                        if href.startswith('/'):
                                            full_url = f"{self.base_url}{href}"
                                        else:
                                            full_url = f"{self.base_url}/{href}"

                                    menu_item["links"].append({
                                        "text": link_text,
                                        "url": full_url
                                    })

                            if menu_item["links"]:
                                menus_found.append(menu_item)

            # 중복 제거 (텍스트 기준)
            unique_menus = []
            seen_texts = set()

            for menu in menus_found:
                # 첫 50자로 비교
                text_key = menu["text"][:50]
                if text_key not in seen_texts:
                    unique_menus.append(menu)
                    seen_texts.add(text_key)

            self.data["menus"] = unique_menus
            print(f"   수집된 고유 메뉴: {len(unique_menus)}개")

            # 샘플 출력
            for menu in unique_menus[:5]:
                print(f"      - {menu['text'][:40]}... ({len(menu['links'])}개 링크)")

        except Exception as e:
            print(f"   ⚠️ 메뉴 수집 오류: {e}")
            import traceback
            traceback.print_exc()

    def _crawl_main_pages(self, page: Page):
        """주요 페이지 크롤링"""
        # 주요 페이지 URL 목록
        main_pages = [
            {"path": "/home.do", "name": "홈"},
            {"path": "/op/opc/selectOpenData.do", "name": "데이터 목록"},
            {"path": "/st/stc/selectStcList.do", "name": "통계 목록"},
            {"path": "/op/opi/selectOpenApiList.do", "name": "Open API"},
            {"path": "/cm/cm_info.do?pgmId=HIRAA010000000000", "name": "서비스 소개"},
        ]

        for page_info in main_pages:
            try:
                url = f"{self.base_url}{page_info['path']}"
                print(f"   크롤링: {page_info['name']} - {url}")

                # 페이지 이동
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    time.sleep(1)
                except Exception as e:
                    print(f"      ⚠️ 페이지 로딩 오류, 계속 진행: {e}")

                # 페이지 데이터 수집
                page_data = self._extract_page_data(page, page_info['name'], url)
                if page_data:
                    self.data["pages"].append(page_data)
                    print(f"      ✓ 수집 완료")

            except Exception as e:
                print(f"      ⚠️ 크롤링 오류: {e}")
                continue

    def _extract_page_data(self, page: Page, page_name: str, url: str) -> Optional[Dict]:
        """페이지 데이터 추출"""
        try:
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # 제목 추출
            title = page.title()

            # 본문 텍스트 추출
            content_selectors = [
                'div.content',
                'div.container',
                'div.main-content',
                'div#content',
                'main',
                'article',
                'div.board',
            ]

            content_text = ""
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    content_text = content.get_text(separator='\n', strip=True)[:3000]
                    break

            # 전체 텍스트 (fallback)
            if not content_text:
                body = soup.find('body')
                if body:
                    content_text = body.get_text(separator='\n', strip=True)[:3000]

            # 테이블 추출
            tables = []
            for table in soup.find_all('table')[:5]:
                table_data = self._extract_table_data(table)
                if table_data:
                    tables.append(table_data)

            # 링크 추출
            links = []
            for link in soup.find_all('a', href=True)[:100]:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if text and 3 < len(text) < 100:
                    full_url = href
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            full_url = f"{self.base_url}{href}"
                        else:
                            full_url = f"{self.base_url}/{href}"

                    links.append({
                        "text": text,
                        "url": full_url
                    })

            # 중복 링크 제거
            unique_links = []
            seen_urls = set()
            for link in links:
                if link["url"] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link["url"])

            return {
                "name": page_name,
                "url": url,
                "title": title,
                "content_preview": content_text[:500] if content_text else "",
                "content_length": len(content_text),
                "tables_count": len(tables),
                "tables": tables,
                "links_count": len(unique_links),
                "links": unique_links[:20],  # 상위 20개만 저장
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
                headers = [cell.get_text(strip=True) for cell in header_cells if cell.get_text(strip=True)]

            # 헤더가 없으면 첫 번째 행을 헤더로
            if not headers:
                first_row = table.find('tr')
                if first_row:
                    header_cells = first_row.find_all(['th', 'td'])
                    if header_cells and all(cell.name == 'th' for cell in header_cells):
                        headers = [cell.get_text(strip=True) for cell in header_cells]

            # 데이터 행 추출
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr')[:15]:  # 최대 15행
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row = [cell.get_text(strip=True) for cell in cells]
                    # 빈 행이 아니면 추가
                    if any(cell for cell in row):
                        rows.append(row)

            if rows:
                return {
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows),
                    "column_count": len(rows[0]) if rows else 0
                }

            return None

        except Exception as e:
            return None

    def _collect_statistics(self):
        """통계 정보 수집"""
        stats = {
            "total_menus": len(self.data["menus"]),
            "total_pages": len(self.data["pages"]),
            "total_links": sum(page.get("links_count", 0) for page in self.data["pages"]),
            "total_tables": sum(page.get("tables_count", 0) for page in self.data["pages"]),
            "total_menu_links": sum(len(menu.get("links", [])) for menu in self.data["menus"]),
        }

        self.data["statistics"] = stats
        print(f"   메뉴: {stats['total_menus']}개")
        print(f"   메뉴 링크: {stats['total_menu_links']}개")
        print(f"   페이지: {stats['total_pages']}개")
        print(f"   페이지 링크: {stats['total_links']}개")
        print(f"   테이블: {stats['total_tables']}개")

    def _finalize_data(self):
        """데이터 정리 및 최종화"""
        self.data["site_info"]["completed_at"] = datetime.now().isoformat()
        print("   데이터 정리 완료")

    def save_json(self, output_path: str):
        """JSON 파일로 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size
        print(f"\n✅ JSON 저장 완료: {output_path}")
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")

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
                "engine": "Playwright",
                "statistics": self.data["statistics"]
            },
            "menu_structure": [
                {
                    "id": menu["id"],
                    "name": menu["text"][:60],
                    "links_count": len(menu["links"]),
                    "sample_links": menu["links"][:3]
                }
                for menu in self.data["menus"]
            ],
            "pages_overview": [
                {
                    "name": page["name"],
                    "url": page["url"],
                    "title": page["title"],
                    "content_length": page.get("content_length", 0),
                    "tables": page["tables_count"],
                    "links": page["links_count"]
                }
                for page in self.data["pages"]
            ],
            "full_data": self.data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size
        print(f"✅ 요약 JSON 저장 완료: {output_path}")
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")


def main():
    """메인 실행 함수"""
    print("\n" + "="*80)
    print("HIRA 오픈데이터 포털 Playwright 크롤러 v1.0")
    print("="*80 + "\n")

    # 크롤러 초기화
    crawler = HIRACrawler(headless=True, timeout=30000)

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
