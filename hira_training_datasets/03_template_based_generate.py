#!/usr/bin/env python3
"""
HIRA 템플릿 기반 데이터 생성
- 주제 기반 질문 생성
- 키워드 기반 질문 생성
- 답변 재사용 및 변형

목표: 1,064개 → 5,000개
"""

import json
import yaml
import random
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from datetime import datetime
import argparse


class TemplateBasedGenerator:
    """템플릿 기반 데이터 생성기"""

    def __init__(self, augmented_path: str, source_path: str, template_path: str):
        """초기화"""
        # 증강된 데이터 로드
        with open(augmented_path, 'r', encoding='utf-8') as f:
            self.augmented_data = json.load(f)

        # 소스 데이터 로드 (메뉴/주제 정보)
        with open(source_path, 'r', encoding='utf-8') as f:
            self.source_data = json.load(f)

        # 템플릿 로드
        with open(template_path, 'r', encoding='utf-8') as f:
            self.templates = yaml.safe_load(f)

        self.generated_data = []
        self.seen_questions = set([qa["instruction"] for qa in self.augmented_data])

        # 기존 데이터 추가
        self.generated_data.extend(self.augmented_data)

        # 메뉴별 답변 맵 구축
        self.menu_answers = self._build_answer_map()

        # 통계
        self.stats = {
            "initial_count": len(self.augmented_data),
            "generated_count": 0,
            "by_template_type": defaultdict(int),
            "by_menu": defaultdict(int)
        }

    def _build_answer_map(self) -> Dict:
        """메뉴별 답변 맵 구축"""
        answer_map = defaultdict(list)

        for qa in self.augmented_data:
            menu = qa["metadata"]["menu"]
            answer_map[menu].append(qa["output"])

        return answer_map

    def generate(self, target: int = 5000):
        """템플릿 기반 생성"""
        print("="*80)
        print("템플릿 기반 데이터 생성")
        print("="*80 + "\n")

        print(f"초기 데이터: {len(self.augmented_data)}개")
        print(f"목표: {target}개")
        print(f"생성 필요: {target - len(self.augmented_data)}개\n")

        needed = target - len(self.augmented_data)

        # 생성 전략
        strategies = [
            ("주제 기반 생성", self._generate_topic_based, int(needed * 0.4)),
            ("키워드 기반 생성", self._generate_keyword_based, int(needed * 0.3)),
            ("조합 생성", self._generate_combination, int(needed * 0.3)),
        ]

        for name, method, count in strategies:
            print(f"\n[{name}] 목표: {count}개")
            generated = method(count)
            print(f"  생성: {generated}개")
            self.stats["generated_count"] += generated

        print(f"\n✅ 총 {len(self.generated_data)}개")
        print(f"   초기: {self.stats['initial_count']}개")
        print(f"   생성: {self.stats['generated_count']}개")

        return self.generated_data

    def _generate_topic_based(self, target: int) -> int:
        """주제 기반 생성"""
        generated = 0

        for menu_id, menu_info in self.source_data["menu_structure"].items():
            menu_name = menu_info["name"]

            for topic in menu_info["topics"]:
                topic_name = topic["name"]
                keywords = topic["keywords"]

                # 각 주제당 생성할 개수
                per_topic = max(3, target // len(menu_info["topics"]))

                for _ in range(per_topic):
                    if generated >= target:
                        break

                    # 템플릿 선택
                    template_type = random.choice(["how_to", "what_is", "where", "confirmation"])
                    templates = self.templates["question_templates"][template_type]
                    template = random.choice(templates)

                    # 질문 생성
                    if "{topic}" in template:
                        question = template.replace("{topic}", topic_name)
                    elif "{keyword}" in template:
                        keyword = random.choice(keywords) if keywords else topic_name
                        question = template.replace("{keyword}", keyword)
                    elif "{action}" in template:
                        action = topic_name + (" 조회" if "코드" in topic_name else " 신청")
                        question = template.replace("{action}", action)
                    else:
                        continue

                    # 중복 체크
                    if question in self.seen_questions:
                        continue

                    # 답변 선택 (같은 메뉴의 기존 답변 재사용)
                    if self.menu_answers[menu_id]:
                        answer = random.choice(self.menu_answers[menu_id])

                        # 답변 일부 변형
                        answer = self._adapt_answer(answer, topic_name)

                        self._add_qa(question, answer, menu_id, menu_name, f"topic_{template_type}")
                        generated += 1

        return generated

    def _generate_keyword_based(self, target: int) -> int:
        """키워드 기반 생성"""
        generated = 0

        # 모든 키워드 수집
        all_keywords = []
        for menu_id, menu_info in self.source_data["menu_structure"].items():
            menu_name = menu_info["name"]
            for topic in menu_info["topics"]:
                for keyword in topic["keywords"]:
                    all_keywords.append({
                        "keyword": keyword,
                        "topic": topic["name"],
                        "menu_id": menu_id,
                        "menu_name": menu_name
                    })

        random.shuffle(all_keywords)

        for kw_info in all_keywords:
            if generated >= target:
                break

            keyword = kw_info["keyword"]

            # 키워드 기반 질문 패턴
            patterns = [
                f"{keyword}가 뭔가요?",
                f"{keyword}에 대해 알려주세요",
                f"{keyword}는 어떻게 사용하나요?",
                f"{keyword} 조회 방법",
                f"{keyword} 확인하는 방법",
                f"{keyword}는 어디서 보나요?",
            ]

            for pattern in patterns[:2]:  # 각 키워드당 2개
                if generated >= target:
                    break

                if pattern in self.seen_questions:
                    continue

                # 답변 재사용
                if self.menu_answers[kw_info["menu_id"]]:
                    answer = random.choice(self.menu_answers[kw_info["menu_id"]])
                    answer = self._adapt_answer(answer, keyword)

                    self._add_qa(pattern, answer, kw_info["menu_id"],
                               kw_info["menu_name"], "keyword_based")
                    generated += 1

        return generated

    def _generate_combination(self, target: int) -> int:
        """조합 생성 (여러 키워드/주제 조합)"""
        generated = 0

        for menu_id, menu_info in self.source_data["menu_structure"].items():
            menu_name = menu_info["name"]
            topics = menu_info["topics"]

            if len(topics) < 2:
                continue

            # 두 주제 조합
            for i in range(len(topics) - 1):
                for j in range(i + 1, len(topics)):
                    if generated >= target:
                        break

                    topic1 = topics[i]["name"]
                    topic2 = topics[j]["name"]

                    # 비교 질문 생성
                    comparison_questions = [
                        f"{topic1}와 {topic2}의 차이는?",
                        f"{topic1}와 {topic2} 어떻게 다른가요?",
                        f"{topic1} vs {topic2}",
                    ]

                    for q in comparison_questions[:1]:
                        if q in self.seen_questions:
                            continue

                        # 답변 생성
                        if self.menu_answers[menu_id]:
                            answer = random.choice(self.menu_answers[menu_id])
                            answer = self._adapt_answer(answer, f"{topic1}와 {topic2}")

                            self._add_qa(q, answer, menu_id, menu_name, "combination")
                            generated += 1
                            break

        return generated

    def _adapt_answer(self, answer: str, context: str) -> str:
        """답변을 컨텍스트에 맞게 변형"""
        # 간단한 변형: 일부 표현 교체
        adaptations = {
            "상병코드": context if "코드" in context else "상병코드",
            "환자표본": context if "환자" in context or "표본" in context else "환자표본",
            "데이터": context if "데이터" in context else "데이터",
        }

        adapted = answer
        for old, new in adaptations.items():
            if old in answer and old != new:
                adapted = answer.replace(old, new, 1)
                break

        return adapted

    def _add_qa(self, question: str, answer: str, menu_id: str, menu_name: str, gen_method: str):
        """Q&A 추가"""
        if question not in self.seen_questions:
            self.seen_questions.add(question)

            qa_data = {
                "id": f"hira_{menu_id}_{len(self.generated_data):05d}",
                "instruction": question,
                "input": "",
                "output": answer,
                "metadata": {
                    "menu": menu_id,
                    "menu_name": menu_name,
                    "generation_method": f"template_{gen_method}",
                    "created_at": datetime.now().isoformat(),
                    "question_length": len(question),
                    "answer_length": len(answer)
                }
            }

            self.generated_data.append(qa_data)
            self.stats["by_template_type"][gen_method] += 1
            self.stats["by_menu"][menu_id] += 1

    def save_data(self, output_path: str):
        """데이터 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.generated_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 데이터 저장: {output_path}")
        print(f"   파일 크기: {output_path.stat().st_size:,} bytes")

    def print_statistics(self):
        """통계 출력"""
        print("\n" + "="*80)
        print("📊 생성 통계")
        print("="*80)

        print(f"\n전체:")
        print(f"  총 데이터: {len(self.generated_data)}개")
        print(f"  초기 (규칙 증강): {self.stats['initial_count']}개")
        print(f"  템플릿 생성: {self.stats['generated_count']}개")

        print(f"\n템플릿 유형별:")
        for ttype, count in self.stats["by_template_type"].items():
            pct = (count / self.stats['generated_count']) * 100 if self.stats['generated_count'] else 0
            print(f"  {ttype:20s}: {count:4d}개 ({pct:5.1f}%)")

        print(f"\n메뉴별 분포:")
        sorted_menus = sorted(
            self.stats["by_menu"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for menu_id, count in sorted_menus:
            menu_name = self.source_data["menu_structure"][menu_id]["name"]
            pct = (count / self.stats['generated_count']) * 100 if self.stats['generated_count'] else 0
            print(f"  {menu_name:20s}: {count:4d}개 ({pct:5.1f}%)")


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(description="HIRA 템플릿 기반 데이터 생성")
    parser.add_argument("--input", type=str,
                       default="output/temp/rule_augmented.json",
                       help="입력 파일 (규칙 증강 결과)")
    parser.add_argument("--source", type=str,
                       default="source_data/hira_source.json",
                       help="소스 데이터 (메뉴/주제 정보)")
    parser.add_argument("--template", type=str,
                       default="config/question_templates.yaml",
                       help="질문 템플릿 파일")
    parser.add_argument("--target", type=int, default=5000,
                       help="목표 데이터 수")
    parser.add_argument("--output", type=str,
                       default="output/temp/template_generated.json",
                       help="출력 파일")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("HIRA 템플릿 기반 데이터 생성기 v1.0")
    print("="*80 + "\n")

    # 경로 설정
    base_dir = Path(__file__).parent
    input_path = base_dir / args.input
    source_path = base_dir / args.source
    template_path = base_dir / args.template
    output_path = base_dir / args.output

    # 생성기 초기화
    generator = TemplateBasedGenerator(input_path, source_path, template_path)

    # 생성 실행
    generated_data = generator.generate(target=args.target)

    # 저장
    generator.save_data(output_path)

    # 통계
    generator.print_statistics()

    print("\n" + "="*80)
    print("🎉 템플릿 기반 생성 완료!")
    print("="*80)
    print(f"\n다음 단계: 품질 검증")
    print(f"python3 04_quality_check.py --input {output_path}")


if __name__ == "__main__":
    main()
