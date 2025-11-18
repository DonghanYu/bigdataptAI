#!/usr/bin/env python3
"""
HIRA 오픈데이터 포털 Requests 크롤러 (안정적)
URL: https://opendata.hira.or.kr/home.do
"""

import json
import time
import re
import warnings
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# SSL 경고 무시
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class HIRACrawler:
    """HIRA 오픈데이터 포털 크롤러 (Requests)"""

    def __init__(self, timeout: int = 30):
        """
        Args:
            timeout: 요청 대기 시간 (초)
        """
        self.base_url = "https://opendata.hira.or.kr"
        self.timeout = timeout

        # 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

        # 수집된 데이터 저장
        self.data = {
            "site_info": {
                "url": self.base_url,
                "crawled_at": datetime.now().isoformat(),
                "crawler_version": "1.0.0",
                "engine": "Requests"
            },
            "menus": [],
            "pages": [],
            "statistics": {}
        }

    def crawl(self):
        """전체 크롤링 실행"""
        print("="*80)
        print("HIRA 오픈데이터 포털 크롤링 시작 (Requests)")
        print("="*80)

        try:
            # 1. 홈페이지 접속
            print(f"\n[1/5] 홈페이지 접속: {self.base_url}/home.do")
            homepage_html = self._access_homepage()

            if not homepage_html:
                print("   ⚠️ 홈페이지 접속 실패, 제한된 크롤링 진행")

            # 2. 메뉴 구조 수집
            print("\n[2/5] 메뉴 구조 수집 중...")
            if homepage_html:
                self._collect_menu_structure(homepage_html)
            else:
                print("   ⚠️ 건너뜀")

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

    def _access_homepage(self) -> Optional[str]:
        """홈페이지 접속"""
        try:
            url = f"{self.base_url}/home.do"
            response = self.session.get(url, timeout=self.timeout, verify=False)

            print(f"   상태 코드: {response.status_code}")
            print(f"   인코딩: {response.encoding}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")

            if response.status_code == 200:
                print(f"   ✓ 접속 성공! (응답 크기: {len(response.text):,} bytes)")
                return response.text
            else:
                print(f"   ✗ 접속 실패 (상태 코드: {response.status_code})")
                return None

        except requests.exceptions.SSLError as e:
            print(f"   ⚠️ SSL 오류: {e}")
            return None
        except requests.exceptions.Timeout:
            print(f"   ⚠️ 타임아웃 ({self.timeout}초)")
            return None
        except Exception as e:
            print(f"   ⚠️ 오류: {e}")
            return None

    def _collect_menu_structure(self, html: str):
        """메뉴 구조 수집"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 페이지 제목 확인
            title = soup.find('title')
            if title:
                print(f"   페이지 제목: {title.get_text(strip=True)}")

            # 메뉴 찾기 (여러 선택자 시도)
            menu_selectors = [
                'nav ul',
                'div.gnb ul',
                'div.lnb ul',
                'ul.menu',
                'ul.nav',
                'header ul',
                'div[id*="menu"]',
                'div[class*="menu"]',
                '#gnb',
                '.gnb',
                '#header',
                '.header',
            ]

            menus_found = []
            all_links = []

            # 모든 링크 수집 (fallback)
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if text and 2 < len(text) < 80 and href:
                    full_url = href
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            full_url = f"{self.base_url}{href}"
                        elif not href.startswith('#') and not href.startswith('javascript:'):
                            full_url = f"{self.base_url}/{href}"
                        else:
                            continue

                    all_links.append({
                        "text": text,
                        "url": full_url,
                        "original_href": href
                    })

            # 메뉴로 추정되는 링크 필터링
            menu_keywords = ['소개', '데이터', '통계', 'API', '고객', '지원', '자료', '서비스', '분석', '정보']
            menu_links = []

            for link in all_links:
                if any(keyword in link['text'] for keyword in menu_keywords):
                    menu_links.append(link)

            # 중복 제거
            unique_links = []
            seen_urls = set()

            for link in menu_links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])

            # 메뉴 구조 생성
            if unique_links:
                menu_item = {
                    "id": "main_menu",
                    "text": "주요 메뉴",
                    "links": unique_links
                }
                menus_found.append(menu_item)

            self.data["menus"] = menus_found
            print(f"   수집된 메뉴 링크: {len(unique_links)}개")

            # 샘플 출력
            for link in unique_links[:10]:
                print(f"      - {link['text']}")

        except Exception as e:
            print(f"   ⚠️ 메뉴 수집 오류: {e}")
            import traceback
            traceback.print_exc()

    def _crawl_main_pages(self):
        """주요 페이지 크롤링"""
        # 주요 페이지 URL 목록
        main_pages = [
            {"path": "/home.do", "name": "홈"},
            {"path": "/op/opc/selectOpenData.do", "name": "데이터 목록"},
            {"path": "/st/stc/selectStcList.do", "name": "통계 목록"},
            {"path": "/op/opi/selectOpenApiList.do", "name": "Open API"},
            {"path": "/cm/cm_info.do?pgmId=HIRAA010000000000", "name": "서비스 소개"},
            {"path": "/bd/ay/selectBdUseList.do", "name": "빅데이터 활용"},
            {"path": "/cs/ntt/selectBoardList.do?bbsId=BBSMSTR_000000000012", "name": "공지사항"},
        ]

        for page_info in main_pages:
            try:
                url = f"{self.base_url}{page_info['path']}"
                print(f"   크롤링: {page_info['name']}")
                print(f"      URL: {url}")

                # 페이지 요청
                response = self.session.get(url, timeout=self.timeout, verify=False)

                if response.status_code == 200:
                    # 페이지 데이터 수집
                    page_data = self._extract_page_data(response.text, page_info['name'], url)
                    if page_data:
                        self.data["pages"].append(page_data)
                        print(f"      ✓ 수집 완료 (콘텐츠: {page_data.get('content_length', 0):,}자)")
                else:
                    print(f"      ✗ 실패 (상태: {response.status_code})")

                time.sleep(0.5)  # 서버 부하 방지

            except Exception as e:
                print(f"      ⚠️ 오류: {e}")
                continue

    def _extract_page_data(self, html: str, page_name: str, url: str) -> Optional[Dict]:
        """페이지 데이터 추출"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 제목 추출
            title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 본문 텍스트 추출
            content_selectors = [
                'div.content',
                'div.container',
                'div.main-content',
                'div#content',
                'main',
                'article',
                'div.board',
                'div.cont',
            ]

            content_text = ""
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    # 스크립트/스타일 제거
                    for script in content.find_all(['script', 'style']):
                        script.decompose()
                    content_text = content.get_text(separator='\n', strip=True)
                    break

            # 전체 body (fallback)
            if not content_text:
                body = soup.find('body')
                if body:
                    for script in body.find_all(['script', 'style']):
                        script.decompose()
                    content_text = body.get_text(separator='\n', strip=True)

            # 테이블 추출
            tables = []
            for table in soup.find_all('table')[:10]:
                table_data = self._extract_table_data(table)
                if table_data:
                    tables.append(table_data)

            # 링크 추출
            links = []
            for link in soup.find_all('a', href=True)[:100]:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if text and 2 < len(text) < 100 and href:
                    full_url = href
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            full_url = f"{self.base_url}{href}"
                        elif not href.startswith('#') and not href.startswith('javascript:'):
                            full_url = f"{self.base_url}/{href}"
                        else:
                            continue

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
                "content_preview": content_text[:800] if content_text else "",
                "content_length": len(content_text),
                "tables_count": len(tables),
                "tables": tables[:5],  # 최대 5개 테이블만
                "links_count": len(unique_links),
                "links": unique_links[:30],  # 최대 30개 링크
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
                for tr in thead.find_all('tr'):
                    header_cells = tr.find_all(['th', 'td'])
                    if header_cells:
                        headers = [cell.get_text(strip=True) for cell in header_cells if cell.get_text(strip=True)]
                        if headers:
                            break

            # 헤더가 없으면 첫 번째 행 확인
            if not headers:
                first_row = table.find('tr')
                if first_row:
                    header_cells = first_row.find_all('th')
                    if header_cells:
                        headers = [cell.get_text(strip=True) for cell in header_cells]

            # 데이터 행 추출
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr')[:20]:  # 최대 20행
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row = [cell.get_text(strip=True) for cell in cells]
                    # 빈 행이 아니면 추가
                    if any(cell for cell in row):
                        rows.append(row)

            if rows:
                return {
                    "headers": headers,
                    "rows": rows[:15],  # 최대 15행만 저장
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
            "total_content_length": sum(page.get("content_length", 0) for page in self.data["pages"]),
        }

        self.data["statistics"] = stats
        print(f"   메뉴: {stats['total_menus']}개")
        print(f"   메뉴 링크: {stats['total_menu_links']}개")
        print(f"   크롤링 페이지: {stats['total_pages']}개")
        print(f"   수집 링크: {stats['total_links']}개")
        print(f"   수집 테이블: {stats['total_tables']}개")
        print(f"   총 콘텐츠: {stats['total_content_length']:,}자")

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
                "engine": "Requests + BeautifulSoup",
                "statistics": self.data["statistics"]
            },
            "menu_structure": [
                {
                    "id": menu["id"],
                    "name": menu.get("text", "")[:60],
                    "links_count": len(menu.get("links", [])),
                    "sample_links": [
                        {
                            "text": link["text"],
                            "url": link["url"]
                        }
                        for link in menu.get("links", [])[:5]
                    ]
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
    print("HIRA 오픈데이터 포털 Requests 크롤러 v1.0")
    print("="*80 + "\n")

    # 크롤러 초기화
    crawler = HIRACrawler(timeout=30)

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
