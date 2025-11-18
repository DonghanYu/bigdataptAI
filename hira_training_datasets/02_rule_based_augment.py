#!/usr/bin/env python3
"""
HIRA 규칙 기반 데이터 증강
- 어미 변형
- 조사 변경
- 동의어 치환
- 질문 형식 변경
- 어순 변경
- 축약/확장

목표: 323개 → 2,000개 (6배 증강)
"""

import json
import random
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from datetime import datetime
import argparse


class RuleBasedAugmentor:
    """규칙 기반 데이터 증강기"""

    def __init__(self, source_path: str):
        """초기화"""
        with open(source_path, 'r', encoding='utf-8') as f:
            self.source_data = json.load(f)

        self.augmented_data = []
        self.seen_questions = set()

        # 동의어 사전
        self.synonyms = {
            '신청': ['요청', '등록'],
            '방법': ['절차', '과정'],
            '확인': ['조회', '검색'],
            '가능': ['되나요', '할 수 있나요'],
            '어디서': ['어느 곳에서', '어느 메뉴에서'],
            '어떻게': ['어떤 방법으로', '어떤 식으로'],
            '무엇': ['뭐', '어떤 것'],
            '데이터': ['자료', '정보'],
            '분석': ['연구', '분석작업'],
            '통계': ['수치', '통계자료'],
            '사용': ['이용', '활용'],
            '제공': ['지원', '서비스'],
            '필요': ['요구', '필요한'],
        }

        # 통계
        self.stats = {
            "original_count": 0,
            "augmented_count": 0,
            "by_method": defaultdict(int),
            "by_menu": defaultdict(int)
        }

    def augment(self, multiplier: int = 6):
        """데이터 증강 실행"""
        print("="*80)
        print("규칙 기반 데이터 증강")
        print("="*80 + "\n")

        # 원본 Q&A 수집
        original_qa_list = []
        for menu_id, qa_group in self.source_data.get("core_qa", {}).items():
            menu_name = self.source_data["menu_structure"][menu_id]["name"]
            for qa in qa_group["qa_pairs"]:
                original_qa_list.append({
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "menu_id": menu_id,
                    "menu_name": menu_name,
                    "source_id": f"{menu_id}_{len(original_qa_list)}"
                })

        self.stats["original_count"] = len(original_qa_list)
        print(f"원본 Q&A: {len(original_qa_list)}개")
        print(f"목표 배율: {multiplier}x")
        print(f"목표 개수: {len(original_qa_list) * multiplier}개\n")

        # 원본 추가
        for qa in original_qa_list:
            self._add_qa(qa, "original")

        # 각 Q&A에 대해 변형 생성
        print("변형 생성 중...")
        for idx, qa in enumerate(original_qa_list):
            if (idx + 1) % 50 == 0:
                print(f"  진행: {idx+1}/{len(original_qa_list)} "
                      f"(생성: {len(self.augmented_data)}개)")

            variants_needed = multiplier - 1  # 원본 제외
            variants = self._generate_variants(qa, variants_needed)

            for variant in variants:
                self._add_qa(variant, variant["generation_method"])

        print(f"\n✅ 총 {len(self.augmented_data)}개 생성")
        print(f"   원본: {self.stats['by_method']['original']}개")
        print(f"   증강: {len(self.augmented_data) - self.stats['by_method']['original']}개")

        return self.augmented_data

    def _generate_variants(self, qa: Dict, count: int) -> List[Dict]:
        """단일 Q&A에 대한 변형 생성"""
        variants = []
        attempts = 0
        max_attempts = count * 10  # 더 많은 시도

        while len(variants) < count and attempts < max_attempts:
            attempts += 1

            # 변형 방법 랜덤 선택
            method = random.choice([
                self._variant_ending,
                self._variant_question_format,
                self._variant_synonym,
                self._variant_particle,
                self._variant_abbreviation,
                self._variant_word_order,
                self._variant_interrogative,
                self._variant_combo  # 조합 변형
            ])

            # 변형 생성
            variant_q = method(qa["question"])

            # 유효성 검사
            if variant_q and variant_q != qa["question"] and variant_q not in self.seen_questions:
                # 오타 수정
                variant_q = self._fix_typos(variant_q)

                variants.append({
                    "question": variant_q,
                    "answer": qa["answer"],
                    "menu_id": qa["menu_id"],
                    "menu_name": qa["menu_name"],
                    "source_id": qa["source_id"],
                    "generation_method": method.__name__.replace("_variant_", "")
                })

        return variants

    def _variant_ending(self, question: str) -> str:
        """어미 변형"""
        patterns = [
            (r'(.+)하나요\?', [r'\1해요?', r'\1할까요?', r'\1하죠?', r'\1합니까?']),
            (r'(.+)인가요\?', [r'\1이에요?', r'\1일까요?', r'\1이죠?', r'\1입니까?']),
            (r'(.+)있나요\?', [r'\1있어요?', r'\1있을까요?', r'\1있죠?', r'\1있습니까?']),
            (r'(.+)되나요\?', [r'\1돼요?', r'\1될까요?', r'\1되죠?', r'\1됩니까?']),
            (r'(.+)가능한가요\?', [r'\1가능해요?', r'\1가능할까요?', r'\1할 수 있나요?']),
        ]

        for pattern, replacements in patterns:
            if re.match(pattern, question):
                return re.sub(pattern, random.choice(replacements), question)

        return question

    def _variant_question_format(self, question: str) -> str:
        """질문 형식 변형"""
        patterns = [
            (r'(.+) 어떻게 하나요\?', [r'\1 방법은?', r'\1 절차를 알려주세요', r'\1 어떻게 해요?']),
            (r'(.+) 뭔가요\?', [r'\1이 무엇인가요?', r'\1에 대해 설명해주세요', r'\1 의미는?']),
            (r'(.+) 어디서 (.+)\?', [r'\2 어디에서 하나요?', r'\2 어느 곳에서 하나요?']),
            (r'(.+)은 어떻게\?', [r'\1 방법?', r'\1 어떻게 하나요?']),
        ]

        for pattern, replacements in patterns:
            if re.search(pattern, question):
                return re.sub(pattern, random.choice(replacements), question)

        return question

    def _variant_synonym(self, question: str) -> str:
        """동의어 치환"""
        # 랜덤하게 1-2개 단어 치환
        words_to_replace = random.sample(
            list(self.synonyms.keys()),
            min(2, len(self.synonyms))
        )

        variant = question
        for word in words_to_replace:
            if word in variant:
                synonym = random.choice(self.synonyms[word])
                variant = variant.replace(word, synonym, 1)  # 첫 번째만
                break  # 한 번만 치환

        return variant

    def _variant_particle(self, question: str) -> str:
        """조사 변형"""
        replacements = [
            ('은', '는'),
            ('는', '은'),
            ('이', '가'),
            ('가', '이'),
            ('을', '를'),
            ('를', '을'),
        ]

        variant = question
        for old, new in replacements:
            if old in variant:
                variant = variant.replace(old, new, 1)
                break

        return variant

    def _variant_abbreviation(self, question: str) -> str:
        """축약/확장"""
        # 축약 패턴
        abbr_patterns = [
            (r'(.+) 어떻게 (.+)\?', r'\1 \2?'),
            (r'(.+) 방법을 알려주세요', r'\1 방법은?'),
        ]

        # 확장 패턴
        expand_patterns = [
            (r'(.+) 조회\?', r'\1 어떻게 조회하나요?'),
            (r'(.+) 신청\?', r'\1 신청 방법은?'),
        ]

        variant = question

        # 랜덤하게 축약 또는 확장
        if random.random() < 0.5:
            patterns = abbr_patterns
        else:
            patterns = expand_patterns

        for pattern, replacement in patterns:
            if re.search(pattern, variant):
                variant = re.sub(pattern, replacement, variant)
                break

        return variant

    def _variant_word_order(self, question: str) -> str:
        """어순 변경"""
        patterns = [
            (r'HIRA (.+) (.+)', r'\1 HIRA \2'),
            (r'(.+)와 (.+) 차이', r'\2와 \1 차이'),
        ]

        for pattern, replacement in patterns:
            if re.search(pattern, question):
                return re.sub(pattern, replacement, question)

        return question

    def _variant_interrogative(self, question: str) -> str:
        """의문사 변형"""
        replacements = [
            ('뭔가요', '무엇인가요'),
            ('무엇인가요', '뭔가요'),
            ('어떻게', '어떤 방법으로'),
            ('어디서', '어느 곳에서'),
        ]

        variant = question
        for old, new in replacements:
            if old in variant:
                variant = variant.replace(old, new)
                break

        return variant

    def _variant_combo(self, question: str) -> str:
        """조합 변형 (여러 기법 조합)"""
        variant = question

        # 2-3개 기법 조합
        methods = random.sample([
            self._variant_ending,
            self._variant_synonym,
            self._variant_particle
        ], random.randint(2, 3))

        for method in methods:
            variant = method(variant)
            if variant != question:
                break

        return variant

    def _fix_typos(self, text: str) -> str:
        """오타/맞춤법 수정"""
        # 중복 조사 제거
        text = re.sub(r'([가-힣])는는', r'\1는', text)
        text = re.sub(r'([가-힣])은은', r'\1은', text)
        text = re.sub(r'([가-힣])을을', r'\1을', text)
        text = re.sub(r'([가-힣])를를', r'\1를', text)

        # 공백 정리
        text = re.sub(r' +', ' ', text)
        text = text.strip()

        return text

    def _add_qa(self, qa: Dict, method: str):
        """Q&A 추가 (중복 체크)"""
        q = qa["question"]

        if q not in self.seen_questions:
            self.seen_questions.add(q)

            qa_data = {
                "id": f"hira_{qa['menu_id']}_{len(self.augmented_data):05d}",
                "instruction": q,
                "input": "",
                "output": qa["answer"],
                "metadata": {
                    "menu": qa["menu_id"],
                    "menu_name": qa["menu_name"],
                    "generation_method": method,
                    "source_id": qa.get("source_id", ""),
                    "created_at": datetime.now().isoformat(),
                    "question_length": len(q),
                    "answer_length": len(qa["answer"])
                }
            }

            self.augmented_data.append(qa_data)
            self.stats["by_method"][method] += 1
            self.stats["by_menu"][qa["menu_id"]] += 1

    def save_data(self, output_path: str):
        """데이터 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.augmented_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 데이터 저장: {output_path}")
        print(f"   파일 크기: {output_path.stat().st_size:,} bytes")

    def print_statistics(self):
        """통계 출력"""
        print("\n" + "="*80)
        print("📊 증강 통계")
        print("="*80)

        print(f"\n전체:")
        print(f"  총 데이터: {len(self.augmented_data)}개")
        print(f"  원본: {self.stats['by_method']['original']}개")
        print(f"  증강: {len(self.augmented_data) - self.stats['by_method']['original']}개")
        print(f"  증강 배율: {len(self.augmented_data) / self.stats['original_count']:.1f}x")

        print(f"\n생성 방법별:")
        sorted_methods = sorted(
            self.stats["by_method"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for method, count in sorted_methods[:10]:
            pct = (count / len(self.augmented_data)) * 100
            print(f"  {method:20s}: {count:4d}개 ({pct:5.1f}%)")

        print(f"\n메뉴별:")
        for menu_id, count in self.stats["by_menu"].items():
            menu_name = self.source_data["menu_structure"][menu_id]["name"]
            pct = (count / len(self.augmented_data)) * 100
            print(f"  {menu_name:20s}: {count:4d}개 ({pct:5.1f}%)")


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(description="HIRA 규칙 기반 데이터 증강")
    parser.add_argument("--multiplier", type=int, default=6,
                       help="증강 배율 (default: 6)")
    parser.add_argument("--input", type=str,
                       default="source_data/hira_source.json",
                       help="입력 파일 경로")
    parser.add_argument("--output", type=str,
                       default="output/temp/rule_augmented.json",
                       help="출력 파일 경로")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("HIRA 규칙 기반 데이터 증강기 v1.0")
    print("="*80 + "\n")

    # 경로 설정
    base_dir = Path(__file__).parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output

    # 증강기 초기화
    augmentor = RuleBasedAugmentor(input_path)

    # 증강 실행
    augmented_data = augmentor.augment(multiplier=args.multiplier)

    # 저장
    augmentor.save_data(output_path)

    # 통계
    augmentor.print_statistics()

    print("\n" + "="*80)
    print("🎉 규칙 기반 증강 완료!")
    print("="*80)
    print(f"\n다음 단계: 템플릿 기반 생성")
    print(f"python3 03_template_based_generate.py --input {output_path}")


if __name__ == "__main__":
    main()
