---
description: Chay benchmark framework — do overhead, chat luong, va hieu qua tung feature
---

Chay benchmark suite cho framework. Argument: `--overhead`, `--metrics`, `--compare`, `--scenarios`, `--all` (default), `--export csv`.

## Cach chay

```bash
# Chay tat ca benchmarks
python .claude/scripts/benchmark.py

# Chi do overhead (tu dong, nhanh)
python .claude/scripts/benchmark.py --overhead

# Phan tich metrics tu events.jsonl (can co sessions truoc)
python .claude/scripts/benchmark.py --metrics --days 30

# So sanh feature cost vs value
python .claude/scripts/benchmark.py --compare

# In A/B test scenarios (guide thu cong)
python .claude/scripts/benchmark.py --scenarios

# Export CSV
python .claude/scripts/benchmark.py --all --export csv
```

## 3 loai benchmark

### 1. Token Overhead (tu dong)
Do framework tieu ton bao nhieu tokens:
- **Eager baseline**: files luon load moi session (CLAUDE.md, PROJECT_MAP, project_state, HALLUCINATION_RULES)
- **Typical session**: eager + ~30% lazy files + ~40% skills
- **Max possible**: tat ca files load
- **Overhead %**: so voi budget 120K tokens

### 2. Quality & Productivity Metrics (tu dong, can data)
Phan tich tu `events.jsonl` (tich luy qua cac sessions):
- **Sessions**: avg tokens, cost, cache hit, rotate rate
- **Quality**: HRS scores (GREEN/RED rate), hook block rate, top block rules
- **Productivity**: loop retries per session, unclosed task warnings

### 3. Feature Cost vs Value (tu dong)
So sanh tung feature moi:
- **Skills vs Full Rules**: bao nhieu tokens tiet kiem khi dung progressive disclosure
- **Code Graph vs File Reading**: bao nhieu tokens tiet kiem khi query graph thay vi doc file
- **6D Classification**: overhead mot lan de chon dung methodology
- **Task Tracker**: overhead de chong Agent Amnesia

### 4. A/B Test Scenarios (thu cong)
5 test scenarios de so sanh WITH framework vs WITHOUT:
- Small bug fix, Medium feature, Investigation, Large epic, Legacy codebase
- Scoring matrix: token efficiency (25%), code quality (25%), completion rate (20%), time (15%), state preservation (15%)

## Khi nao chay benchmark

| Thoi diem | Benchmark nao |
|-----------|--------------|
| Sau setup framework | `--overhead` (verify overhead chap nhan duoc) |
| Sau 5+ sessions | `--metrics` (du data de phan tich) |
| Khi can justify framework | `--all --export csv` (bao cao day du) |
| Khi them/sua feature | `--compare` (verify ROI feature moi) |
| Khi onboard team moi | `--scenarios` (A/B test de chung minh gia tri) |
