#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 품질 검증 스크립트
중복 제거, 유효성 체크, 통계 분석
"""

import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple

class DataQualityValidator:
    def __init__(self, data_path: str):
        """
        품질 검증기 초기화

        Args:
            data_path: 검증할 JSONL 파일 경로
        """
        self.data_path = Path(data_path)
        self.data = []
        self.load_data()

    def load_data(self):
        """데이터 로드"""
        print(f"데이터 로드 중: {self.data_path}")

        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    self.data.append(item)
                except:
                    continue

        print(f"✅ 로드 완료: {len(self.data):,}건\n")

    def check_duplicates(self) -> Tuple[int, List[str]]:
        """중복 체크"""
        print("="*80)
        print("1️⃣  중복 체크")
        print("="*80)

        questions = [item['instruction'] for item in self.data]
        question_counts = Counter(questions)

        duplicates = {q: count for q, count in question_counts.items() if count > 1}

        if duplicates:
            print(f"⚠️  중복 발견: {len(duplicates)}개 질문이 중복됨")
            print("\n[중복 질문 TOP 10]")
            for i, (q, count) in enumerate(sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10], 1):
                print(f"  {i}. ({count}번) {q}")
        else:
            print("✅ 중복 없음: 모든 질문이 고유합니다")

        return len(duplicates), list(duplicates.keys())

    def check_length(self):
        """길이 체크"""
        print("\n" + "="*80)
        print("2️⃣  길이 체크")
        print("="*80)

        q_lengths = [len(item['instruction']) for item in self.data]
        a_lengths = [len(item['output']) for item in self.data]

        print(f"\n[질문 길이]")
        print(f"  평균: {sum(q_lengths) / len(q_lengths):.1f}자")
        print(f"  최소: {min(q_lengths)}자")
        print(f"  최대: {max(q_lengths)}자")
        print(f"  중앙값: {sorted(q_lengths)[len(q_lengths)//2]}자")

        # 너무 짧거나 긴 질문
        too_short = [item for item in self.data if len(item['instruction']) < 5]
        too_long = [item for item in self.data if len(item['instruction']) > 100]

        if too_short:
            print(f"\n  ⚠️  너무 짧은 질문 ({len(too_short)}건): 5자 미만")
            for item in too_short[:3]:
                print(f"     - {item['instruction']}")

        if too_long:
            print(f"\n  ⚠️  너무 긴 질문 ({len(too_long)}건): 100자 초과")
            for item in too_long[:3]:
                print(f"     - {item['instruction'][:80]}...")

        print(f"\n[답변 길이]")
        print(f"  평균: {sum(a_lengths) / len(a_lengths):.1f}자")
        print(f"  최소: {min(a_lengths)}자")
        print(f"  최대: {max(a_lengths)}자")
        print(f"  중앙값: {sorted(a_lengths)[len(a_lengths)//2]}자")

        # 너무 짧거나 긴 답변
        too_short_a = [item for item in self.data if len(item['output']) < 30]
        too_long_a = [item for item in self.data if len(item['output']) > 500]

        if too_short_a:
            print(f"\n  ⚠️  너무 짧은 답변 ({len(too_short_a)}건): 30자 미만")
            for item in too_short_a[:3]:
                print(f"     Q: {item['instruction']}")
                print(f"     A: {item['output']}\n")

        if too_long_a:
            print(f"\n  ⚠️  너무 긴 답변 ({len(too_long_a)}건): 500자 초과")

    def check_quality(self):
        """품질 체크"""
        print("\n" + "="*80)
        print("3️⃣  품질 체크")
        print("="*80)

        issues = []

        # 1. 빈 답변 체크
        empty_output = [item for item in self.data if not item.get('output', '').strip()]
        if empty_output:
            issues.append(f"빈 답변: {len(empty_output)}건")

        # 2. 빈 질문 체크
        empty_instruction = [item for item in self.data if not item.get('instruction', '').strip()]
        if empty_instruction:
            issues.append(f"빈 질문: {len(empty_instruction)}건")

        # 3. 질문과 답변이 동일한 경우
        same_qa = [item for item in self.data if item.get('instruction', '') == item.get('output', '')]
        if same_qa:
            issues.append(f"질문=답변: {len(same_qa)}건")

        # 4. 템플릿 문구가 그대로 남아있는 경우
        template_remaining = []
        for item in self.data:
            if '{' in item['instruction'] or '}' in item['instruction']:
                template_remaining.append(item)
            if '{' in item['output'] or '}' in item['output']:
                template_remaining.append(item)

        if template_remaining:
            issues.append(f"템플릿 미치환: {len(template_remaining)}건")
            print(f"\n  ⚠️  템플릿 문구 미치환 샘플:")
            for item in template_remaining[:3]:
                print(f"     Q: {item['instruction']}")
                print(f"     A: {item['output'][:80]}...\n")

        # 5. 기본 답변 비율 체크 (fallback 답변)
        fallback_pattern = "빅데이터개방포털의 해당 메뉴에서 이용하실 수 있습니다"
        fallback_count = sum(1 for item in self.data if fallback_pattern in item['output'])
        fallback_ratio = (fallback_count / len(self.data)) * 100

        print(f"\n[품질 지표]")
        print(f"  빈 답변: {len(empty_output)}건")
        print(f"  빈 질문: {len(empty_instruction)}건")
        print(f"  질문=답변: {len(same_qa)}건")
        print(f"  템플릿 미치환: {len(template_remaining)}건")
        print(f"  기본 답변 비율: {fallback_ratio:.1f}% ({fallback_count:,}/{len(self.data):,}건)")

        if fallback_ratio > 30:
            print(f"    ⚠️  기본 답변이 너무 많습니다 (30% 초과)")

        if not issues:
            print("\n✅ 품질 문제 없음")
        else:
            print(f"\n⚠️  발견된 문제: {len(issues)}개")
            for issue in issues:
                print(f"  - {issue}")

        return issues

    def check_variety(self):
        """다양성 체크"""
        print("\n" + "="*80)
        print("4️⃣  다양성 체크")
        print("="*80)

        # 질문 시작 패턴 분석
        start_patterns = Counter()
        for item in self.data:
            q = item['instruction']
            # 첫 2단어 추출
            words = q.split()[:2]
            pattern = ' '.join(words) if len(words) >= 2 else q
            start_patterns[pattern] += 1

        print(f"\n[질문 시작 패턴 TOP 15]")
        for i, (pattern, count) in enumerate(start_patterns.most_common(15), 1):
            percentage = (count / len(self.data)) * 100
            print(f"  {i:2d}. {pattern:30s}: {count:4,}건 ({percentage:4.1f}%)")

        # 답변 시작 패턴 분석
        answer_start_patterns = Counter()
        for item in self.data:
            a = item['output']
            # 첫 5단어 추출
            words = a.split()[:5]
            pattern = ' '.join(words) if len(words) >= 5 else a[:20]
            answer_start_patterns[pattern] += 1

        print(f"\n[답변 시작 패턴 TOP 10]")
        for i, (pattern, count) in enumerate(answer_start_patterns.most_common(10), 1):
            percentage = (count / len(self.data)) * 100
            print(f"  {i:2d}. {pattern:50s}: {count:4,}건 ({percentage:4.1f}%)")

    def remove_duplicates(self, output_path: str):
        """중복 제거 후 저장"""
        print("\n" + "="*80)
        print("5️⃣  중복 제거")
        print("="*80)

        seen_questions = set()
        unique_data = []

        for item in self.data:
            q = item['instruction']
            if q not in seen_questions:
                seen_questions.add(q)
                unique_data.append(item)

        removed = len(self.data) - len(unique_data)

        print(f"  원본: {len(self.data):,}건")
        print(f"  고유: {len(unique_data):,}건")
        print(f"  제거: {removed:,}건")

        if removed > 0:
            # 저장
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                for item in unique_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

            print(f"\n  ✅ 저장 완료: {output_path}")
        else:
            print(f"\n  ✅ 중복 없음: 저장 스킵")

        return len(unique_data)

    def generate_report(self):
        """전체 리포트 생성"""
        print("\n" + "="*80)
        print("📊 종합 품질 리포트")
        print("="*80)

        # 1. 중복 체크
        dup_count, _ = self.check_duplicates()

        # 2. 길이 체크
        self.check_length()

        # 3. 품질 체크
        issues = self.check_quality()

        # 4. 다양성 체크
        self.check_variety()

        # 종합 점수 계산
        print("\n" + "="*80)
        print("✨ 종합 평가")
        print("="*80)

        score = 100
        if dup_count > 0:
            score -= min(20, dup_count)
        if issues:
            score -= len(issues) * 5

        print(f"\n  품질 점수: {score}/100")

        if score >= 90:
            print(f"  등급: ⭐⭐⭐⭐⭐ 매우 우수")
        elif score >= 80:
            print(f"  등급: ⭐⭐⭐⭐ 우수")
        elif score >= 70:
            print(f"  등급: ⭐⭐⭐ 양호")
        elif score >= 60:
            print(f"  등급: ⭐⭐ 보통")
        else:
            print(f"  등급: ⭐ 개선 필요")

        print("\n  권장 사항:")
        if dup_count > 0:
            print(f"    - 중복 {dup_count}건 제거 권장")
        if not issues:
            print(f"    - 데이터 품질 우수, LoRA 학습 진행 가능")
        else:
            print(f"    - {len(issues)}개 품질 이슈 개선 권장")


def main():
    """메인 함수"""

    # 경로 설정
    input_file = Path(__file__).parent.parent / 'output' / 'bigdata_portal_train.jsonl'
    output_file = Path(__file__).parent.parent / 'output' / 'bigdata_portal_train_clean.jsonl'

    # 검증기 실행
    validator = DataQualityValidator(input_file)

    # 전체 리포트 생성
    validator.generate_report()

    # 중복 제거 후 저장
    final_count = validator.remove_duplicates(output_file)

    print("\n" + "="*80)
    print("✅ 품질 검증 완료!")
    print("="*80)
    print(f"\n  원본 파일: {input_file}")
    print(f"  정제 파일: {output_file}")
    print(f"  최종 데이터: {final_count:,}건")


if __name__ == "__main__":
    main()
