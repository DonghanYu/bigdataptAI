#!/usr/bin/env python3
"""
HIRA 소스 데이터 분석
- 현재 데이터 통계
- 메뉴/주제별 분포
- 질문/답변 길이 분석
- 부족한 영역 식별
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List
import re


class HIRADataAnalyzer:
    """HIRA 데이터 분석기"""

    def __init__(self, source_path: str):
        """초기화"""
        self.source_path = Path(source_path)

        with open(self.source_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.stats = {
            "overview": {},
            "menu_distribution": {},
            "topic_distribution": {},
            "question_analysis": {},
            "answer_analysis": {},
            "pattern_analysis": {},
            "gaps": []
        }

    def analyze_all(self):
        """전체 분석 실행"""
        print("="*80)
        print("HIRA 소스 데이터 분석")
        print("="*80 + "\n")

        self.analyze_overview()
        self.analyze_menu_distribution()
        self.analyze_questions()
        self.analyze_answers()
        self.analyze_patterns()
        self.identify_gaps()

        print("\n" + "="*80)
        print("✅ 분석 완료!")
        print("="*80)

        return self.stats

    def analyze_overview(self):
        """전체 개요 분석"""
        print("[1/6] 전체 개요 분석 중...")

        total_menus = len(self.data.get("menu_structure", {}))
        total_topics = sum(
            menu["topics_count"]
            for menu in self.data.get("menu_structure", {}).values()
        )
        total_qa = sum(
            qa_group["qa_count"]
            for qa_group in self.data.get("core_qa", {}).values()
        )

        self.stats["overview"] = {
            "total_menus": total_menus,
            "total_topics": total_topics,
            "total_qa_pairs": total_qa,
            "avg_qa_per_menu": total_qa / total_menus if total_menus else 0,
            "avg_qa_per_topic": total_qa / total_topics if total_topics else 0
        }

        print(f"   메뉴: {total_menus}개")
        print(f"   주제: {total_topics}개")
        print(f"   Q&A: {total_qa}쌍")
        print(f"   메뉴당 평균: {self.stats['overview']['avg_qa_per_menu']:.1f}개")
        print(f"   주제당 평균: {self.stats['overview']['avg_qa_per_topic']:.1f}개")

    def analyze_menu_distribution(self):
        """메뉴별 분포 분석"""
        print("\n[2/6] 메뉴별 분포 분석 중...")

        menu_dist = {}

        for menu_id, qa_group in self.data.get("core_qa", {}).items():
            menu_name = self.data["menu_structure"][menu_id]["name"]
            qa_count = qa_group["qa_count"]
            topics_count = self.data["menu_structure"][menu_id]["topics_count"]

            menu_dist[menu_id] = {
                "name": menu_name,
                "qa_count": qa_count,
                "topics_count": topics_count,
                "qa_per_topic": qa_count / topics_count if topics_count else 0
            }

        self.stats["menu_distribution"] = menu_dist

        # 정렬 (Q&A 수 기준)
        sorted_menus = sorted(
            menu_dist.items(),
            key=lambda x: x[1]["qa_count"],
            reverse=True
        )

        print(f"\n   {'메뉴':<20} {'Q&A':<10} {'주제':<10} {'주제당 Q&A':<15}")
        print("   " + "-"*55)

        for menu_id, info in sorted_menus:
            print(f"   {info['name']:<20} {info['qa_count']:<10} "
                  f"{info['topics_count']:<10} {info['qa_per_topic']:<15.1f}")

    def analyze_questions(self):
        """질문 분석"""
        print("\n[3/6] 질문 분석 중...")

        all_questions = []
        question_starts = []
        question_types = Counter()

        for qa_group in self.data.get("core_qa", {}).values():
            for qa in qa_group["qa_pairs"]:
                q = qa["question"]
                all_questions.append(q)

                # 시작 단어
                first_word = q.split()[0] if q.split() else ""
                question_starts.append(first_word)

                # 질문 유형 분류
                if any(word in q for word in ["어떻게", "방법", "절차"]):
                    question_types["how_to"] += 1
                elif any(word in q for word in ["뭔가요", "무엇", "이란"]):
                    question_types["what_is"] += 1
                elif any(word in q for word in ["어디서", "어디에", "어느"]):
                    question_types["where"] += 1
                elif any(word in q for word in ["차이", "다른", "구분"]):
                    question_types["comparison"] += 1
                else:
                    question_types["other"] += 1

        lengths = [len(q) for q in all_questions]

        self.stats["question_analysis"] = {
            "total": len(all_questions),
            "length_min": min(lengths),
            "length_max": max(lengths),
            "length_avg": sum(lengths) / len(lengths),
            "top_starts": Counter(question_starts).most_common(10),
            "types": dict(question_types)
        }

        print(f"   총 질문: {len(all_questions)}개")
        print(f"   길이: 최소 {min(lengths)}자, 최대 {max(lengths)}자, 평균 {self.stats['question_analysis']['length_avg']:.1f}자")
        print(f"\n   질문 유형:")
        for qtype, count in question_types.most_common():
            pct = (count / len(all_questions)) * 100
            print(f"      {qtype}: {count}개 ({pct:.1f}%)")

        print(f"\n   자주 사용되는 시작 단어 (Top 5):")
        for word, count in self.stats["question_analysis"]["top_starts"][:5]:
            print(f"      {word}: {count}회")

    def analyze_answers(self):
        """답변 분석"""
        print("\n[4/6] 답변 분석 중...")

        all_answers = []

        for qa_group in self.data.get("core_qa", {}).values():
            for qa in qa_group["qa_pairs"]:
                all_answers.append(qa["answer"])

        lengths = [len(a) for a in all_answers]

        # 문장 구조 분석
        has_examples = sum(1 for a in all_answers if "예:" in a or "예를 들어" in a)
        has_steps = sum(1 for a in all_answers if any(str(i) in a for i in range(1, 6)))
        has_links = sum(1 for a in all_answers if ">" in a)  # 메뉴 경로

        self.stats["answer_analysis"] = {
            "total": len(all_answers),
            "length_min": min(lengths),
            "length_max": max(lengths),
            "length_avg": sum(lengths) / len(lengths),
            "has_examples": has_examples,
            "has_steps": has_steps,
            "has_menu_paths": has_links
        }

        print(f"   총 답변: {len(all_answers)}개")
        print(f"   길이: 최소 {min(lengths)}자, 최대 {max(lengths)}자, 평균 {self.stats['answer_analysis']['length_avg']:.1f}자")
        print(f"   예시 포함: {has_examples}개 ({has_examples/len(all_answers)*100:.1f}%)")
        print(f"   단계 설명: {has_steps}개 ({has_steps/len(all_answers)*100:.1f}%)")
        print(f"   메뉴 경로: {has_links}개 ({has_links/len(all_answers)*100:.1f}%)")

    def analyze_patterns(self):
        """패턴 분석"""
        print("\n[5/6] 패턴 분석 중...")

        # 키워드 빈도
        all_text = []
        for qa_group in self.data.get("core_qa", {}).values():
            for qa in qa_group["qa_pairs"]:
                all_text.append(qa["question"] + " " + qa["answer"])

        # 주요 키워드 추출
        keywords = []
        common_words = ["은", "는", "이", "가", "을", "를", "에", "의", "와", "과",
                       "로", "으로", "에서", "하나요", "뭔가요", "어떻게", "입니다",
                       "있습니다", "됩니다", "할", "수", "있는", "대한"]

        for text in all_text:
            words = re.findall(r'[가-힣]+', text)
            keywords.extend([w for w in words if len(w) >= 2 and w not in common_words])

        keyword_freq = Counter(keywords).most_common(30)

        self.stats["pattern_analysis"] = {
            "top_keywords": keyword_freq[:20]
        }

        print(f"   주요 키워드 (Top 10):")
        for word, count in keyword_freq[:10]:
            print(f"      {word}: {count}회")

    def identify_gaps(self):
        """부족한 영역 식별"""
        print("\n[6/6] 부족한 영역 식별 중...")

        gaps = []

        # 메뉴별 Q&A 수 확인
        for menu_id, info in self.stats["menu_distribution"].items():
            if info["qa_count"] < 50:
                gaps.append({
                    "type": "low_menu_coverage",
                    "menu": info["name"],
                    "current": info["qa_count"],
                    "recommended": 100,
                    "priority": "high"
                })
            elif info["qa_count"] < 80:
                gaps.append({
                    "type": "medium_menu_coverage",
                    "menu": info["name"],
                    "current": info["qa_count"],
                    "recommended": 150,
                    "priority": "medium"
                })

        # 질문 유형 불균형 확인
        qtypes = self.stats["question_analysis"]["types"]
        total_q = sum(qtypes.values())

        for qtype, count in qtypes.items():
            ratio = count / total_q
            if ratio < 0.1:  # 10% 미만
                gaps.append({
                    "type": "low_question_type",
                    "question_type": qtype,
                    "current": count,
                    "current_ratio": f"{ratio*100:.1f}%",
                    "recommended": int(total_q * 0.15),
                    "priority": "low"
                })

        self.stats["gaps"] = gaps

        if gaps:
            print(f"   발견된 부족 영역: {len(gaps)}개")
            print(f"\n   {'유형':<20} {'영역':<20} {'현재':<10} {'권장':<10} {'우선순위':<10}")
            print("   " + "-"*70)
            for gap in gaps[:10]:
                area = gap.get("menu") or gap.get("question_type", "N/A")
                print(f"   {gap['type']:<20} {area:<20} {gap['current']:<10} "
                      f"{gap['recommended']:<10} {gap['priority']:<10}")
        else:
            print("   부족한 영역 없음 (균형 잡힌 데이터)")

    def save_report(self, output_path: str):
        """분석 리포트 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 분석 리포트 저장: {output_path}")

    def print_summary(self):
        """요약 출력"""
        print("\n" + "="*80)
        print("📊 분석 요약")
        print("="*80)

        print(f"\n✅ 현재 데이터:")
        print(f"   - 총 Q&A: {self.stats['overview']['total_qa_pairs']}쌍")
        print(f"   - 메뉴: {self.stats['overview']['total_menus']}개")
        print(f"   - 주제: {self.stats['overview']['total_topics']}개")

        print(f"\n📈 증강 목표 (Option B):")
        print(f"   - 목표 Q&A: 5,000쌍")
        print(f"   - 필요 증강: {5000 - self.stats['overview']['total_qa_pairs']}쌍")
        print(f"   - 증강 배율: {5000 / self.stats['overview']['total_qa_pairs']:.1f}x")

        print(f"\n⚠️ 주의 영역:")
        high_priority = [g for g in self.stats["gaps"] if g["priority"] == "high"]
        if high_priority:
            for gap in high_priority[:3]:
                area = gap.get("menu") or gap.get("question_type", "")
                print(f"   - {area}: {gap['current']}개 → {gap['recommended']}개 권장")
        else:
            print(f"   - 없음 (균형 잡힌 데이터)")

        print(f"\n🎯 다음 단계:")
        print(f"   1. 규칙 기반 증강: 323 → 2,000개 (6배)")
        print(f"   2. 템플릿 기반 생성: 2,000 → 5,000개 (2.5배)")
        print(f"   3. 품질 검증 및 필터링")


def main():
    """메인 실행"""
    print("\n" + "="*80)
    print("HIRA 소스 데이터 분석기 v1.0")
    print("="*80 + "\n")

    # 소스 데이터 경로
    source_path = Path(__file__).parent / "source_data" / "hira_source.json"

    if not source_path.exists():
        print(f"❌ 소스 데이터를 찾을 수 없습니다: {source_path}")
        print(f"\n다음 명령으로 소스 데이터를 복사하세요:")
        print(f"cp ../hira_crawler/output/hira_data_from_yaml_*.json source_data/hira_source.json")
        sys.exit(1)

    # 분석기 초기화
    analyzer = HIRADataAnalyzer(source_path)

    # 분석 실행
    stats = analyzer.analyze_all()

    # 리포트 저장
    output_dir = Path(__file__).parent / "output" / "v1.0" / "metadata"
    analyzer.save_report(output_dir / "source_analysis.json")

    # 요약 출력
    analyzer.print_summary()

    print("\n" + "="*80)
    print("🎉 분석 완료!")
    print("="*80)


if __name__ == "__main__":
    main()
