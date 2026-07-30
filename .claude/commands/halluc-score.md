---
name: halluc-score
description: Compute Hallucination Risk Score (HRS) — 7 signals, trigger-only
---

# /halluc-score — Hallucination Risk Score

Tính HRS composite từ 7 signal proxy. **CHỈ chạy khi user trigger** (KHÔNG tự động trong PreToolUse / PostToolUse) — tránh slow workflow.

## Khi nào dùng

- Sau Phase 3 nếu thấy nghi ngờ (Claude tự cite source kém, hoặc schema-check phát hiện field lạ)
- Khi `consecutive_failures` >= 2 (Loop Logic loop nhiều lần)
- Định kỳ đầu/cuối session lớn (sanity check)
- User cảm thấy output có mùi hallucinate

## Cách Claude phải execute

Khi user gõ `/halluc-score`:

1. **Run script** theo hook stack hiện tại (xem `.claude/settings.json`):
   - Python (default): `python .claude/hooks/python/halluc-score.py`
   - Bash:             `bash .claude/hooks/bash/halluc-score.sh`
   - Node:             `node .claude/hooks/nodejs/halluc-score.js`

   > Tokens auto-resolve theo thứ tự: `--tokens N` (nếu pass) > cache `.claude/cache/last_tokens.json` (statusline ghi mỗi refresh) > fallback estimate `len(content)//4`. Output report ghi rõ `token_source` để debug.

2. **Parse output**, đọc:
   - `hrs` (overall score)
   - `color` (GREEN / YELLOW / ORANGE / RED)
   - `dominant_signal` (signal đóng góp nhiều nhất)
   - `signals.*` (chi tiết 7 signal)

3. **Action theo color** (BẮT BUỘC tuân thủ):

| Color  | HRS         | Action                                                                  |
|--------|-------------|--------------------------------------------------------------------------|
| GREEN  | < 0.3       | Continue normally. Không cần làm gì thêm.                               |
| YELLOW | 0.3 – 0.5   | Warning. Tự verify lại dominant signal trước khi proceed.               |
| ORANGE | 0.5 – 0.7   | **Halt Phase 2.** Run `/schema-check`. Load actual source cho ref nghi ngờ. |
| RED    | ≥ 0.7       | **STOP HẲN.** Recovery protocol (`docs/ai/HALLUCINATION_RULES.md`).      |

4. **Recommend action cụ thể** dựa trên `dominant_signal`:

| Signal              | Recovery action                                                                  |
|---------------------|-----------------------------------------------------------------------------------|
| `cite_coverage`     | Re-read source files. Add cite cho mọi external ref.                             |
| `schema_match`      | Run `/schema-check`. Update `schema_snapshot.yaml`. Type 1 hallucination?         |
| `confidence_density`| Replace "I think / probably" bằng cite cụ thể, hoặc admit uncertainty rõ ràng.    |
| `static_errors`     | Run typecheck full. Fix root cause, không skip.                                  |
| `context_drift`     | Run `/rotate` ngay (mandatory ≥ 120k tokens).                                    |
| `failures`          | Loop budget exhausted. Escalate user với context đầy đủ.                         |
| `schema_staleness`  | Update `schema_snapshot.yaml` với ground truth mới (verify với source).          |

5. **Append history** nếu HRS >= 0.5 (YELLOW trở lên):
   - Run với flag `--save` để ghi vào `project_state.yaml#hallucination_history`
   - Track trend cross-session để biết pattern xuất hiện hallucinate

## Flags hỗ trợ

```
--files <a,b,c>       Custom file list (default: git diff vs HEAD)
--tokens <int>        Session token count (default: read .claude/cache/last_tokens.json from statusline; fallback estimate từ char count)
--threshold <float>   Custom RED threshold (default: 0.7)
--save                Append vào project_state.yaml#hallucination_history
--json                Output JSON cho parser khác
```

## Ví dụ flow

```
User: /halluc-score

Claude:
1. Run: python .claude/hooks/python/halluc-score.py --save
2. Output:
   ════════════════════════════════════════════════════════════
     HALLUCINATION RISK SCORE
   ════════════════════════════════════════════════════════════
     Overall: 0.58  🟠 ORANGE
     Threshold: 0.7  |  Dominant: schema_match
     Files: 4  |  Tokens: 65,000 (statusline-cache)

     Signals:
       [1] Cite coverage:     60%  (3/5 refs)
       [2] Schema match:       0%  (1/3 refs, 2 BLOCKED)
       [3] Confidence dens:    1.20/k (8 matches)
       [4] Static errors:      0   (4 files checked)
       [5] Context drift:      0.81 (97,000 / 120k)
       [6] Consec failures:    1
       [7] Schema staleness:  12d

     Recommendation:
       🟠 Halt Phase 2 — /schema-check + load actual source
       🟠 Re-verify dominant signal: schema_match

3. Claude: "🟠 ORANGE — schema_match dominant với 2 ref BLOCKED (trong NOT_available list).
   Đây có khả năng cao là Type 1 hallucination. Tao đề xuất:
   - STOP code hiện tại
   - Run /schema-check để xác định 2 ref nào sai
   - Update schema_snapshot nếu API thật sự có field đó (verify với doc), hoặc remove ref khỏi code
   Tiếp tục?"
```

## Tích hợp với pipeline

- **KHÔNG add vào hook auto** — trade-off: lose visibility, gain workflow speed
- **Phase 3 (Verify)** có thể recommend `/halluc-score` nếu schema-check fail
- **Loop Logic** — sau retry thứ 2 fail, Claude tự gợi ý `/halluc-score` để diagnose
- **Phase 5 (Memory write)** — nếu `/halluc-score --save` chạy trong session, append entry vào `hallucination_history`

## Liên quan

- `docs/ai/HALLUCINATION_RULES.md` — 5 type + recovery
- `.claude/memory/schema_snapshot.yaml` — ground truth cho signal `schema_match`
- `.claude/memory/project_state.yaml#hallucination_history` — trend cross-session
- `.claude/hooks/python/halluc-score.py` — full implementation (Python)
- `.claude/hooks/bash/halluc-score.sh` — Bash lite
- `.claude/hooks/nodejs/halluc-score.js` — Node version
