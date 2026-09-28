# LLM Data Fusion Pipeline

Official code for the paper:

> **Single and Multi Truth Data Fusion using Large Language Models**  
> Hira Beril Kucuk, Norman W Paton, Jiaoyan Chen, Zhenyu Wu  
> Department of Computer Science, University of Manchester

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

This pipeline uses Large Language Models (LLMs) to resolve conflicting values from multiple sources — a problem known as data fusion or truth discovery. It supports both **multi-truth** settings (book authors, movie directors) and **single-truth** settings (flight departure/arrival times and gates).

Every prompt is one of 8 combinations, each run at 0-shot and 1-shot:

```
<DD|DI> - <RW|CW> - <ST|MT>
```

- **DD (Domain-Dependent) vs DI (Domain-Independent)** — DD prompts use real attribute names (author, director, departure time); DI prompts use generic labels (Attribute 1, Attribute 2, ...) and apply unchanged across domains.
- **RW (Row-Wise) vs CW (Column-Wise)** — RW merges every attribute of an entity into one LLM call; CW resolves one attribute per call.
- **ST (Single-Truth) vs MT (Multi-Truth)** — ST prompts assume one correct value per attribute; MT prompts allow several (semicolon-separated). ST prompts can be run on MT data (treating the value set as one value) and vice versa — this cross-application is how the paper tests whether matching the prompt to the data's real nature beats mismatching it.


LLM-based prompts outperform all traditional truth discovery baselines (DART, LTM, MV, SRV) across all datasets. See the paper for full results.

## Datasets

Three benchmark datasets are used:

| Dataset | Type | Task |
|---------|------|------|
| Book | Multi-truth | Predict correct author(s) from conflicting seller records |
| Movie | Multi-truth | Predict correct director(s) from conflicting source records |
| Flight | Single-truth | Predict correct departure/arrival times and gates |

Datasets are publicly available at:
- Book & Flight: https://lunadong.com/fusiondatasets
- Movie: https://heathersherry.github.io/

Set the paths to your local copies in `config.py`.

## Setup

### Prerequisites

- Python 3.9+
- An OpenAI or Anthropic API key

### 1. Install dependencies

```bash
pip install openai anthropic
```

### 2. Configure API keys

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 3. Set data paths

Edit `config.py` and set the paths to your dataset files:

```python
BOOK_CLAIMS_PATH   = ""  # path to book claims file
BOOK_TRUTH_PATH    = ""  # path to book truth file
MOVIE_CLAIMS_PATH  = ""  # path to movie claims file
MOVIE_TRUTH_PATH   = ""  # path to movie truth file
FLIGHT_CLAIMS_PATH = ""  # path to flight claims file
FLIGHT_TRUTH_PATH  = ""  # path to flight truth file
```

### 4. Set the LLM model

```python
LLM_PROVIDER = "openai"       # "openai" | "anthropic"
LLM_MODEL    = "gpt-4o-mini"  # e.g. "gpt-4o", "claude-sonnet-4-6"
```

Primary experiments in the paper use `gpt-4o-mini`. Results with `gpt-4o` and `claude-sonnet-4-6` (best-performing configuration per dataset) are also reported in Table 3.

## Running Experiments

```bash
python run.py --dataset book
python run.py --dataset movie
python run.py --dataset flight
python run.py --dataset flight_blind
python run.py --dataset all
```

Each combination writes 3 files to `results/`:
- `metrics_<model>_<style>_<dataset>_<ts>.txt` — Recall/Precision/F1
- `detail_<model>_<style>_<dataset>_<ts>.{csv,txt}` — per-entity/per-attribute breakdown
- `raw_<model>_<style>_<dataset>_<ts>.txt` — the LLM's raw (unparsed) response

`flight_blind` corresponds to the paper's "Obfuscated Flight ID" experiment: real flight IDs (e.g. `AA-1007-MIA-PHX`) are replaced with anonymous ones (`FLIGHT-001`, ...) before being shown to the LLM, to check whether the model relies on background knowledge of real flight timetables rather than the source data in the prompt. 

## Prompt Variants

Each experiment runs all combinations of:

| Dimension | Options |
|-----------|---------|
| Domain | Domain-Dependent (DD), Domain-Independent (DI) |
| Layout | Row-Wise (RW), Column-Wise (CW) |
| Truth  | Single-Truth (ST), Multi-Truth (MT) |
| Shot   | 0-shot, 1-shot |

## Repository Structure

```
├── config.py                    # Paths, LLM settings, prompt style
├── data/
│   ├── loader.py                # Load raw claims (book, movie, flight)
│   └── normalizer.py            # Text normalization
├── evaluation/
│   ├── truth_loader.py          # Load ground truth
│   └── metrics.py               # Recall/Precision/F1 (token-based & exact-match)
├── llm/
│   ├── client.py                # OpenAI and Anthropic API calls
│   ├── prompt_builder.py        # All prompt variants (DD/DI × RW/CW × ST/MT × shot)
│   ├── parser.py                # Parse LLM responses (book, movie)
│   └── parser_flight.py         # Parse LLM responses (flight)
└── run.py                       # Run all experiments (book, movie, flight)
```

## Citation

If you use this code in your research, please cite the paper above.

```bibtex
```
