#!/usr/bin/env python3
"""
기존 YAML 데이터를 JSON 규격으로 변환
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class YAMLtoJSONConverter:
    """YAML 데이터를 JSON으로 변환"""

    def __init__(self):
        self.base_path = Path("/home/user/bigdataptAI/bigdata_portal_learning/config")
        self.output_data = {
            "site_info": {
                "url": "https://opendata.hira.or.kr",
                "source": "Manual curation",
                "converted_at": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "menu_structure": {},
            "core_qa": {},
            "statistics": {}
        }

    def convert(self):
        """변환 실행"""
        print("="*80)
        print("HIRA 데이터 YAML → JSON 변환")
        print("="*80 + "\n")

        # 1. 메뉴 구조 변환
        print("[1/3] 메뉴 구조 변환 중...")
        self._convert_menu_structure()

        # 2. 핵심 Q&A 변환
        print("\n[2/3] 핵심 Q&A 변환 중...")
        self._convert_core_qa()

        # 3. 통계 생성
        print("\n[3/3] 통계 생성 중...")
        self._generate_statistics()

        print("\n" + "="*80)
        print("✅ 변환 완료!")
        print("="*80)

    def _convert_menu_structure(self):
        """메뉴 구조 변환"""
        try:
            menu_file = self.base_path / "hira_menu_structure.yaml"
            if not menu_file.exists():
                print(f"   ⚠️ 파일 없음: {menu_file}")
                return

            with open(menu_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'menus' not in data:
                print("   ⚠️ 'menus' 키가 없습니다")
                return

            # 메뉴 구조 변환
            menu_structure = {}
            total_topics = 0

            for menu_id, menu_info in data['menus'].items():
                topics = menu_info.get('topics', [])
                total_topics += len(topics)

                menu_structure[menu_id] = {
                    "id": menu_id,
                    "name": menu_info.get('name', ''),
                    "weight": menu_info.get('weight', 0),
                    "topics_count": len(topics),
                    "topics": [
                        {
                            "id": topic.get('id', ''),
                            "name": topic.get('name', ''),
                            "keywords": topic.get('keywords', [])
                        }
                        for topic in topics
                    ]
                }

            self.output_data["menu_structure"] = menu_structure

            print(f"   메뉴: {len(menu_structure)}개")
            print(f"   주제: {total_topics}개")

        except Exception as e:
            print(f"   ⚠️ 변환 오류: {e}")
            import traceback
            traceback.print_exc()

    def _convert_core_qa(self):
        """핵심 Q&A 변환"""
        try:
            # 두 파일 시도
            qa_files = [
                self.base_path / "hira_core_qa_expanded.yaml",
                self.base_path / "hira_core_qa.yaml"
            ]

            qa_file = None
            for f in qa_files:
                if f.exists():
                    qa_file = f
                    break

            if not qa_file:
                print("   ⚠️ Q&A 파일 없음")
                return

            print(f"   파일: {qa_file.name}")

            with open(qa_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'core_qa' not in data:
                print("   ⚠️ 'core_qa' 키가 없습니다")
                return

            # Q&A 변환
            core_qa = {}
            total_qa = 0

            for menu_id, qa_list in data['core_qa'].items():
                converted_qa = []

                for item in qa_list:
                    converted_qa.append({
                        "question": item.get('q', ''),
                        "answer": item.get('a', ''),
                        "question_length": len(item.get('q', '')),
                        "answer_length": len(item.get('a', ''))
                    })
                    total_qa += 1

                core_qa[menu_id] = {
                    "menu_id": menu_id,
                    "qa_count": len(converted_qa),
                    "qa_pairs": converted_qa
                }

            self.output_data["core_qa"] = core_qa

            print(f"   메뉴: {len(core_qa)}개")
            print(f"   Q&A: {total_qa}쌍")

        except Exception as e:
            print(f"   ⚠️ 변환 오류: {e}")
            import traceback
            traceback.print_exc()

    def _generate_statistics(self):
        """통계 생성"""
        try:
            stats = {
                "total_menus": len(self.output_data["menu_structure"]),
                "total_topics": sum(
                    menu["topics_count"]
                    for menu in self.output_data["menu_structure"].values()
                ),
                "total_qa_groups": len(self.output_data["core_qa"]),
                "total_qa_pairs": sum(
                    qa["qa_count"]
                    for qa in self.output_data["core_qa"].values()
                ),
            }

            # Q&A 길이 통계
            all_questions = []
            all_answers = []

            for qa_group in self.output_data["core_qa"].values():
                for item in qa_group["qa_pairs"]:
                    all_questions.append(item["question_length"])
                    all_answers.append(item["answer_length"])

            if all_questions:
                stats["question_stats"] = {
                    "avg_length": sum(all_questions) / len(all_questions),
                    "min_length": min(all_questions),
                    "max_length": max(all_questions)
                }

            if all_answers:
                stats["answer_stats"] = {
                    "avg_length": sum(all_answers) / len(all_answers),
                    "min_length": min(all_answers),
                    "max_length": max(all_answers)
                }

            self.output_data["statistics"] = stats

            print(f"   메뉴: {stats['total_menus']}개")
            print(f"   주제: {stats['total_topics']}개")
            print(f"   Q&A: {stats['total_qa_pairs']}쌍")

            if "question_stats" in stats:
                print(f"   질문 평균 길이: {stats['question_stats']['avg_length']:.1f}자")

            if "answer_stats" in stats:
                print(f"   답변 평균 길이: {stats['answer_stats']['avg_length']:.1f}자")

        except Exception as e:
            print(f"   ⚠️ 통계 생성 오류: {e}")

    def save_json(self, output_path: str):
        """전체 JSON 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.output_data, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size
        print(f"\n✅ JSON 저장 완료: {output_path}")
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    def save_summary(self, output_path: str):
        """요약 JSON 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = {
            "summary": {
                "source": "HIRA manual curation",
                "converted_at": self.output_data["site_info"]["converted_at"],
                "statistics": self.output_data["statistics"]
            },
            "menu_list": [
                {
                    "id": menu["id"],
                    "name": menu["name"],
                    "topics": menu["topics_count"]
                }
                for menu in self.output_data["menu_structure"].values()
            ],
            "qa_list": [
                {
                    "menu_id": qa["menu_id"],
                    "qa_count": qa["qa_count"],
                    "sample_qa": qa["qa_pairs"][:3]  # 처음 3개만
                }
                for qa in self.output_data["core_qa"].values()
            ],
            "full_data": self.output_data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size
        print(f"✅ 요약 JSON 저장 완료: {output_path}")
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    def save_qa_only(self, output_path: str):
        """Q&A만 저장 (학습용)"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        qa_list = []

        for qa_group in self.output_data["core_qa"].values():
            for item in qa_group["qa_pairs"]:
                qa_list.append({
                    "instruction": item["question"],
                    "input": "",
                    "output": item["answer"]
                })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(qa_list, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size
        print(f"✅ Q&A 학습용 JSON 저장 완료: {output_path}")
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"   Q&A 쌍: {len(qa_list)}개")


def main():
    """메인 실행"""
    print("\n" + "="*80)
    print("HIRA YAML → JSON 변환기 v1.0")
    print("="*80 + "\n")

    converter = YAMLtoJSONConverter()

    try:
        # 변환 실행
        converter.convert()

        # 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("/home/user/bigdataptAI/hira_crawler/output")
        output_dir.mkdir(exist_ok=True)

        # 1. 전체 데이터
        converter.save_json(output_dir / f"hira_data_from_yaml_{timestamp}.json")

        # 2. 요약 데이터
        converter.save_summary(output_dir / f"hira_summary_from_yaml_{timestamp}.json")

        # 3. Q&A만 (학습용)
        converter.save_qa_only(output_dir / f"hira_qa_training_{timestamp}.json")

        print("\n" + "="*80)
        print("🎉 모든 작업 완료!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
