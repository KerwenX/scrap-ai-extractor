# Hybrid Web Extractor

`Hybrid Web Extractor` is a parsing-focused MVP for structured extraction from existing web pages.

This project does not include crawler responsibilities. It assumes the caller already has:

- `url`
- `raw_html`
- a natural-language extraction prompt

The system focuses on large-scale parsing needs where the same site may contain multiple page scenarios and templates.

## Core approach

- First-seen templates use LLM-based semantic parsing
- Known templates use deterministic parsers first
- Validation failures or template drift trigger LLM fallback
- Output includes parsed data, template metadata, validation status, and debug trace
- Successful fallback runs can persist reusable template candidates for later solidification
- Solidification supports two modes:
  - declarative field-rule DSL first
  - code-based parsing hooks as fallback for hard cases

## Current scope

- Single-page HTML parsing
- Site-aware and scenario-aware template matching
- Deterministic parsing for known templates
- LLM fallback for unknown or invalid cases
- Request-level logging

Current built-in site scenarios:

- `dayi / disease_detail`
- `dayi / qa_detail`

## Service layout

The project now separates responsibilities into:

- `controllers/`: request/response orchestration
- `services/`: template storage and extraction dispatch
- `engine.py`: parsing workflow
- `classification.py`: site and page-scenario recognition
- `fingerprinting.py`: portable page signatures for template reuse
- `rule_runtime.py`: executes declarative field rules

This is intended to make future solidified parsing logic portable across machines by storing manifests and candidates as JSON files.

## Project layout

```text
docs/                         requirements and architecture
config/templates/             template metadata
src/hybrid_extractor/         parser engine and template parsers
tests/                        unit tests
local_medical_html_extraction.py
```

## Install

```powershell
pip install -e .
```

For tests:

```powershell
pip install -e .[dev]
pytest
```

## Run

```powershell
python .\local_medical_html_extraction.py --html-path "E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html"
```

Or via CLI:

```powershell
hybrid-web-extractor --html-path "E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html" --url "https://www.dayi.org.cn/symptom/..." --prompt "提取疾病基本信息、病因、症状、诊断、治疗、日常注意事项和预防"
```

Optional file output:

```powershell
hybrid-web-extractor ... --output-file result.json
```

## Local API

Start a local parsing API:

```powershell
@'
from hybrid_extractor.api_server import run_server
run_server()
'@ | python -
```

Endpoints:

- `POST /extract`
- `GET /templates`

## Prompt strategy

The extraction request is split into two layers:

- user prompt: business intent only, such as fields or output goals
- internal prompt contract: concise system rules for JSON-only output, evidence grounding, stable field naming, and reusable template thinking

Current implementation keeps these internal constraints in `src/hybrid_extractor/prompts.py` so prompt behavior can evolve without requiring callers to rewrite their business prompts.

For template solidification, the runtime is now modeled as two stages:

- analysis stage: identify stable anchors, field shapes, repeatable sections, and weak deterministic candidates
- DSL stage: generate a reusable declarative extraction plan from that analysis

The first version stores both artifacts in template candidate files for later review and hardening.

## Documents

- [Requirements](G:\code\Extractor\scrap-ai-extractor\docs\requirements.md)
- [Architecture](G:\code\Extractor\scrap-ai-extractor\docs\architecture.md)
