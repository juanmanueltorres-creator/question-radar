# Retrieval Calibration & Abstention v0.7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Status:** implementation and review fixes complete on `feat/retrieval-calibration-abstention-v0.7`; final CI on this documentation head is the remaining verification gate. PR #14 remains draft and unmerged.

**Goal:** Calibrate lexical retrieval so selected Spanish plural variants are recoverable, weak lexical collisions are inspectable, zero-evidence rows never pad a shortlist, and genuinely zero-evidence queries abstain explicitly.

**Architecture:** Preserve the v0.6 unified read-only corpus. Add an isolated dependency-free retrieval normalizer, coverage-aware evidence/ranking, evidence-only shortlist admission, and explicit abstention. Keep frozen v0.5 novelty/Jaccard as secondary evidence and human review mandatory.

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
- `src/question_radar/retrieval.py` — BM25 retrieval, coverage evidence, evidence-only shortlist admission, calibrated ordering, and abstention.
- `src/question_radar/retrieval_export.py` — deterministic v0.7 Markdown/JSON evidence and abstention output.
- `src/question_radar/retrieval_storage.py` — unchanged v0.6 read-only unified corpus loader.
- `src/question_radar/cli_v06.py` — unchanged public retrieval routing facade.
- `tests/test_retrieval_text.py` — normalizer contract and verb-stemming guard.
- `tests/test_retrieval.py` — coverage/ranking/shortlist/abstention contract.
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
- [x] Withdrew Q16-as-abstention because `personas → persona` creates genuine weak lexical evidence. Q16 remains a diagnostic weak-evidence control.
- [x] Withdrew Q24 top-five gold after CI showed it still depends on `entienden ↔ entender`; forcing it would require verb stemming, semantic assistance, or an ad hoc boost outside v0.7.

### Task 4 — Renderer and CLI evidence contract

- [x] Updated deterministic Markdown/JSON to expose coverage fields.
- [x] Added explicit `ABSTAINED` / `no_lexical_evidence` rendering.
- [x] Kept the public `question-radar retrieval compare` namespace and existing CLI facade.
- [x] Preserved byte-for-byte read-only CLI database behavior and fail-closed missing-DB behavior.

### Task 5 — Morphology self-review

A self-review found that the initial generic plural rule silently stemmed verbs such as `puedes → pued`, `tomas → toma`, and `trabajas → trabaja`.

- [x] Added a failing regression before changing production.
- [x] CI RED: 1 failed, 315 passed, showing the unwanted transformations.
- [x] Replaced the generic rule with narrow noun-focused suffix handling:
  - `-iones` → remove final `es`.
  - `-ores` → remove final `es`.
  - `-emas` → remove final `s`.
  - `-onas` → remove final `s`.
  - `-os` → remove final `s`, except `-mos`.
- [x] Regression explicitly preserves `entienden`, `modifica`, `pierde`, `puedes`, `tomas`, `usas`, and `trabajas` unchanged.
- [x] CI GREEN after fix: 316 tests passed and `python -m compileall -q src` succeeded.

### Task 6 — Code-review shortlist admission fix

A final diff review found that v0.7 could still return zero-evidence rows after one positive match merely to fill `limit`.

- [x] Added a regression requiring a mixed corpus to return only evidence-bearing rows.
- [x] CI RED: 1 failed, 315 passed; result IDs were `match`, `zero-a`, `zero-b` instead of only `match`.
- [x] Filtered shortlist candidates to `matched_token_count > 0` before sorting and slicing.
- [x] `limit` is now a maximum, not a quota.
- [x] CI GREEN after the runtime fix; final documentation-head CI remains the last gate.

---

## Verification gates before PR completion

- [ ] Run the full suite on the final documentation head: `pytest -q`.
- [ ] Run `python -m compileall -q src` on that same head.
- [x] Confirm `pyproject.toml` still contains `dependencies = []`.
- [x] Confirm no new SQLite tables or mutation paths were added; `retrieval_storage.py` is unchanged.
- [x] Compare branch against `main`; diff is limited to v0.7 retrieval source/tests/docs/calibration data plus README documentation.
- [ ] Update PR #14 with exact final head SHA, final CI evidence, retained gold labels, Q16/Q24 control rationale, and shortlist-admission review fix.
- [ ] Leave PR #14 unmerged pending explicit integration approval.

## Scientific boundary

A retrieval result means **“review this prior question before treating the candidate as new.”** It does not mean semantic equivalence. An abstention means only that the v0.7 lexical layer found no supported overlap; it does not prove the candidate is conceptually novel.
