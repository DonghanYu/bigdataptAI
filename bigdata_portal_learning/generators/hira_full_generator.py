#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIRA 보건의료빅데이터개방시스템 최고품질 데이터 생성기
핵심 Q&A 기반 자동 확장 → 1,500-2,500건 생성
"""

import json
import random
import yaml
from pathlib import Path
from typing import List, Dict
import re

class HIRAFullGenerator:
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.core_qa = self._load_yaml('hira_core_qa.yaml')
        self.generated_data = []
        self.question_set = set()

    def _load_yaml(self, filename: str) -> dict:
        """YAML 파일 로드"""
        with open(self.config_dir / filename, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate_all_data(self, target_count: int = 2000) -> List[Dict]:
        """전체 데이터 생성"""
        print("="*80)
        print("HIRA 최고품질 학습 데이터 생성")
        print("="*80)
        print(f"목표: {target_count:,}건\n")

        # 핵심 Q&A 로드
        all_core_qa = []
        for category, qa_list in self.core_qa['core_qa'].items():
            for qa in qa_list:
                all_core_qa.append({
                    'category': category,
                    'q': qa['q'],
                    'a': qa['a']
                })

        print(f"핵심 Q&A: {len(all_core_qa)}개")
        print(f"각 Q&A당 약 {target_count // len(all_core_qa)}개 변형 생성\n")

        # 각 핵심 Q&A를 확장
        variants_per_qa = target_count // len(all_core_qa)

        for core in all_core_qa:
            # 원본 추가
            self._add_qa(core['q'], core['a'])

            # 변형 생성
            for _ in range(variants_per_qa - 1):
                variant_q = self._generate_question_variant(core['q'])

                if variant_q and variant_q not in self.question_set:
                    self._add_qa(variant_q, core['a'])

        # 목표 개수 맞추기
        if len(self.generated_data) < target_count:
            shortage = target_count - len(self.generated_data)
            print(f"\n추가 생성 필요: {shortage}건")

            for _ in range(shortage):
                core = random.choice(all_core_qa)
                variant_q = self._generate_question_variant(core['q'])

                if variant_q and variant_q not in self.question_set:
                    self._add_qa(variant_q, core['a'])

        # 데이터 섞기
        random.shuffle(self.generated_data)

        # 최종 개수 조정
        self.generated_data = self.generated_data[:target_count]

        print("\n" + "="*80)
        print(f"✅ 생성 완료: {len(self.generated_data):,}건")
        print("="*80)

        return self.generated_data

    def _add_qa(self, question: str, answer: str):
        """Q&A 추가"""
        if question not in self.question_set:
            self.question_set.add(question)
            self.generated_data.append({
                "instruction": question,
                "input": "",
                "output": answer
            })

    def _generate_question_variant(self, original_q: str) -> str:
        """질문 변형 생성 - 강화된 버전"""

        variants = []

        # 1. 어미 변형 (존댓말/반말)
        variants.extend(self._change_speech_style(original_q))

        # 2. 질문 형식 변형
        variants.extend(self._change_question_format(original_q))

        # 3. 동의어 치환 (여러 번 적용)
        for _ in range(3):
            variants.extend(self._synonym_replacement(original_q))

        # 4. 조사 변형
        variants.extend(self._change_particle(original_q))

        # 5. 표현 변형
        variants.extend(self._rephrase(original_q))

        # 6. 추가 표현 (새로운)
        variants.extend(self._add_context_phrases(original_q))

        # 7. 간결화/확장
        variants.extend(self._simplify_or_expand(original_q))

        # 8. 조합 변형 (기존 변형들을 조합)
        if len(variants) > 2:
            # 일부 변형을 조합하여 새로운 변형 생성
            for _ in range(5):
                base = random.choice(variants)
                # 추가 변형 적용
                combined = self._apply_random_transform(base)
                if combined and combined != original_q:
                    variants.append(combined)

        # 중복 제거
        unique_variants = list(set(variants))
        # 원본과 같은 것 제거
        unique_variants = [v for v in unique_variants if v != original_q]

        # 랜덤 선택
        if unique_variants:
            return random.choice(unique_variants)
        else:
            return None

    def _change_speech_style(self, question: str) -> List[str]:
        """존댓말/반말 변형"""
        variants = []

        # 존댓말 → 반말
        if '하나요' in question or '인가요' in question or '주세요' in question:
            informal = question
            informal = informal.replace('하나요?', '해?')
            informal = informal.replace('하나요', '해')
            informal = informal.replace('인가요?', '인가?')
            informal = informal.replace('인가요', '야')
            informal = informal.replace('주세요', '줘')
            informal = informal.replace('되나요', '돼')
            informal = informal.replace('있나요', '있어')
            if informal != question:
                variants.append(informal)

        # 반말 → 존댓말
        if '해?' in question or '야?' in question or '줘' in question:
            formal = question
            formal = formal.replace('해?', '하나요?')
            formal = formal.replace('야?', '인가요?')
            formal = formal.replace('줘', '주세요')
            formal = formal.replace('돼?', '되나요?')
            formal = formal.replace('있어?', '있나요?')
            if formal != question:
                variants.append(formal)

        return variants

    def _change_question_format(self, question: str) -> List[str]:
        """질문 형식 변형"""
        variants = []

        # "~은 어떻게 하나요?" → "~하려면 어떻게 해야 하나요?"
        match = re.search(r'(.+?)은 어떻게 하나요', question)
        if match:
            topic = match.group(1)
            variants.append(f"{topic}하려면 어떻게 해야 하나요?")
            variants.append(f"{topic} 방법 알려주세요")
            variants.append(f"{topic} 절차가 궁금합니다")

        # "~는 어디서~" → "~하는 곳이 어디인가요?"
        match = re.search(r'(.+?)는 어디서 (.+)', question)
        if match:
            topic = match.group(1)
            action = match.group(2)
            variants.append(f"{topic} {action}하는 곳이 어디인가요?")

        # "~는 무엇인가요?" → "~에 대해 설명해주세요"
        match = re.search(r'(.+?)는 무엇인가요', question)
        if match:
            topic = match.group(1)
            variants.append(f"{topic}에 대해 설명해주세요")
            variants.append(f"{topic}이 뭔가요?")
            variants.append(f"{topic} 알려주세요")

        # "~하고 싶어요" 형식 추가
        if '방법' in question:
            base = question.replace(' 방법', '').replace('?', '').replace('하나요', '')
            variants.append(f"{base}하고 싶어요")

        return variants

    def _synonym_replacement(self, question: str) -> List[str]:
        """동의어 치환"""
        variants = []

        synonym_dict = {
            '어떻게': ['어떤 방법으로', '어느 방식으로'],
            '방법': ['절차', '방식', '과정'],
            '조회': ['확인', '검색', '찾기', '보기'],
            '어디서': ['어디에서', '어느 곳에서'],
            '무엇인가요': ['뭔가요', '무엇입니까'],
            '있나요': ['있습니까', '있을까요'],
            '신청': ['등록', '요청'],
            '다운로드': ['내려받기', '받기', '저장'],
            '사용': ['이용', '활용'],
        }

        for original, synonyms in synonym_dict.items():
            if original in question:
                for syn in synonyms:
                    variant = question.replace(original, syn)
                    if variant != question:
                        variants.append(variant)

        return variants

    def _change_particle(self, question: str) -> List[str]:
        """조사 변형"""
        variants = []

        particle_changes = [
            ('는', '은'),
            ('을', '를'),
            ('이', '가'),
            ('에', '에서'),
        ]

        for old_p, new_p in particle_changes:
            if old_p in question:
                variant = question.replace(old_p, new_p, 1)  # 첫 번째만 변경
                if variant != question:
                    variants.append(variant)

        return variants

    def _rephrase(self, question: str) -> List[str]:
        """표현 변형 (더 자연스러운 표현)"""
        variants = []

        rephrase_patterns = [
            (r'(.+) 어떻게 하나요\?', r'\1 방법이 궁금해요'),
            (r'(.+) 알려주세요', r'\1 좀 가르쳐주세요'),
            (r'(.+)이 뭔가요\?', r'\1 설명 부탁드립니다'),
            (r'(.+) 가능한가요\?', r'\1 할 수 있나요?'),
            (r'(.+) 어디서 (.+)\?', r'\2 어디서 하나요?'),
        ]

        for pattern, replacement in rephrase_patterns:
            match = re.match(pattern, question)
            if match:
                variant = re.sub(pattern, replacement, question)
                if variant != question:
                    variants.append(variant)

        return variants

    def _add_context_phrases(self, question: str) -> List[str]:
        """문맥 추가 표현"""
        variants = []

        prefixes = [
            "궁금한 게 있는데, ",
            "문의드립니다. ",
            "질문 있어요. ",
        ]

        suffixes = [
            " 답변 부탁드려요",
            " 알려주시면 감사하겠습니다",
            " 설명 부탁합니다",
        ]

        # 접두사 추가
        for prefix in prefixes:
            variants.append(prefix + question)

        # 접미사 추가
        for suffix in suffixes:
            base = question.rstrip('?').rstrip('.')
            variants.append(base + suffix)

        return variants

    def _simplify_or_expand(self, question: str) -> List[str]:
        """간결화 또는 확장"""
        variants = []

        # 간결화: 불필요한 단어 제거
        simplified = question.replace('어떻게 ', '')
        simplified = simplified.replace('어떤 ', '')
        if simplified != question:
            variants.append(simplified)

        # 확장: 구체적 표현 추가
        expansions = [
            question.replace('?', ' 가능한가요?'),
            question.replace('?', ' 되나요?'),
            question.replace('하나요?', '하는 방법은 무엇인가요?'),
        ]

        for exp in expansions:
            if exp != question:
                variants.append(exp)

        return variants

    def _apply_random_transform(self, question: str) -> str:
        """랜덤 변형 적용"""
        transforms = [
            lambda q: q.replace('?', ''),
            lambda q: q.replace('하나요', '해'),
            lambda q: q.replace('인가요', '야'),
            lambda q: q.replace('주세요', '줘'),
            lambda q: q.replace('은', '는'),
            lambda q: q.replace('를', '을'),
            lambda q: q.replace('이', '가'),
        ]

        transform = random.choice(transforms)
        try:
            return transform(question)
        except:
            return question

    def save_jsonl(self, output_path: str):
        """JSONL 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.generated_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"\n✅ JSONL 저장 완료: {output_path}")
        print(f"   총 {len(self.generated_data):,}건")

    def save_json(self, output_path: str):
        """JSON 저장 (검토용)"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.generated_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 저장 완료: {output_path}")

    def print_statistics(self):
        """통계 출력"""
        print("\n" + "="*80)
        print("📊 데이터 통계")
        print("="*80)

        q_lengths = [len(item['instruction']) for item in self.generated_data]
        a_lengths = [len(item['output']) for item in self.generated_data]

        print(f"\n[질문 길이]")
        print(f"  평균: {sum(q_lengths) / len(q_lengths):.1f}자")
        print(f"  최소: {min(q_lengths)}자")
        print(f"  최대: {max(q_lengths)}자")

        print(f"\n[답변 길이]")
        print(f"  평균: {sum(a_lengths) / len(a_lengths):.1f}자")
        print(f"  최소: {min(a_lengths)}자")
        print(f"  최대: {max(a_lengths)}자")

        # 샘플 출력
        print("\n" + "="*80)
        print("📝 무작위 샘플 10개")
        print("="*80)

        samples = random.sample(self.generated_data, min(10, len(self.generated_data)))
        for i, sample in enumerate(samples, 1):
            print(f"\n[샘플 {i}]")
            print(f"Q: {sample['instruction']}")
            print(f"A: {sample['output'][:150]}...")


def main():
    """메인 실행"""
    config_dir = Path(__file__).parent.parent / 'config'
    output_dir = Path(__file__).parent.parent / 'output'

    # 생성기 초기화
    generator = HIRAFullGenerator(config_dir)

    # 데이터 생성 (목표: 2,000건)
    generator.generate_all_data(target_count=2000)

    # 통계 출력
    generator.print_statistics()

    # JSONL 저장 (학습용)
    generator.save_jsonl(output_dir / 'hira_train_2000.jsonl')

    # JSON 저장 (검토용)
    generator.save_json(output_dir / 'hira_train_2000.json')

    print("\n" + "="*80)
    print("✅ 최고품질 데이터 생성 완료!")
    print("="*80)
    print(f"\n📁 생성 파일:")
    print(f"  1. {output_dir / 'hira_train_2000.jsonl'} (학습용)")
    print(f"  2. {output_dir / 'hira_train_2000.json'} (검토용)")
    print(f"\n다음 단계:")
    print(f"  1. 데이터 품질 검증")
    print(f"  2. LoRA 학습 준비")


if __name__ == "__main__":
    main()
