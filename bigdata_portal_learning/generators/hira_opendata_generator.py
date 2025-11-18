#!/usr/bin/env python3
"""
HIRA 오픈데이터 포털 학습 데이터 생성기
- 주제별 3,000개 질의응답 세트 생성 목표
- 템플릿 기반 + 고급 변형 기법
"""

import yaml
import json
import random
import re
from pathlib import Path
from typing import List, Dict
from collections import Counter

class HIRAOpenDataGenerator:
    def __init__(self, structure_path: str):
        """초기화"""
        with open(structure_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self.menus = data['menus']
        self.training_data = []

        # 확장된 동의어 사전
        self.synonyms = {
            '신청': ['요청', '등록', '제출', '접수'],
            '방법': ['절차', '과정', '프로세스', '순서'],
            '확인': ['조회', '검색', '찾기', '찾아보기'],
            '가능': ['되나요', '할 수 있나요', '가능한가요', '되는지'],
            '어디서': ['어느 곳에서', '어느 메뉴에서', '어디에서', '어느 곳'],
            '어떻게': ['어떤 방법으로', '어떤 식으로', '어떻게 하면', '방법'],
            '무엇': ['뭐', '어떤 것', '무슨'],
            '데이터': ['자료', '정보'],
            '분석': ['연구', '조사'],
            '통계': ['수치', '지표'],
            '서비스': ['기능', '제공'],
            '이용': ['사용', '활용'],
            '제공': ['지원', '제공'],
            '연구자': ['연구원', '분석가', '학자'],
            '환자': ['수진자', '진료환자'],
        }

        # 질문 접두사 변형
        self.question_prefixes = [
            '',
            '혹시 ',
            '제가 궁금한게 ',
            '알고 싶은데 ',
            '문의드립니다. ',
            '질문있어요. ',
        ]

        # 질문 접미사 변형
        self.question_suffixes = [
            '',
            ' 알려주세요',
            ' 알려줘',
            ' 설명해주세요',
            ' 궁금합니다',
            ' 궁금해요',
            ' 좀 알려주실 수 있나요',
        ]

    def generate(self, target_per_topic: int = 3000):
        """주제별 데이터 생성"""

        print("="*80)
        print("HIRA 오픈데이터 포털 학습 데이터 생성")
        print("="*80)
        print(f"주제별 목표: {target_per_topic:,}건\n")

        total_topics = sum(len(menu_data['topics']) for menu_data in self.menus.values())
        print(f"총 주제 수: {total_topics}개")
        print(f"예상 총 데이터: {total_topics * target_per_topic:,}건\n")

        for menu_id, menu_data in self.menus.items():
            menu_name = menu_data['name']
            print(f"\n{'='*80}")
            print(f"📁 메뉴: {menu_name}")
            print(f"{'='*80}")

            for topic in menu_data['topics']:
                topic_name = topic['name']
                core_qa = topic.get('core_qa', [])

                print(f"\n  📌 주제: {topic_name}")
                print(f"     핵심 Q&A: {len(core_qa)}개")

                if not core_qa:
                    print(f"     ⚠️  핵심 Q&A가 없어 건너뜁니다.")
                    continue

                # 1. 원본 추가
                for item in core_qa:
                    self.training_data.append({
                        "instruction": item['q'],
                        "input": "",
                        "output": item['a'],
                        "metadata": {
                            "menu": menu_id,
                            "menu_name": menu_name,
                            "topic": topic['id'],
                            "topic_name": topic_name,
                            "type": "original"
                        }
                    })

                # 2. 변형 생성
                target_variants = target_per_topic - len(core_qa)
                variants_per_qa = target_variants // len(core_qa)

                print(f"     각 Q&A당 약 {variants_per_qa}개 변형 생성 중...")

                generated_count = 0
                for item in core_qa:
                    original_q = item['q']
                    answer = item['a']

                    # 각 Q&A에 대해 variants_per_qa개 변형 생성
                    for _ in range(variants_per_qa):
                        variant = self._generate_variant(original_q)

                        if variant and variant != original_q:
                            # 중복 체크
                            if not any(d['instruction'] == variant for d in self.training_data):
                                self.training_data.append({
                                    "instruction": variant,
                                    "input": "",
                                    "output": answer,
                                    "metadata": {
                                        "menu": menu_id,
                                        "menu_name": menu_name,
                                        "topic": topic['id'],
                                        "topic_name": topic_name,
                                        "type": "variant"
                                    }
                                })
                                generated_count += 1

                print(f"     ✅ 생성 완료: {len(core_qa) + generated_count:,}건")

        print(f"\n{'='*80}")
        print(f"✅ 전체 생성 완료: {len(self.training_data):,}건")
        print(f"{'='*80}\n")

        return self.training_data

    def _generate_variant(self, original_q: str) -> str:
        """질문 변형 생성 (다양한 기법 적용)"""

        # 변형 기법 리스트
        techniques = [
            self._변형_어미,
            self._변형_질문형식,
            self._변형_동의어,
            self._변형_조사,
            self._변형_축약확장,
            self._변형_단어순서,
            self._변형_의문사,
            self._변형_접두접미사,
            self._변형_존댓말반말,
            self._변형_부가표현,
        ]

        # 랜덤하게 1~3개 기법 선택하여 연속 적용
        num_techniques = random.randint(1, 3)
        selected_techniques = random.sample(techniques, num_techniques)

        variant = original_q
        for technique in selected_techniques:
            variants = technique(variant)
            if variants:
                variant = random.choice(variants)

        # 오타 수정
        variant = self._fix_typos(variant)

        return variant

    def _변형_어미(self, question: str) -> List[str]:
        """어미 변형"""
        variants = []

        patterns = [
            (r'(.+)하나요\?', [r'\1해요?', r'\1할까요?', r'\1하죠?', r'\1합니까?', r'\1하세요?']),
            (r'(.+)인가요\?', [r'\1이에요?', r'\1일까요?', r'\1이죠?', r'\1입니까?', r'\1예요?']),
            (r'(.+)있나요\?', [r'\1있어요?', r'\1있을까요?', r'\1있죠?', r'\1있습니까?']),
            (r'(.+)되나요\?', [r'\1돼요?', r'\1될까요?', r'\1되죠?', r'\1됩니까?', r'\1되나요']),
            (r'(.+)가능한가요\?', [r'\1가능해요?', r'\1가능할까요?', r'\1할 수 있나요?', r'\1가능한지요?']),
        ]

        for pattern, replacements in patterns:
            if re.search(pattern, question):
                for repl in replacements:
                    variant = re.sub(pattern, repl, question)
                    if variant != question:
                        variants.append(variant)

        return variants

    def _변형_질문형식(self, question: str) -> List[str]:
        """질문 형식 변형"""
        variants = []

        patterns = [
            (r'(.+) 어떻게 (.+)\?', [r'\1 \2 방법은?', r'\2 방법 알려주세요', r'\1 어떤 방법으로 \2?']),
            (r'(.+) 뭔가요\?', [r'\1이 무엇인가요?', r'\1에 대해 알려주세요', r'\1 설명해주세요']),
            (r'(.+) 어디서 (.+)\?', [r'\2 어디에서 하나요?', r'\1 \2 위치는?', r'\2 곳은 어디인가요?']),
            (r'(.+) 가능한가요\?', [r'\1 수 있나요?', r'\1 가능여부는?', r'\1 되나요?']),
        ]

        for pattern, replacements in patterns:
            if re.search(pattern, question):
                for repl in replacements:
                    try:
                        variant = re.sub(pattern, repl, question)
                        if variant != question:
                            variants.append(variant)
                    except:
                        pass

        return variants

    def _변형_동의어(self, question: str) -> List[str]:
        """동의어 치환"""
        variants = []

        for word, synonyms in self.synonyms.items():
            if word in question:
                for synonym in synonyms:
                    variant = question.replace(word, synonym, 1)  # 첫 번째만 치환
                    if variant != question:
                        variants.append(variant)

        return variants

    def _변형_조사(self, question: str) -> List[str]:
        """조사 변형"""
        variants = []

        replacements = [
            ('은', '는'),
            ('는', '은'),
            ('이', '가'),
            ('가', '이'),
            ('을', '를'),
            ('를', '을'),
            ('과', '와'),
            ('와', '과'),
        ]

        for old, new in replacements:
            if old in question:
                variant = question.replace(old, new, 1)
                if variant != question:
                    variants.append(variant)

        return variants

    def _변형_축약확장(self, question: str) -> List[str]:
        """축약/확장"""
        variants = []

        # 축약 패턴
        abbr_patterns = [
            (r'(.+) 어떻게 (.+)\?', r'\1 \2?'),
            (r'(.+)에 대해 (.+)\?', r'\1 \2?'),
            (r'(.+)하는 방법', r'\1 방법'),
        ]

        for pattern, replacement in abbr_patterns:
            if re.search(pattern, question):
                variant = re.sub(pattern, replacement, question)
                if variant != question:
                    variants.append(variant)

        # 확장 패턴
        if not question.endswith('?'):
            variants.append(question + '?')

        return variants

    def _변형_단어순서(self, question: str) -> List[str]:
        """단어 순서 변경 (제한적)"""
        variants = []

        patterns = [
            (r'(.+)와 (.+) 차이', r'\2와 \1 차이'),
            (r'(.+) 어디서 (.+)', r'\2 어디서 하나요?'),
        ]

        for pattern, replacement in patterns:
            if re.search(pattern, question):
                variant = re.sub(pattern, replacement, question)
                if variant != question:
                    variants.append(variant)

        return variants

    def _변형_의문사(self, question: str) -> List[str]:
        """의문사 변형"""
        variants = []

        replacements = [
            ('뭔가요', '무엇인가요'),
            ('무엇인가요', '뭔가요'),
            ('어떻게', '어떤 방법으로'),
            ('어떤 방법으로', '어떻게'),
            ('어디서', '어느 곳에서'),
            ('어느 곳에서', '어디서'),
            ('언제', '몇 시에'),
            ('왜', '어떤 이유로'),
            ('얼마나', '어느 정도'),
        ]

        for old, new in replacements:
            if old in question:
                variant = question.replace(old, new)
                if variant != question:
                    variants.append(variant)

        return variants

    def _변형_접두접미사(self, question: str) -> List[str]:
        """접두사/접미사 추가"""
        variants = []

        # 접두사 추가
        for prefix in self.question_prefixes:
            if not question.startswith(prefix):
                variant = prefix + question
                variants.append(variant)

        # 접미사 추가 (물음표 제거 후)
        q_without_mark = question.rstrip('?')
        for suffix in self.question_suffixes:
            if suffix and not question.endswith(suffix):
                variant = q_without_mark + suffix
                if not variant.endswith('?'):
                    variant += '?'
                variants.append(variant)

        return variants

    def _변형_존댓말반말(self, question: str) -> List[str]:
        """존댓말/반말 변환"""
        variants = []

        # 존댓말 -> 반말
        formal_to_casual = [
            ('하나요', '해'),
            ('인가요', '이야'),
            ('있나요', '있어'),
            ('되나요', '돼'),
            ('알려주세요', '알려줘'),
            ('설명해주세요', '설명해줘'),
        ]

        # 반말 -> 존댓말
        casual_to_formal = [
            ('해', '합니까'),
            ('이야', '입니까'),
            ('있어', '있습니까'),
            ('돼', '됩니까'),
            ('알려줘', '알려주십시오'),
        ]

        for old, new in formal_to_casual + casual_to_formal:
            if old in question:
                variant = question.replace(old, new)
                if variant != question:
                    variants.append(variant)

        return variants

    def _변형_부가표현(self, question: str) -> List[str]:
        """부가 표현 추가"""
        variants = []

        additional_phrases = [
            ('조회', '조회 및 검색'),
            ('데이터', '데이터셋'),
            ('신청', '신청 및 등록'),
            ('방법', '상세 방법'),
            ('정보', '상세 정보'),
            ('통계', '통계 정보'),
        ]

        for word, expanded in additional_phrases:
            if word in question and expanded not in question:
                variant = question.replace(word, expanded, 1)
                if variant != question:
                    variants.append(variant)

        return variants

    def _fix_typos(self, text: str) -> str:
        """오타/맞춤법 수정"""

        # 자주 발생하는 오타 패턴
        typo_fixes = [
            ('데가터', '데이터'),
            ('데이가', '데이터'),
            ('  ', ' '),  # 중복 공백
            (' ?', '?'),  # 공백 + 물음표
            ('??', '?'),  # 중복 물음표
        ]

        for wrong, correct in typo_fixes:
            text = text.replace(wrong, correct)

        # 조사 중복 제거
        text = re.sub(r'([가-힣])는는', r'\1는', text)
        text = re.sub(r'([가-힣])은은', r'\1은', text)
        text = re.sub(r'([가-힣])을을', r'\1을', text)
        text = re.sub(r'([가-힣])를를', r'\1를', text)

        return text.strip()

    def get_statistics(self) -> Dict:
        """통계 정보"""
        questions = [item['instruction'] for item in self.training_data]
        answers = [item['output'] for item in self.training_data]

        q_lengths = [len(q) for q in questions]
        a_lengths = [len(a) for a in answers]

        # 메뉴별 분포
        menu_dist = Counter()
        topic_dist = Counter()
        for item in self.training_data:
            menu_name = item['metadata']['menu_name']
            topic_name = item['metadata']['topic_name']
            menu_dist[menu_name] += 1
            topic_dist[topic_name] += 1

        return {
            "total": len(self.training_data),
            "q_length_avg": sum(q_lengths) / len(q_lengths) if q_lengths else 0,
            "q_length_min": min(q_lengths) if q_lengths else 0,
            "q_length_max": max(q_lengths) if q_lengths else 0,
            "a_length_avg": sum(a_lengths) / len(a_lengths) if a_lengths else 0,
            "a_length_min": min(a_lengths) if a_lengths else 0,
            "a_length_max": max(a_lengths) if a_lengths else 0,
            "menu_distribution": menu_dist.most_common(),
            "topic_distribution": topic_dist.most_common(),
        }

    def save_jsonl(self, output_path: str, include_metadata: bool = False):
        """JSONL 저장 (학습용)"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.training_data:
                if include_metadata:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
                else:
                    # 메타데이터 제외
                    simple_item = {
                        "instruction": item['instruction'],
                        "input": item['input'],
                        "output": item['output']
                    }
                    f.write(json.dumps(simple_item, ensure_ascii=False) + '\n')

        print(f"✅ JSONL 저장 완료: {output_path}")
        print(f"   총 {len(self.training_data):,}건\n")

    def save_json(self, output_path: str, include_metadata: bool = True):
        """JSON 저장 (검토용)"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if include_metadata:
            data = self.training_data
        else:
            data = [
                {
                    "instruction": item['instruction'],
                    "input": item['input'],
                    "output": item['output']
                }
                for item in self.training_data
            ]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 저장 완료: {output_path}\n")

    def print_samples(self, count: int = 10):
        """샘플 출력"""
        print(f"{'='*80}")
        print(f"📝 무작위 샘플 {count}개")
        print(f"{'='*80}\n")

        samples = random.sample(self.training_data, min(count, len(self.training_data)))

        for i, sample in enumerate(samples, 1):
            print(f"[샘플 {i}]")
            print(f"메뉴: {sample['metadata']['menu_name']} > {sample['metadata']['topic_name']}")
            print(f"Q: {sample['instruction']}")
            print(f"A: {sample['output'][:100]}...\n")

    def print_statistics(self):
        """통계 출력"""
        stats = self.get_statistics()

        print(f"{'='*80}")
        print(f"📊 데이터 통계")
        print(f"{'='*80}\n")

        print(f"[전체]")
        print(f"  총 데이터: {stats['total']:,}건\n")

        print(f"[질문 길이]")
        print(f"  평균: {stats['q_length_avg']:.1f}자")
        print(f"  최소: {stats['q_length_min']}자")
        print(f"  최대: {stats['q_length_max']}자\n")

        print(f"[답변 길이]")
        print(f"  평균: {stats['a_length_avg']:.1f}자")
        print(f"  최소: {stats['a_length_min']}자")
        print(f"  최대: {stats['a_length_max']}자\n")

        print(f"[메뉴별 분포]")
        for menu_name, count in stats['menu_distribution']:
            pct = (count / stats['total']) * 100
            print(f"  {menu_name:30s}: {count:6,}건 ({pct:5.1f}%)")

        print(f"\n[주제별 분포 TOP 10]")
        for i, (topic_name, count) in enumerate(stats['topic_distribution'][:10], 1):
            pct = (count / stats['total']) * 100
            print(f"  {i:2d}. {topic_name:30s}: {count:6,}건 ({pct:5.1f}%)")


def main():
    # 경로 설정
    structure_path = "/home/user/bigdataptAI/bigdata_portal_learning/config/hira_opendata_structure.yaml"
    output_dir = "/home/user/bigdataptAI/bigdata_portal_learning/output"

    output_jsonl_train = f"{output_dir}/hira_opendata_train.jsonl"
    output_jsonl_full = f"{output_dir}/hira_opendata_train_with_metadata.jsonl"
    output_json = f"{output_dir}/hira_opendata_train.json"

    # 생성기 초기화
    print("HIRA 오픈데이터 포털 학습 데이터 생성기")
    print("="*80)
    generator = HIRAOpenDataGenerator(structure_path)

    # 데이터 생성 (주제별 3,000건 목표)
    generator.generate(target_per_topic=3000)

    # 통계 출력
    generator.print_statistics()

    # 샘플 출력
    generator.print_samples(15)

    # 저장
    generator.save_jsonl(output_jsonl_train, include_metadata=False)  # 학습용 (메타데이터 제외)
    generator.save_jsonl(output_jsonl_full, include_metadata=True)    # 전체 (메타데이터 포함)
    generator.save_json(output_json, include_metadata=True)           # JSON (검토용)

    print(f"{'='*80}")
    print(f"✅ HIRA 오픈데이터 학습 데이터 생성 완료!")
    print(f"{'='*80}\n")

    print(f"📁 생성 파일:")
    print(f"  1. {output_jsonl_train} (학습용, 메타데이터 제외)")
    print(f"  2. {output_jsonl_full} (전체, 메타데이터 포함)")
    print(f"  3. {output_json} (JSON, 검토용)\n")


if __name__ == "__main__":
    main()
