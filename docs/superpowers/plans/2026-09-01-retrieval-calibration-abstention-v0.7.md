# Retrieval Calibration & Abstention v0.7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Status:** implemented on `feat/retrieval-calibration-abstention-v0.7`; final documentation-head verification pending at the time of this update. PR #14 remains draft and unmerged.

**Goal:** Calibrate lexical retrieval so selected Spanish plural variants are recoverable, weak lexical collisions are easier to inspect, and genuinely zero-evidence queries abstain explicitly.

**Architecture:** Preserve the v0.6 unified read-only corpus. Add an isolated dependency-free retrieval normalizer, coverage-aware evidence/ranking, and explicit abstention. Keep the frozen v0.5 novelty/Jaccard contract as secondary evidence and keep human review mandatory.

**Tech Stack:** Python 3.11+, SQLite, stdlib runtime only, pytest.

**Spec:** `docs/superpowers/specs/2026-09-01-retrieval-calibration-abstention-v0.7-design.md`

## Global constraints

- No embeddings, vector search, LLM runtime inference, synonym expansion, or automatic semantic relations.
- No new SQLite tables or write path.
- SQLite retrieval remains `mode=ro`.
- Runtime dependencies remain empty.
- v0.5 novelty normalization remains frozen.
- Blind benchmark files remain calibration inputs only.
- Human review remains mandatory.

---

## Final file architecture

- `src/question_radar/retrieval_text.py` — retrieval-only normalization and narrow noun-focused plural handling.
- `src/question_radar/retrieval.py` — BM25 retrieval, coverage evidence, calibrated ordering, and abstention.
- `src/question_radar/retrieval_export.py` — deterministic v0.7 Markdown/JSON evidence and abstention output.
- `src/question_radar/retrieval_storage.py` — unchanged v0.6 read-only unified corpus loader.
- `src/question_radar/cli_v06.py` — unchanged public retrieval routing facade.
- `tests/test_retrieval_text.py` — normalizer contract and verb-stemming guard.
- `tests/test_retrieval.py` — coverage/ranking/abstention contract.
- `tests/test_retrieval_benchmarks.py` — frozen blind inputs and retained strong gold labels.
- `tests/test_retrieval_cli.py` — deterministic output, CLI, and read-only regressions.
- `corpus/blind-system-trust-2026-09-01.jsonl` — 24-question external Blind Benchmark #4.

---

## Executed TDD chronology

### Task 1 — Retrieval-specific normalization

- [x] Added `tests/test_retrieval_text.py` before production code.
- [x] CI RED: `ModuleNotFoundError: question_radar.retrieval_text`.
- [x] Added `normalize_retrieval_tokens()` with retrieval-specific stopwords and initial conservative morphology.
- [x] Preserved v0.5 `normalize_tokens()` unchanged through regression coverage.

### Task 2 — Coverage-aware ranking and abstention

- [x] Extended `RetrievalEvidence` with `matched_token_count`, `query_token_count`, and `query_coverage`.
- [x] Extended `RetrievalPack` with `abstained` and `abstention_reason`.
- [x] Added explicit `no_lexical_evidence` abstention with `results=()` for truly zero-overlap queries.
- [x] Changed ordering to matched-token count → coverage → BM25 → frozen v0.5 Jaccard → stable keys.
- [x] Preserved read-only corpus loading and mandatory human review.

### Task 3 — Blind Benchmark #4 calibration

- [x] Froze all 24 blind system-trust questions exactly before accepting final behavior.
- [x] Retained strong gold labels that fit v0.7 scope:
  - Q1 → `vault-2026-08-31-001` top 5.
  - Q14 → `qv2-cal-013` top 5.
  - prior Blind #3 Q7 → `qv2-cal-013` top 5.
- [x] Withdrew Q16-as-abstention before production closure because `personas → persona` creates genuine weak lexical evidence. Q16 remains a diagnostic weak-evidence control.
- [x] CI later showed Q24 still depends on `entienden ↔ entender`; forcing Q24 top 5 would require verb stemming, semantic assistance, or an ad hoc boost outside v0.7. Q24 remains a negative control instead of being overfit.

### Task 4 — Renderer and CLI evidence contract

- [x] Updated deterministic Markdown/JSON to expose coverage fields.
- [x] Added explicit `ABSTAINED` / `no_lexical_evidence` rendering.
- [x] Kept the public `question-radar retrieval compare` namespace and existing CLI facade.
- [x] Preserved byte-for-byte read-only CLI database behavior and fail-closed missing-DB behavior.

### Task 5 — Morphology self-review

A self-review found that the initial generic plural rule silently stemmed verbs such as `puedes → pued`, `tomas → toma`, and `trabajas → trabaja`.

- [x] Added a failing regression before changing production.
- [x] CI RED: 1 failed, 315 passed, with the exact unwanted verb transformations above.
- [x] Replaced the generic rule with narrow noun-focused suffix handling:
  - `-iones` → remove final `es`.
  - `-ores` → remove final `es`.
  - `-emas` → remove final `s`.
  - `-onas` → remove final `s`.
  - `-os` → remove final `s`, except `-mos`.
- [x] Regression explicitly preserves `entienden`, `modifica`, `pierde`, `puedes`, `tomas`, `usas`, and `trabajas` unchanged.
- [x] CI GREEN on implementation head: 316 tests passed and `python -m compileall -q src` succeeded.

---

## Verification gates before PR completion

- [ ] Run the full suite on the final documentation head: `pytest -q`.
- [ ] Run `python -m compileall -q src` on that same head.
- [ ] Confirm `pyproject.toml` still contains `dependencies = []`.
- [ ] Confirm no new SQLite tables or mutation paths were added.
- [ ] Compare branch against `main` and verify the diff is limited to v0.7 source/tests/docs/calibration data.
- [ ] Update PR #14 with exact final head SHA, CI evidence, retained gold labels, and Q16/Q24 control rationale.
- [ ] Leave PR #14 unmerged pending explicit integration approval.

## Scientific boundary

A retrieval result means **“review this prior question before treating the candidate as new.”** It does not mean semantic equivalence. An abstention means only that the v0.7 lexical layer found no supported overlap; it does not prove the candidate is conceptually novel.
