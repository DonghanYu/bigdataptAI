# CLAUDE.md - AI Assistant Guide for bigdataptAI Repository

**Last Updated**: 2025-11-17
**Repository**: bigdataptAI - LLM Fine-tuning for Healthcare Data Portal Q&A

---

## 📋 Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Structure](#codebase-structure)
3. [Development Workflows](#development-workflows)
4. [Key Conventions](#key-conventions)
5. [Configuration Guide](#configuration-guide)
6. [Common Tasks](#common-tasks)
7. [Testing & Evaluation](#testing--evaluation)
8. [Troubleshooting](#troubleshooting)
9. [Important Notes for AI Assistants](#important-notes-for-ai-assistants)

---

## Repository Overview

### Purpose
This repository contains a complete LLM fine-tuning pipeline for building domain-specific Q&A systems, specifically focused on:
- **HIRA (Health Insurance Review & Assessment Service)** data queries
- **빅데이터개방포털 (Big Data Portal)** information retrieval

### Project Goals
1. Generate high-quality synthetic training data using template-based approaches
2. Fine-tune SOLAR-10.7B model using LoRA (Low-Rank Adaptation)
3. Minimize hallucination and overfitting through proper validation
4. Deploy a production-ready Q&A inference system

### Technology Stack
- **Language**: Python 3.x
- **ML Framework**: PyTorch, Transformers (Hugging Face)
- **Fine-tuning**: PEFT (Parameter-Efficient Fine-Tuning) with LoRA
- **Base Model**: SOLAR-10.7B (Korean language model)
- **Data Format**: JSONL, YAML, JSON
- **Web Interface**: Flask (for inference API)
- **Hardware**: NVIDIA A100 80GB GPU (training), 24GB+ RAM

### Current Status
- **Data Generation**: ✅ Complete (6,525 high-quality samples)
- **Training Pipeline**: ✅ Implemented with validation
- **Evaluation System**: ✅ BLEU, ROUGE, Perplexity metrics
- **Known Issues**: Hallucination problems being addressed through data quality improvements

---

## Codebase Structure

### Directory Layout

```
bigdataptAI/
├── Root Scripts (Main Pipeline)
│   ├── 01_data_cleaning.py              # Data deduplication & train/val/test split
│   ├── 02_train_with_validation.py      # LoRA training with validation monitoring
│   ├── 03_improved_interface.py         # Flask inference API with confidence scoring
│   ├── 04_evaluate_model.py             # Model evaluation (BLEU, ROUGE, etc.)
│   └── 05_data_augmentation.py          # Data augmentation (paraphrasing, negatives)
│
├── bigdata_portal_learning/             # Data Generation Module
│   ├── config/                          # Configuration files
│   │   ├── menu_structure.yaml          # 8 menus, 170+ topics
│   │   ├── question_templates.yaml      # 100+ Q&A patterns
│   │   ├── hira_menu_structure.yaml     # HIRA-specific menus
│   │   ├── hira_question_templates.yaml # HIRA Q&A templates
│   │   ├── hira_core_qa.yaml            # Core HIRA questions
│   │   └── hira_core_qa_expanded.yaml   # Expanded HIRA dataset
│   │
│   ├── generators/                      # Data generation scripts
│   │   ├── data_generator.py            # Main bigdata portal generator
│   │   ├── hira_sample_generator.py     # HIRA sample generator
│   │   ├── hira_improved_generator.py   # Improved HIRA generator
│   │   ├── hira_full_generator.py       # Full HIRA dataset generator
│   │   ├── expand_core_qa.py            # Core Q&A expander
│   │   └── quality_validator.py         # Data quality validation
│   │
│   ├── output/                          # Generated datasets
│   │   ├── bigdata_portal_train.jsonl   # 6,525 training samples
│   │   ├── bigdata_portal_train_with_metadata.json  # With metadata
│   │   ├── hira_train_final.json        # HIRA final dataset
│   │   └── hira_train_2000.json         # HIRA 2000 samples
│   │
│   └── README.md                        # Generator documentation (Korean)
│
├── Documentation
│   ├── README.md                        # Main project README (minimal)
│   ├── SUMMARY.md                       # Project summary & quick start
│   ├── README_EXECUTION_GUIDE.md        # Step-by-step execution guide
│   ├── improvement_plan.md              # Detailed improvement roadmap
│   └── CLAUDE.md                        # This file - AI assistant guide
│
└── train_solar                          # Training execution script (shell)
```

### Key File Descriptions

#### Root Scripts (Execution Order)

1. **01_data_cleaning.py** (Line count: ~180)
   - **Purpose**: Remove duplicates, filter quality, split datasets
   - **Input**: Raw JSONL data
   - **Output**: `cleaned_data/train.jsonl`, `val.jsonl`, `test.jsonl`
   - **Key Functions**: `clean_data()`, `split_data()`, `get_hash()`
   - **Execution Time**: 1-2 minutes

2. **02_train_with_validation.py** (Line count: ~320)
   - **Purpose**: LoRA fine-tuning with validation monitoring
   - **Input**: Cleaned train/val datasets
   - **Output**: `workspace/models/solar_hira_v3/best_model/`
   - **Key Classes**: `HIRADataset`, training loop with early stopping
   - **Execution Time**: 2-3 hours on A100
   - **Hardware Requirement**: 40GB+ GPU memory

3. **03_improved_interface.py** (Line count: ~370)
   - **Purpose**: Flask web API for inference
   - **Features**: Confidence scoring, conservative generation, hallucination prevention
   - **Port**: 8888
   - **Key Parameters**: `temperature=0.3`, `repetition_penalty=1.15`

4. **04_evaluate_model.py** (Line count: ~280)
   - **Purpose**: Comprehensive model evaluation
   - **Metrics**: BLEU, ROUGE-L, Perplexity, Hallucination Rate
   - **Output**: `workspace/evaluation/evaluation_results.json`
   - **Execution Time**: 10-15 minutes

5. **05_data_augmentation.py** (Line count: ~320)
   - **Purpose**: Expand dataset through paraphrasing and negative sampling
   - **Methods**: Rule-based transformations, optional GPT-4 API
   - **Target**: Expand to 3,000-4,000 samples

#### Data Generator Scripts

Located in `bigdata_portal_learning/generators/`:

1. **data_generator.py** (Line count: ~630)
   - **Class**: `BigDataPortalDataGenerator`
   - **Purpose**: Template-based synthetic data generation
   - **Key Methods**:
     - `generate_all_data(target_count)`: Main generation loop
     - `_generate_menu_data()`: Per-menu generation
     - `_generate_topic_data()`: Per-topic generation with variations
   - **Features**: Automatic deduplication, polite/casual tone variations

2. **quality_validator.py** (Line count: ~240)
   - **Purpose**: Validate generated data quality
   - **Checks**: Empty values, duplicates, template substitution, length distribution
   - **Output**: Quality score (0-100), detailed statistics

3. **hira_*_generator.py** (Multiple files)
   - **Purpose**: HIRA-specific data generation with different strategies
   - **Variants**: Sample (small), Improved (enhanced), Full (complete)

---

## Development Workflows

### 1. Complete Training Pipeline (From Scratch)

```bash
# Step 1: Generate training data
cd bigdata_portal_learning
python3 generators/data_generator.py  # Generates 6,525 samples

# Step 2: Validate data quality
python3 generators/quality_validator.py  # Should show 100/100 score

# Step 3: Clean and split data
cd ..
python3 01_data_cleaning.py  # Creates train/val/test splits

# Step 4: Train model with validation
python3 02_train_with_validation.py  # 2-3 hours on A100

# Step 5: Evaluate model
python3 04_evaluate_model.py  # BLEU, ROUGE, Hallucination metrics

# Step 6: Deploy inference API
python3 03_improved_interface.py  # Start Flask server on port 8888
```

### 2. Data Generation Workflow

```python
# Typical data generation pattern
from bigdata_portal_learning.generators.data_generator import BigDataPortalDataGenerator

# Initialize generator
generator = BigDataPortalDataGenerator(config_dir='bigdata_portal_learning/config')

# Generate data
data = generator.generate_all_data(target_count=7000)

# Save to JSONL
generator.save_to_jsonl(data, 'output/new_train.jsonl')

# Validate quality
from quality_validator import QualityValidator
validator = QualityValidator('output/new_train.jsonl')
score, stats = validator.validate()
```

### 3. Model Training Workflow

Key configuration parameters in `02_train_with_validation.py`:

```python
config = {
    "batch_size": 2,
    "gradient_accumulation_steps": 4,  # Effective batch size = 8
    "learning_rate": 5e-5,
    "num_epochs": 15,
    "max_length": 512,
    "warmup_steps": 100,
    "logging_steps": 10,
    "eval_steps": 50,  # Validation frequency
    "patience": 5,     # Early stopping patience
}

# LoRA configuration
lora_config = LoraConfig(
    r=16,              # Rank
    lora_alpha=32,     # Scaling factor
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    task_type=TaskType.CAUSAL_LM
)
```

### 4. Inference Workflow

```python
# Conservative generation settings (anti-hallucination)
generation_params = {
    'temperature': 0.3,          # Lower = more deterministic
    'top_p': 0.85,               # Nucleus sampling
    'repetition_penalty': 1.15,  # Prevent repetition
    'max_new_tokens': 256,       # Limit response length
    'no_repeat_ngram_size': 3,   # No 3-gram repetition
    'do_sample': True,
    'early_stopping': True
}
```

---

## Key Conventions

### Code Style

1. **File Encoding**: UTF-8 with BOM for all Python files
   ```python
   #!/usr/bin/env python3
   # -*- coding: utf-8 -*-
   ```

2. **Docstring Style**: Korean descriptions with clear purpose statements
   ```python
   """
   데이터 클리닝 및 Train/Val/Test 분할
   - 중복 제거
   - 품질 필터링
   - 전략적 분할
   """
   ```

3. **Logging Style**: Emoji-enhanced progress indicators
   ```python
   print("="*70)
   print("📊 데이터 생성 시작")
   print("="*70)
   print(f"  ├─ 생성 완료: {count}개")
   print(f"  └─ 최종 결과: {total}개")
   ```

4. **Variable Naming**:
   - English: Technical terms (e.g., `tokenizer`, `model`, `dataset`)
   - Korean: Domain-specific (e.g., `menu_structure`, `question_templates`)

### Data Format Conventions

#### JSONL Format (Training Data)
```json
{
  "instruction": "API 키 어떻게 발급받나요?",
  "input": "",
  "output": "API 키는 다음과 같이 발급받으실 수 있습니다: 1) 포털 로그인..."
}
```

#### JSON with Metadata (Review/Debug)
```json
{
  "instruction": "API 키 어떻게 발급받나요?",
  "input": "",
  "output": "API 키는 다음과 같이 발급받으실 수 있습니다...",
  "metadata": {
    "menu": "api_service",
    "topic": "api_key_issue",
    "topic_name": "API 키 발급"
  }
}
```

### YAML Configuration Structure

#### menu_structure.yaml
```yaml
menus:
  menu_key:
    name: "메뉴 이름"
    weight: 1500  # Target number of samples
    topics:
      - id: "topic_id"
        name: "주제 이름"
        keywords: ["키워드1", "키워드2"]
```

#### question_templates.yaml
```yaml
question_patterns:
  basic:
    - "{topic} 알려주세요"
    - "{keyword}에 대해 설명해주세요"

answer_templates:
  basic_answer:
    - "{topic}는 다음과 같습니다: {content}"
```

### File Naming Conventions

- Scripts: `01_data_cleaning.py`, `02_train_*.py` (numbered by execution order)
- Generators: `{domain}_generator.py` (e.g., `hira_full_generator.py`)
- Output: `{domain}_train.jsonl`, `{domain}_train_with_metadata.json`
- Models: `solar_hira_v{version}` (e.g., `solar_hira_v3`)

---

## Configuration Guide

### Environment Paths

The code assumes this directory structure:
```python
WORK_DIR = Path("/home/work/LLM_Meditron/bigdataAI")
MODEL_PATH = WORK_DIR / "solar_10.7b_package" / "model"
DATA_PATH = WORK_DIR / "workspace" / "data" / "hira" / "cleaned_data"
OUTPUT_PATH = WORK_DIR / "workspace" / "models" / "solar_hira_v3"
```

**Important**: When running locally or in different environments, update these paths in:
- `02_train_with_validation.py` (lines 34-37)
- `03_improved_interface.py` (model loading paths)
- `04_evaluate_model.py` (data and model paths)

### GPU Requirements

| Task | GPU Memory | Recommended GPU |
|------|-----------|----------------|
| Data Generation | < 1GB | CPU only |
| Training (LoRA) | 40-50GB | A100 80GB |
| Inference | 20-30GB | A100 40GB / A6000 |
| Evaluation | 20-30GB | A100 40GB / A6000 |

### Memory Optimization

If GPU OOM errors occur:
```python
# Reduce batch size
config['batch_size'] = 1
config['gradient_accumulation_steps'] = 8  # Maintain effective batch size

# Enable gradient checkpointing (add to training script)
model.gradient_checkpointing_enable()

# Use 8-bit quantization (requires bitsandbytes)
# Note: Current code blocks bitsandbytes - remove block if using
```

---

## Common Tasks

### Task 1: Add New Data Topics

**Location**: `bigdata_portal_learning/config/menu_structure.yaml`

```yaml
# Add to existing menu
menus:
  data_search:
    topics:
      - id: "new_topic_id"
        name: "새로운 주제"
        keywords: ["키워드1", "키워드2", "키워드3"]
```

Then regenerate data:
```bash
cd bigdata_portal_learning
python3 generators/data_generator.py
```

### Task 2: Add Question Patterns

**Location**: `bigdata_portal_learning/config/question_templates.yaml`

```yaml
question_patterns:
  custom:
    - "{topic} 어떻게 사용하나요?"
    - "{keyword}에 관해 질문이 있습니다"

answer_templates:
  custom_answer:
    - "{topic}의 사용 방법은 다음과 같습니다: {content}"
```

### Task 3: Modify Training Hyperparameters

**Location**: `02_train_with_validation.py` (lines 50-61)

```python
# Common adjustments
config['learning_rate'] = 3e-5  # Lower for more stable training
config['num_epochs'] = 20       # More epochs if early stopping
config['patience'] = 7          # More patience to avoid premature stopping

# LoRA adjustments
lora_config.r = 32              # Higher rank for more capacity
lora_config.lora_alpha = 64     # Scale with rank (typically 2x)
lora_config.lora_dropout = 0.1  # Higher dropout to prevent overfitting
```

### Task 4: Adjust Inference Temperature

**Location**: `03_improved_interface.py` (generation parameters)

```python
# More conservative (less hallucination, less creative)
temperature = 0.2
top_p = 0.8
repetition_penalty = 1.2

# More creative (more hallucination risk, more varied)
temperature = 0.5
top_p = 0.9
repetition_penalty = 1.1
```

### Task 5: Debug Data Quality Issues

```bash
# Check for duplicates
cd bigdata_portal_learning/output
python3 -c "
import json
seen = set()
dups = 0
with open('bigdata_portal_train.jsonl', 'r') as f:
    for line in f:
        item = json.loads(line)
        key = item['output']
        if key in seen:
            dups += 1
        seen.add(key)
print(f'Duplicates: {dups}')
"

# Validate with quality validator
cd generators
python3 quality_validator.py
```

---

## Testing & Evaluation

### Evaluation Metrics

**BLEU Score** (0-1, higher better)
- Target: > 0.60 for production
- Measures: Translation/generation quality

**ROUGE-L** (0-1, higher better)
- Target: > 0.65 for production
- Measures: Summary quality, overlap with reference

**Perplexity** (lower better)
- Target: < 5.0
- Measures: Language model confidence

**Hallucination Rate** (0-100%, lower better)
- Target: < 15%
- Measures: Factual accuracy

### Running Evaluations

```bash
# Full evaluation on test set
python3 04_evaluate_model.py

# Expected output
{
  "bleu_score": 0.65,
  "rouge_l": 0.68,
  "perplexity": 4.2,
  "hallucination_rate": 12.5,
  "avg_response_length": 104.7
}
```

### Manual Testing Checklist

Test these query types in the inference interface:

1. **Basic Facts**: "1인당 평균 진료비는?"
2. **Definitions**: "DRG가 뭐야?"
3. **Procedures**: "API 키 발급 방법은?"
4. **Out-of-scope** (should refuse): "내일 날씨는?"
5. **Edge Cases**: Very long questions, typos, informal language

---

## Troubleshooting

### Common Issues

#### Issue 1: Training Loss Increases (Overfitting)

**Symptoms**:
- Epoch 1: Loss 0.23 → Epoch 3: Loss 0.67
- Validation loss increases while training loss decreases

**Solutions**:
```python
# 1. Increase regularization
lora_config.lora_dropout = 0.1

# 2. Reduce learning rate
config['learning_rate'] = 3e-5

# 3. Add more data
python3 05_data_augmentation.py

# 4. Early stopping on validation loss (already implemented)
```

#### Issue 2: High Hallucination Rate

**Symptoms**:
- Model generates factually incorrect information
- Answers unrelated to training domain

**Solutions**:
```python
# 1. Lower temperature
temperature = 0.2  # More deterministic

# 2. Increase repetition penalty
repetition_penalty = 1.2

# 3. Add negative samples
# Edit question_templates.yaml to include out-of-scope questions

# 4. Implement RAG (future enhancement)
```

#### Issue 3: GPU Out of Memory

**Symptoms**:
- CUDA OOM error during training

**Solutions**:
```python
# 1. Reduce batch size
config['batch_size'] = 1
config['gradient_accumulation_steps'] = 8

# 2. Reduce max sequence length
config['max_length'] = 384  # From 512

# 3. Enable gradient checkpointing
model.gradient_checkpointing_enable()

# 4. Use smaller LoRA rank
lora_config.r = 8  # From 16
```

#### Issue 4: Data Generation Produces Too Few Samples

**Symptoms**:
- Generated data count < target (e.g., 4,000 instead of 7,000)

**Solutions**:
```python
# 1. Increase max_attempts in data_generator.py
max_attempts = 30  # From 20

# 2. Add more question patterns in question_templates.yaml

# 3. Increase topic weights in menu_structure.yaml
weight: 2000  # From 1500

# 4. Enable additional variations
# Add more tone variations, paraphrases
```

#### Issue 5: Validation Loss Not Improving

**Symptoms**:
- Validation loss plateaus early
- Early stopping triggers too soon

**Solutions**:
```python
# 1. Increase patience
config['patience'] = 7  # From 5

# 2. Adjust learning rate schedule
config['warmup_steps'] = 200  # More gradual warmup

# 3. Check data quality
# Ensure train/val split is proper, no data leakage

# 4. Try different optimizer settings
# Modify optimizer in 02_train_with_validation.py
```

### Debug Mode

Enable verbose logging:
```python
# Add to any script
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use print statements
print(f"DEBUG: {variable_name} = {variable_value}")
```

---

## Important Notes for AI Assistants

### When Making Code Changes

1. **Always Read Before Editing**
   - Use Read tool to view current file state
   - Understand context before modifications
   - Preserve existing structure and conventions

2. **Preserve Korean Comments**
   - Many comments and docstrings are in Korean
   - Do not translate to English unless explicitly requested
   - Maintain bilingual variable names pattern

3. **Path Handling**
   - Be aware of hardcoded paths (`/home/work/LLM_Meditron/bigdataAI`)
   - Suggest path parameterization when making changes
   - Use `Path` from `pathlib` for cross-platform compatibility

4. **Configuration Changes**
   - YAML files are the source of truth for data generation
   - Python scripts contain training hyperparameters
   - Document all parameter changes in commit messages

### When Answering Questions

1. **Refer to Specific Files**
   - Use format: `file_path:line_number`
   - Example: "The training configuration is in 02_train_with_validation.py:51-61"

2. **Provide Context**
   - This is a research/development project, not production code
   - Performance metrics are experimental targets
   - Some features are documented but not fully implemented

3. **Consider Resource Constraints**
   - Training requires expensive GPU resources
   - Data augmentation with GPT-4 API has costs
   - Execution times matter (2-3 hours for training)

### When Implementing New Features

1. **Follow Existing Patterns**
   - Number new pipeline scripts: `06_*.py`, `07_*.py`
   - Place generators in `bigdata_portal_learning/generators/`
   - Use same logging style with emojis

2. **Update Documentation**
   - Add new scripts to this CLAUDE.md
   - Update SUMMARY.md with quick start info
   - Consider updating README_EXECUTION_GUIDE.md

3. **Test Data Pipeline**
   - Generate small sample first (100 items)
   - Validate quality before full generation
   - Check for duplicates and empty values

4. **Model Training Best Practices**
   - Always use train/val/test split
   - Monitor validation loss, not training loss
   - Save checkpoints frequently
   - Log all hyperparameters

### Git Workflow Notes

- **Branch**: Development should occur on `claude/claude-md-mi2ie2w8pz54tz1f-018QZuxyJcpGLfTw5mBi7tS2`
- **Commits**: Use clear, descriptive messages (bilingual OK)
- **Push**: Always use `git push -u origin <branch-name>`
- **Recent Work**: Focus has been on data quality improvements (see commit history)

### Current Project Priorities

Based on SUMMARY.md and improvement_plan.md:

1. **High Priority**: Fix overfitting through better validation
2. **High Priority**: Reduce hallucination rate (<15% target)
3. **Medium Priority**: Data augmentation to 3,000-4,000 samples
4. **Medium Priority**: Implement comprehensive evaluation system
5. **Low Priority**: RAG system integration (future)

---

## Quick Reference

### File Quick Links

| Task | Script | Config File | Output |
|------|--------|-------------|--------|
| Generate Data | `generators/data_generator.py` | `config/menu_structure.yaml` | `output/*.jsonl` |
| Clean Data | `01_data_cleaning.py` | N/A | `cleaned_data/*.jsonl` |
| Train Model | `02_train_with_validation.py` | In-script config dict | `models/solar_hira_v3/` |
| Evaluate | `04_evaluate_model.py` | N/A | `evaluation/*.json` |
| Inference | `03_improved_interface.py` | N/A | Flask API :8888 |

### Key Metrics Targets

| Metric | Current | Target | Excellent |
|--------|---------|--------|-----------|
| BLEU | ~0.55 | 0.60 | 0.70+ |
| ROUGE-L | ~0.60 | 0.65 | 0.70+ |
| Hallucination | ~20% | <15% | <10% |
| Validation Loss | ~0.35 | <0.25 | <0.20 |

### Command Cheat Sheet

```bash
# Generate training data
cd bigdata_portal_learning && python3 generators/data_generator.py

# Full pipeline execution
python3 01_data_cleaning.py && \
python3 02_train_with_validation.py && \
python3 04_evaluate_model.py

# Check data quality
python3 bigdata_portal_learning/generators/quality_validator.py

# Start inference server
python3 03_improved_interface.py

# Monitor GPU usage
watch -n 1 nvidia-smi
```

---

## Version History

- **v1.0** (2025-11-17): Initial CLAUDE.md created with comprehensive documentation
- Project started: 2025-11-12
- Latest data generation: 6,525 samples (quality score: 100/100)

---

## Additional Resources

- **Project Summary**: See `SUMMARY.md` for quick overview
- **Execution Guide**: See `README_EXECUTION_GUIDE.md` for step-by-step instructions
- **Improvement Plan**: See `improvement_plan.md` for detailed roadmap
- **Data Generator Docs**: See `bigdata_portal_learning/README.md` for generation details

---

**For AI Assistants**: This document should be your primary reference when working with this codebase. When in doubt, refer to the actual code files and use the Read tool to verify current implementation details. The project is actively evolving, so always check file timestamps and recent commits.
