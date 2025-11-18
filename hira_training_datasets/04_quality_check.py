#!/usr/bin/env python3
"""
HIRA 데이터 품질 검증
- 중복 제거
- 길이 검증
- 품질 점수 계산
- 필터링

목표: 고품질 데이터만 선별
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter, defaultdict
import argparse
from datetime import datetime


class QualityChecker:
    """데이터 품질 검증기"""

    def __init__(self, input_path: str):
        """초기화"""
        with open(input_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.filtered_data = []
        self.rejected = []

        self.stats = {
            "initial_count": len(self.data),
            "filtered_count": 0,
            "rejected_count": 0,
            "rejection_reasons": Counter(),
            "quality_scores": []
        }

    def check_all(self, min_score: float = 0.6):
        """전체 품질 검증"""
        print("="*80)
        print("데이터 품질 검증")
        print("="*80 + "\n")

        print(f"입력 데이터: {len(self.data)}개")
        print(f"최소 품질 점수: {min_score}\n")

        # 1. 중복 제거
        print("[1/5] 중복 제거 중...")
        self._remove_duplicates()

        # 2. 길이 검증
        print("[2/5] 길이 검증 중...")
        self._check_lengths()

        # 3. 품질 점수 계산
        print("[3/5] 품질 점수 계산 중...")
        self._calculate_quality_scores()

        # 4. 필터링
        print("[4/5] 필터링 중...")
        self._filter_by_score(min_score)

        # 5. 최종 정리
        print("[5/5] 최종 정리 중...")
        self._finalize()

        print(f"\n✅ 검증 완료")
        print(f"   통과: {self.stats['filtered_count']}개")
        print(f"   제외: {self.stats['rejected_count']}개")

        return self.filtered_data

    def _remove_duplicates(self):
        """중복 제거"""
        seen_questions = set()
        unique_data = []

        for qa in self.data:
            q = qa["instruction"]

            if q not in seen_questions:
                seen_questions.add(q)
                unique_data.append(qa)
            else:
                self.rejected.append({
                    "data": qa,
                    "reason": "duplicate_question"
                })

        duplicates = len(self.data) - len(unique_data)
        print(f"   제거된 중복: {duplicates}개")
        print(f"   남은 데이터: {len(unique_data)}개")

        self.data = unique_data
        self.stats["rejection_reasons"]["duplicate"] = duplicates

    def _check_lengths(self):
        """길이 검증"""
        valid_data = []

        for qa in self.data:
            q_len = len(qa["instruction"])
            a_len = len(qa["output"])

            # 길이 기준: 질문 5-100자, 답변 20-500자
            if 5 <= q_len <= 100 and 20 <= a_len <= 500:
                valid_data.append(qa)
            else:
                self.rejected.append({
                    "data": qa,
                    "reason": f"length_invalid (Q:{q_len}, A:{a_len})"
                })

        rejected = len(self.data) - len(valid_data)
        print(f"   길이 부적합: {rejected}개")
        print(f"   남은 데이터: {len(valid_data)}개")

        self.data = valid_data
        self.stats["rejection_reasons"]["length"] = rejected

    def _calculate_quality_scores(self):
        """품질 점수 계산"""
        for qa in self.data:
            score = self._calculate_score(qa)
            qa["metadata"]["quality_score"] = score
            self.stats["quality_scores"].append(score)

        avg_score = sum(self.stats["quality_scores"]) / len(self.stats["quality_scores"])
        print(f"   평균 품질 점수: {avg_score:.3f}")

    def _calculate_score(self, qa: Dict) -> float:
        """개별 품질 점수 계산"""
        score = 1.0
        question = qa["instruction"]
        answer = qa["output"]

        # 1. 질문 품질 (0.4)
        q_score = 0.0

        # 질문 길이 적정성
        q_len = len(question)
        if 10 <= q_len <= 30:
            q_score += 0.15
        elif 5 <= q_len < 10 or 30 < q_len <= 50:
            q_score += 0.10
        else:
            q_score += 0.05

        # 질문 부호 존재
        if '?' in question or '요' in question[-2:]:
            q_score += 0.10
        else:
            q_score -= 0.05

        # 질문 명확성 (의문사 존재)
        interrogatives = ['어떻게', '뭔가요', '무엇', '어디서', '언제', '왜', '누가']
        if any(word in question for word in interrogatives):
            q_score += 0.10

        # 중복 단어 체크
        words = question.split()
        if len(words) != len(set(words)):
            q_score -= 0.05

        # 2. 답변 품질 (0.4)
        a_score = 0.0

        # 답변 길이 적정성
        a_len = len(answer)
        if 50 <= a_len <= 200:
            a_score += 0.15
        elif 20 <= a_len < 50 or 200 < a_len <= 350:
            a_score += 0.10
        else:
            a_score += 0.05

        # 답변 구조성
        if '습니다' in answer or '됩니다' in answer:
            a_score += 0.10

        # 메뉴 경로 포함
        if '>' in answer or '메뉴' in answer:
            a_score += 0.10

        # 예시 포함
        if '예:' in answer or '예를 들어' in answer:
            a_score += 0.05

        # 3. 일관성 (0.2)
        c_score = 0.0

        # Q-A 키워드 일치
        q_keywords = set(re.findall(r'[가-힣]{2,}', question))
        a_keywords = set(re.findall(r'[가-힣]{2,}', answer))

        overlap = len(q_keywords & a_keywords)
        if overlap >= 2:
            c_score += 0.15
        elif overlap == 1:
            c_score += 0.10
        else:
            c_score += 0.05

        # Q에 있는 주요 키워드가 A에도 있는지
        important_words = ['데이터', '신청', '통계', '코드', 'API', '분석']
        for word in important_words:
            if word in question and word in answer:
                c_score += 0.05
                break

        # 최종 점수
        final_score = max(0.0, min(1.0, q_score + a_score + c_score))

        return final_score

    def _filter_by_score(self, min_score: float):
        """점수 기준 필터링"""
        filtered = []

        for qa in self.data:
            score = qa["metadata"]["quality_score"]

            if score >= min_score:
                filtered.append(qa)
            else:
                self.rejected.append({
                    "data": qa,
                    "reason": f"low_quality_score ({score:.3f})"
                })

        rejected = len(self.data) - len(filtered)
        print(f"   낮은 품질 점수: {rejected}개")
        print(f"   남은 데이터: {len(filtered)}개")

        self.filtered_data = filtered
        self.stats["filtered_count"] = len(filtered)
        self.stats["rejected_count"] = self.stats["initial_count"] - self.stats["filtered_count"]
        self.stats["rejection_reasons"]["low_score"] = rejected

    def _finalize(self):
        """최종 정리"""
        # ID 재부여
        for idx, qa in enumerate(self.filtered_data):
            menu = qa["metadata"]["menu"]
            qa["id"] = f"hira_{menu}_{idx:05d}"

        print(f"   최종 데이터: {len(self.filtered_data)}개")

    def save_data(self, output_path: str):
        """필터링된 데이터 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.filtered_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 필터링 데이터 저장: {output_path}")
        print(f"   파일 크기: {output_path.stat().st_size:,} bytes")

    def save_report(self, output_path: str):
        """품질 리포트 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "summary": {
                "initial_count": self.stats["initial_count"],
                "filtered_count": self.stats["filtered_count"],
                "rejected_count": self.stats["rejected_count"],
                "pass_rate": self.stats["filtered_count"] / self.stats["initial_count"],
            },
            "quality_scores": {
                "average": sum(self.stats["quality_scores"]) / len(self.stats["quality_scores"]) if self.stats["quality_scores"] else 0,
                "min": min(self.stats["quality_scores"]) if self.stats["quality_scores"] else 0,
                "max": max(self.stats["quality_scores"]) if self.stats["quality_scores"] else 0,
                "distribution": {
                    "excellent (0.9-1.0)": sum(1 for s in self.stats["quality_scores"] if s >= 0.9),
                    "good (0.8-0.9)": sum(1 for s in self.stats["quality_scores"] if 0.8 <= s < 0.9),
                    "fair (0.7-0.8)": sum(1 for s in self.stats["quality_scores"] if 0.7 <= s < 0.8),
                    "acceptable (0.6-0.7)": sum(1 for s in self.stats["quality_scores"] if 0.6 <= s < 0.7),
                    "poor (<0.6)": sum(1 for s in self.stats["quality_scores"] if s < 0.6),
                }
            },
            "rejection_reasons": dict(self.stats["rejection_reasons"]),
            "timestamp": datetime.now().isoformat()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 품질 리포트 저장: {output_path}")

    def print_statistics(self):
        """통계 출력"""
        print("\n" + "="*80)
        print("📊 품질 검증 통계")
        print("="*80)

        print(f"\n전체:")
        print(f"  입력: {self.stats['initial_count']}개")
        print(f"  통과: {self.stats['filtered_count']}개")
        print(f"  제외: {self.stats['rejected_count']}개")
        print(f"  통과율: {self.stats['filtered_count']/self.stats['initial_count']*100:.1f}%")

        print(f"\n제외 사유:")
        for reason, count in self.stats["rejection_reasons"].most_common():
            pct = (count / self.stats['rejected_count']) * 100 if self.stats['rejected_count'] else 0
            print(f"  {reason:20s}: {count:4d}개 ({pct:5.1f}%)")

        print(f"\n품질 점수 분포:")
        if self.stats["quality_scores"]:
            avg = sum(self.stats["quality_scores"]) / len(self.stats["quality_scores"])
            print(f"  평균: {avg:.3f}")
            print(f"  최소: {min(self.stats['quality_scores']):.3f}")
            print(f"  최대: {max(self.stats['quality_scores']):.3f}")

            bins = {
                "우수 (0.9-1.0)": sum(1 for s in self.stats["quality_scores"] if s >= 0.9),
                "양호 (0.8-0.9)": sum(1 for s in self.stats["quality_scores"] if 0.8 <= s < 0.9),
                "보통 (0.7-0.8)": sum(1 for s in self.stats["quality_scores"] if 0.7 <= s < 0.8),
                "허용 (0.6-0.7)": sum(1 for s in self.stats["quality_scores"] if 0.6 <= s < 0.7),
            }

            for grade, count in bins.items():
                pct = (count / len(self.stats["quality_scores"])) * 100
                print(f"  {grade:15s}: {count:4d}개 ({pct:5.1f}%)")


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(description="HIRA 데이터 품질 검증")
    parser.add_argument("--input", type=str,
                       default="output/temp/template_generated.json",
                       help="입력 파일")
    parser.add_argument("--output", type=str,
                       default="output/temp/quality_filtered.json",
                       help="출력 파일 (필터링된 데이터)")
    parser.add_argument("--report", type=str,
                       default="output/v1.0/metadata/quality_report.json",
                       help="품질 리포트 파일")
    parser.add_argument("--min-score", type=float, default=0.6,
                       help="최소 품질 점수 (default: 0.6)")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("HIRA 데이터 품질 검증기 v1.0")
    print("="*80 + "\n")

    # 경로 설정
    base_dir = Path(__file__).parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output
    report_path = base_dir / args.report

    # 검증기 초기화
    checker = QualityChecker(input_path)

    # 검증 실행
    filtered_data = checker.check_all(min_score=args.min_score)

    # 저장
    checker.save_data(output_path)
    checker.save_report(report_path)

    # 통계
    checker.print_statistics()

    print("\n" + "="*80)
    print("🎉 품질 검증 완료!")
    print("="*80)
    print(f"\n다음 단계: 데이터셋 분할")
    print(f"python3 05_split_dataset.py --input {output_path}")


if __name__ == "__main__":
    main()
