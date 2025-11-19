#!/usr/bin/env python3
"""
HIRA 학습 데이터셋 점검 및 통합 스크립트
- Train/Val/Test 데이터 품질 점검
- 중복 제거 및 검증
- 하나의 JSON 파일로 통합
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Any


class HIRADatasetInspector:
    """HIRA 데이터셋 점검 및 통합"""

    def __init__(self, base_path: str = "output/v1.0/full"):
        self.base_path = Path(base_path)
        self.train_data = []
        self.val_data = []
        self.test_data = []
        self.all_data = []

        self.report = {
            "inspection_time": datetime.now().isoformat(),
            "files_processed": [],
            "total_count": 0,
            "duplicates_found": 0,
            "quality_issues": [],
            "statistics": {},
            "merged_output": ""
        }

    def load_datasets(self):
        """데이터셋 파일 로드"""
        print("=" * 60)
        print("📂 데이터셋 파일 로드 중...")
        print("=" * 60)

        files = {
            "train": self.base_path / "train.json",
            "val": self.base_path / "val.json",
            "test": self.base_path / "test.json"
        }

        for split_name, file_path in files.items():
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if split_name == "train":
                    self.train_data = data
                elif split_name == "val":
                    self.val_data = data
                elif split_name == "test":
                    self.test_data = data

                self.report["files_processed"].append({
                    "file": str(file_path),
                    "split": split_name,
                    "count": len(data),
                    "size_kb": file_path.stat().st_size / 1024
                })

                print(f"✓ {split_name:5s}: {len(data):5d}개 ({file_path.stat().st_size/1024:.1f} KB)")
            else:
                print(f"✗ {split_name:5s}: 파일 없음 - {file_path}")

        self.all_data = self.train_data + self.val_data + self.test_data
        self.report["total_count"] = len(self.all_data)

        print(f"\n📊 전체 데이터: {len(self.all_data):,}개")
        print()

    def check_duplicates(self):
        """중복 검사"""
        print("=" * 60)
        print("🔍 중복 검사 중...")
        print("=" * 60)

        # ID 중복 검사
        id_counter = Counter([item["id"] for item in self.all_data])
        duplicates = {id_: count for id_, count in id_counter.items() if count > 1}

        if duplicates:
            print(f"⚠️  중복된 ID 발견: {len(duplicates)}개")
            for id_, count in list(duplicates.items())[:5]:
                print(f"   - {id_}: {count}회")
            if len(duplicates) > 5:
                print(f"   ... 외 {len(duplicates) - 5}개")
            self.report["duplicates_found"] = len(duplicates)
        else:
            print("✓ 중복 없음")
            self.report["duplicates_found"] = 0

        # 질문-답변 조합 중복 검사
        qa_pairs = Counter([
            (item["instruction"], item["output"])
            for item in self.all_data
        ])
        qa_duplicates = {pair: count for pair, count in qa_pairs.items() if count > 1}

        if qa_duplicates:
            print(f"⚠️  동일한 Q&A 조합 발견: {len(qa_duplicates)}개")
            self.report["quality_issues"].append({
                "type": "duplicate_qa_pairs",
                "count": len(qa_duplicates)
            })
        else:
            print("✓ Q&A 조합 중복 없음")

        print()

    def validate_structure(self):
        """데이터 구조 검증"""
        print("=" * 60)
        print("🔧 데이터 구조 검증 중...")
        print("=" * 60)

        required_fields = ["id", "instruction", "input", "output", "metadata"]
        metadata_fields = ["menu", "menu_name", "generation_method", "created_at"]

        missing_fields = defaultdict(int)
        missing_metadata = defaultdict(int)
        empty_instructions = 0
        empty_outputs = 0

        for idx, item in enumerate(self.all_data):
            # 필수 필드 확인
            for field in required_fields:
                if field not in item:
                    missing_fields[field] += 1

            # 메타데이터 필드 확인
            if "metadata" in item:
                for field in metadata_fields:
                    if field not in item["metadata"]:
                        missing_metadata[field] += 1

            # 빈 값 확인
            if not item.get("instruction", "").strip():
                empty_instructions += 1
            if not item.get("output", "").strip():
                empty_outputs += 1

        if missing_fields:
            print("⚠️  필수 필드 누락:")
            for field, count in missing_fields.items():
                print(f"   - {field}: {count}개")
            self.report["quality_issues"].append({
                "type": "missing_required_fields",
                "details": dict(missing_fields)
            })
        else:
            print("✓ 모든 필수 필드 존재")

        if missing_metadata:
            print("⚠️  메타데이터 필드 누락:")
            for field, count in missing_metadata.items():
                print(f"   - {field}: {count}개")
            self.report["quality_issues"].append({
                "type": "missing_metadata_fields",
                "details": dict(missing_metadata)
            })
        else:
            print("✓ 모든 메타데이터 필드 존재")

        if empty_instructions > 0:
            print(f"⚠️  빈 질문(instruction): {empty_instructions}개")
            self.report["quality_issues"].append({
                "type": "empty_instructions",
                "count": empty_instructions
            })
        else:
            print("✓ 빈 질문 없음")

        if empty_outputs > 0:
            print(f"⚠️  빈 답변(output): {empty_outputs}개")
            self.report["quality_issues"].append({
                "type": "empty_outputs",
                "count": empty_outputs
            })
        else:
            print("✓ 빈 답변 없음")

        print()

    def calculate_statistics(self):
        """통계 계산"""
        print("=" * 60)
        print("📊 통계 분석 중...")
        print("=" * 60)

        # 메뉴별 분포
        menu_dist = Counter([item["metadata"]["menu"] for item in self.all_data])

        # 생성 방법별 분포
        gen_method_dist = Counter([
            item["metadata"].get("generation_method", "unknown")
            for item in self.all_data
        ])

        # 품질 점수 통계
        quality_scores = [
            item["metadata"].get("quality_score", 0)
            for item in self.all_data
        ]

        # 길이 통계
        question_lengths = [len(item["instruction"]) for item in self.all_data]
        answer_lengths = [len(item["output"]) for item in self.all_data]

        stats = {
            "menu_distribution": dict(menu_dist),
            "generation_method_distribution": dict(gen_method_dist),
            "quality_scores": {
                "min": min(quality_scores) if quality_scores else 0,
                "max": max(quality_scores) if quality_scores else 0,
                "avg": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "count_high": sum(1 for s in quality_scores if s >= 0.7),
                "count_medium": sum(1 for s in quality_scores if 0.6 <= s < 0.7),
                "count_low": sum(1 for s in quality_scores if s < 0.6)
            },
            "question_length": {
                "min": min(question_lengths),
                "max": max(question_lengths),
                "avg": sum(question_lengths) / len(question_lengths)
            },
            "answer_length": {
                "min": min(answer_lengths),
                "max": max(answer_lengths),
                "avg": sum(answer_lengths) / len(answer_lengths)
            },
            "split_distribution": {
                "train": len(self.train_data),
                "val": len(self.val_data),
                "test": len(self.test_data),
                "total": len(self.all_data)
            }
        }

        self.report["statistics"] = stats

        # 출력
        print(f"📂 데이터셋 분할:")
        print(f"   - Train: {stats['split_distribution']['train']:5d}개 ({stats['split_distribution']['train']/stats['split_distribution']['total']*100:.1f}%)")
        print(f"   - Val:   {stats['split_distribution']['val']:5d}개 ({stats['split_distribution']['val']/stats['split_distribution']['total']*100:.1f}%)")
        print(f"   - Test:  {stats['split_distribution']['test']:5d}개 ({stats['split_distribution']['test']/stats['split_distribution']['total']*100:.1f}%)")
        print(f"   - Total: {stats['split_distribution']['total']:5d}개")

        print(f"\n📋 메뉴별 분포:")
        for menu, count in sorted(menu_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {menu:20s}: {count:5d}개 ({count/len(self.all_data)*100:5.1f}%)")

        print(f"\n🔧 생성 방법별 분포:")
        for method, count in sorted(gen_method_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {method:25s}: {count:5d}개 ({count/len(self.all_data)*100:5.1f}%)")

        print(f"\n⭐ 품질 점수:")
        print(f"   - 최소: {stats['quality_scores']['min']:.2f}")
        print(f"   - 최대: {stats['quality_scores']['max']:.2f}")
        print(f"   - 평균: {stats['quality_scores']['avg']:.2f}")
        print(f"   - 고품질 (≥0.7): {stats['quality_scores']['count_high']:5d}개 ({stats['quality_scores']['count_high']/len(self.all_data)*100:5.1f}%)")
        print(f"   - 중품질 (0.6~0.7): {stats['quality_scores']['count_medium']:5d}개 ({stats['quality_scores']['count_medium']/len(self.all_data)*100:5.1f}%)")
        print(f"   - 저품질 (<0.6): {stats['quality_scores']['count_low']:5d}개 ({stats['quality_scores']['count_low']/len(self.all_data)*100:5.1f}%)")

        print(f"\n📏 질문 길이:")
        print(f"   - 최소: {stats['question_length']['min']}자")
        print(f"   - 최대: {stats['question_length']['max']}자")
        print(f"   - 평균: {stats['question_length']['avg']:.1f}자")

        print(f"\n📝 답변 길이:")
        print(f"   - 최소: {stats['answer_length']['min']}자")
        print(f"   - 최대: {stats['answer_length']['max']}자")
        print(f"   - 평균: {stats['answer_length']['avg']:.1f}자")

        print()

    def merge_and_save(self, output_dir: str = "output/merge_final_data"):
        """데이터 통합 및 저장"""
        print("=" * 60)
        print("💾 데이터 통합 및 저장 중...")
        print("=" * 60)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 통합 데이터 저장 (각 split 정보 포함)
        merged_data = []

        for item in self.train_data:
            item_copy = item.copy()
            item_copy["split"] = "train"
            merged_data.append(item_copy)

        for item in self.val_data:
            item_copy = item.copy()
            item_copy["split"] = "val"
            merged_data.append(item_copy)

        for item in self.test_data:
            item_copy = item.copy()
            item_copy["split"] = "test"
            merged_data.append(item_copy)

        # 메인 통합 파일
        merged_file = output_path / "hira_merged_dataset.json"
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 통합 데이터셋 저장: {merged_file}")
        print(f"  - 총 {len(merged_data):,}개 항목")
        print(f"  - 파일 크기: {merged_file.stat().st_size / 1024:.1f} KB")

        # Split별로도 저장 (원본 그대로)
        splits_dir = output_path / "splits"
        splits_dir.mkdir(exist_ok=True)

        for split_name, data in [("train", self.train_data), ("val", self.val_data), ("test", self.test_data)]:
            split_file = splits_dir / f"{split_name}.json"
            with open(split_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ {split_name} 데이터: {split_file} ({len(data):,}개)")

        # 검사 리포트 저장
        report_file = output_path / "inspection_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)

        print(f"✓ 검사 리포트 저장: {report_file}")

        # README 생성
        readme_file = output_path / "README.md"
        readme_content = self._generate_readme()
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"✓ README 저장: {readme_file}")

        self.report["merged_output"] = str(merged_file)

        print()

    def _generate_readme(self) -> str:
        """README 생성"""
        stats = self.report["statistics"]

        readme = f"""# HIRA 학습 데이터셋 (최종 통합본)

## 📊 데이터셋 개요

- **생성일시**: {self.report["inspection_time"]}
- **총 데이터 수**: {self.report["total_count"]:,}개
- **Train/Val/Test 분할**: {stats['split_distribution']['train']}/{stats['split_distribution']['val']}/{stats['split_distribution']['test']}

## 📁 파일 구조

```
merge_final_data/
├── hira_merged_dataset.json      # 전체 통합 데이터 (split 정보 포함)
├── inspection_report.json        # 데이터 검사 리포트
├── README.md                      # 이 파일
└── splits/                        # Split별 데이터
    ├── train.json
    ├── val.json
    └── test.json
```

## 📋 데이터 통계

### 데이터셋 분할
- **Train**: {stats['split_distribution']['train']:,}개 ({stats['split_distribution']['train']/stats['split_distribution']['total']*100:.1f}%)
- **Val**: {stats['split_distribution']['val']:,}개 ({stats['split_distribution']['val']/stats['split_distribution']['total']*100:.1f}%)
- **Test**: {stats['split_distribution']['test']:,}개 ({stats['split_distribution']['test']/stats['split_distribution']['total']*100:.1f}%)

### 메뉴별 분포
"""
        for menu, count in sorted(stats['menu_distribution'].items(), key=lambda x: x[1], reverse=True):
            readme += f"- **{menu}**: {count:,}개 ({count/self.report['total_count']*100:.1f}%)\n"

        readme += f"""
### 생성 방법별 분포
"""
        for method, count in sorted(stats['generation_method_distribution'].items(), key=lambda x: x[1], reverse=True):
            readme += f"- **{method}**: {count:,}개 ({count/self.report['total_count']*100:.1f}%)\n"

        readme += f"""
### 품질 점수
- **평균**: {stats['quality_scores']['avg']:.2f}
- **최소**: {stats['quality_scores']['min']:.2f}
- **최대**: {stats['quality_scores']['max']:.2f}
- **고품질 (≥0.7)**: {stats['quality_scores']['count_high']:,}개 ({stats['quality_scores']['count_high']/self.report['total_count']*100:.1f}%)
- **중품질 (0.6~0.7)**: {stats['quality_scores']['count_medium']:,}개 ({stats['quality_scores']['count_medium']/self.report['total_count']*100:.1f}%)
- **저품질 (<0.6)**: {stats['quality_scores']['count_low']:,}개 ({stats['quality_scores']['count_low']/self.report['total_count']*100:.1f}%)

### 텍스트 길이
- **질문 평균**: {stats['question_length']['avg']:.1f}자 (범위: {stats['question_length']['min']}~{stats['question_length']['max']}자)
- **답변 평균**: {stats['answer_length']['avg']:.1f}자 (범위: {stats['answer_length']['min']}~{stats['answer_length']['max']}자)

## ✅ 품질 검사 결과

- **중복 ID**: {self.report['duplicates_found']}개
- **품질 이슈**: {len(self.report['quality_issues'])}건

## 📖 데이터 형식

```json
{{
  "id": "hira_menu_xxxxx",
  "instruction": "질문 내용",
  "input": "",
  "output": "답변 내용",
  "split": "train|val|test",
  "metadata": {{
    "menu": "메뉴 ID",
    "menu_name": "메뉴 이름",
    "generation_method": "생성 방법",
    "created_at": "생성 시간",
    "question_length": 질문_길이,
    "answer_length": 답변_길이,
    "quality_score": 품질_점수
  }}
}}
```

## 🚀 사용 방법

### Python으로 로드
```python
import json

# 전체 통합 데이터 로드
with open('hira_merged_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Split별로 필터링
train_data = [item for item in data if item['split'] == 'train']
val_data = [item for item in data if item['split'] == 'val']
test_data = [item for item in data if item['split'] == 'test']
```

### 특정 Split 로드
```python
# 개별 split 파일 로드
with open('splits/train.json', 'r', encoding='utf-8') as f:
    train_data = json.load(f)
```

## 📝 생성 과정

1. **소스 데이터 분석**: 323개 Q&A 쌍
2. **규칙 기반 증강**: 323 → 1,064개 (3.3배)
3. **템플릿 기반 생성**: 1,064 → 3,032개
4. **품질 필터링**: 3,032 → 1,423개 (통과율 46.9%)
5. **데이터셋 분할**: Train/Val/Test = 80/10/10
6. **최종 검증 및 통합**: {self.report['total_count']:,}개

---

*Generated by HIRA Dataset Inspector v1.0*
*{self.report["inspection_time"]}*
"""
        return readme

    def run_full_inspection(self, output_dir: str = "output/merge_final_data"):
        """전체 검사 실행"""
        self.load_datasets()
        self.check_duplicates()
        self.validate_structure()
        self.calculate_statistics()
        self.merge_and_save(output_dir)

        print("=" * 60)
        print("✅ 검사 및 통합 완료!")
        print("=" * 60)
        print(f"📂 출력 디렉토리: {output_dir}")
        print(f"📊 총 데이터: {self.report['total_count']:,}개")
        print(f"⚠️  중복: {self.report['duplicates_found']}개")
        print(f"⚠️  품질 이슈: {len(self.report['quality_issues'])}건")
        print("=" * 60)


def main():
    inspector = HIRADatasetInspector(
        base_path="hira_training_datasets/output/v1.0/full"
    )

    inspector.run_full_inspection(
        output_dir="hira_training_datasets/output/merge_final_data"
    )


if __name__ == "__main__":
    main()
