# Question Radar Cross-Repo Handoff V0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a strict, deterministic `question-research-handoff/v0.1` export path from the current Question Radar investigation decision without changing existing question, profile, lineage, retrieval, or decision semantics.

**Architecture:** Question Radar remains the source of inquiry and attention state. A new stdlib-only handoff contract and exporter read the existing v0.4 `QuestionNode` plus the current v0.9 `InvestigationDecision`, fingerprint that exact snapshot, and emit UTF-8 JSON. Routing is operator-supplied; no destination code is imported and no route is inferred.

**Tech Stack:** Python 3.11+, standard library only, dataclasses, `hashlib`, `json`, SQLite through existing stores, pytest.

**Spec:** `docs/superpowers/specs/2026-09-04-cross-repo-problem-opportunity-handoff-v0.1-design.md`

## Global Constraints

- Runtime dependencies remain empty.
- Preserve all existing CLI namespaces and v0.1-v0.9 persistence contracts.
- Do not add a shared package, cross-repo import, RPC, network call, background worker, or external action.
- `PARKED` and `KILLED` decisions cannot export an actionable handoff.
- The exporter must use the **current** v0.9 decision returned by `InvestigationDecisionStore.get_current()`.
- `decision_fingerprint` is a deterministic SHA-256 over the exact `QuestionNode.to_dict()` plus `InvestigationDecision.to_dict()` canonical JSON payload.
- `question_profile_ref` remains `null` in V0.1 unless an explicit, structurally linked profile reference already exists; do not infer one from equal free-text questions.
- `question.canonical` defaults to the stored `QuestionNode.question` exactly. An explicit operator-supplied canonical question may replace it; no hidden canonicalization is allowed.
- Route vocabulary is exactly `TERRITORIAL_RESEARCH` and `PUBLIC_CONTRIBUTION_RESEARCH`.
- Destination mapping is deterministic: `TERRITORIAL_RESEARCH -> andes-context-os`; `PUBLIC_CONTRIBUTION_RESEARCH -> opportunity-os`.
- Handoffs are snapshots current **as of export**; they are not live leases.
- Unknown fields and unsupported contract versions fail closed.
- Public dogfood contains no credentials, private contacts, Gmail bodies, private profile content, or unpublished personal data.

---

### Task 1: Contract 1 strict model and deterministic fingerprint

**Files:**
- Create: `src/question_radar/handoffs.py`
- Create: `tests/test_handoff_models.py`

**Interfaces:**
- Consumes: `QuestionNode.to_dict()`, `InvestigationDecision.to_dict()`.
- Produces: `QuestionResearchHandoff.from_dict(payload)`, `QuestionResearchHandoff.to_dict()`, `decision_fingerprint(node, decision) -> str`.

- [ ] **Step 1: Write failing contract tests**

Cover:

```python
def test_handoff_rejects_unknown_contract_version(): ...
def test_handoff_rejects_unknown_route(): ...
def test_handoff_rejects_parked_and_killed_decisions(): ...
def test_handoff_requires_timezone_aware_created_at(): ...
def test_decision_fingerprint_is_deterministic(): ...
```

Use an exact valid payload with:

```python
"contract": "question-research-handoff/v0.1"
"routing": {"kind": "TERRITORIAL_RESEARCH", "destination": "andes-context-os"}
"investigation": {"decision": "RESEARCH", "rationale": "...", "next_test": "..."}
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```bash
pytest tests/test_handoff_models.py -q
```

Expected: import/module failures because `question_radar.handoffs` does not exist.

- [ ] **Step 3: Implement the minimal strict dataclasses**

Create frozen/slotted dataclasses for:

```python
HandoffSource
HandoffQuestion
HandoffInvestigation
HandoffRouting
QuestionResearchHandoff
```

Use closed constants:

```python
HANDOFF_CONTRACT = "question-research-handoff/v0.1"
ACTIONABLE_DECISIONS = ("DO_NOW", "RESEARCH")
ROUTES = ("TERRITORIAL_RESEARCH", "PUBLIC_CONTRIBUTION_RESEARCH")
DESTINATION_BY_ROUTE = {
    "TERRITORIAL_RESEARCH": "andes-context-os",
    "PUBLIC_CONTRIBUTION_RESEARCH": "opportunity-os",
}
```

Implement strict required/allowed-field checks locally rather than adding a dependency. Validate timezone-aware timestamps with `datetime.fromisoformat()`.

Implement fingerprinting as:

```python
def decision_fingerprint(node: QuestionNode, decision: InvestigationDecision) -> str:
    payload = {
        "question": node.to_dict(),
        "decision": decision.to_dict(),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()
```

- [ ] **Step 4: Run model tests and confirm GREEN**

```bash
pytest tests/test_handoff_models.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/question_radar/handoffs.py tests/test_handoff_models.py
git commit -m "feat: add strict question research handoff contract"
```

---

### Task 2: Build Contract 1 only from a current explicit decision

**Files:**
- Create: `src/question_radar/handoff_export.py`
- Create: `tests/test_handoff_export.py`
- Read without modifying unless required by a failing compatibility test: `src/question_radar/decision_storage.py`

**Interfaces:**
- Consumes: `QuestionNode`, current `InvestigationDecision`.
- Produces:

```python
build_question_research_handoff(
    node: QuestionNode,
    decision: InvestigationDecision,
    *,
    route: str,
    handoff_id: str,
    created_at: str,
    canonical_question: str | None = None,
    constraints: tuple[str, ...] = (),
) -> QuestionResearchHandoff

render_question_research_handoff_json(
    handoff: QuestionResearchHandoff,
) -> str
```

- [ ] **Step 1: Write failing exporter tests**

Required regressions:

```python
def test_builder_uses_raw_question_as_canonical_when_no_override(): ...
def test_builder_preserves_explicit_canonical_question(): ...
def test_builder_keeps_question_profile_ref_null_without_explicit_link(): ...
def test_builder_rejects_parked_decision(): ...
def test_builder_rejects_route_destination_mismatch_by_construction(): ...
def test_json_export_is_byte_deterministic_for_same_inputs(): ...
```

Also assert `source.decision_id` and `source.decision_fingerprint` match the supplied current records.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
pytest tests/test_handoff_export.py -q
```

- [ ] **Step 3: Implement the builder and deterministic renderer**

The builder must not rewrite question text. Use:

```python
canonical = node.question if canonical_question is None else canonical_question.strip()
```

Reject empty explicit canonical text.

Render with:

```python
json.dumps(
    handoff.to_dict(),
    ensure_ascii=False,
    sort_keys=True,
    indent=2,
) + "\n"
```

Do not read profiles by fuzzy or text-equality lookup in this task. `question_profile_ref=None` is the correct V0.1 value when no explicit structural link exists.

- [ ] **Step 4: Run exporter tests and confirm GREEN**

```bash
pytest tests/test_handoff_models.py tests/test_handoff_export.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/question_radar/handoff_export.py tests/test_handoff_export.py
git commit -m "feat: export current investigation handoff"
```

---

### Task 3: Add a backward-compatible `decision handoff` CLI command

**Files:**
- Modify: `src/question_radar/cli_v09.py`
- Create: `tests/test_handoff_cli.py`
- Preserve: `tests/test_decision_cli.py`

**Interfaces:**
- Consumes: existing `--db`, `InvestigationDecisionStore.get_question_node()`, `get_current()`.
- Produces CLI:

```text
question-radar --db <db> decision handoff <question_id>
  --route TERRITORIAL_RESEARCH|PUBLIC_CONTRIBUTION_RESEARCH
  --out <path>
  [--canonical-question <text>]
  [--constraint <text>]...
  [--handoff-id <id>]
  [--created-at <aware-iso>]
```

- [ ] **Step 1: Write failing CLI tests**

Test:

1. `RESEARCH` current decision writes one valid JSON artifact.
2. `DO_NOW` also exports.
3. `PARKED` and `KILLED` return exit code `2` and do not create the output file.
4. After decision B supersedes decision A, export references B, never A.
5. Existing `decision show/history/active`, `retrieval`, `benchmark`, and `lineage` delegation still works.
6. Repeated `--constraint` preserves order.
7. An explicit `--created-at` and `--handoff-id` makes the exported bytes deterministic.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
pytest tests/test_handoff_cli.py -q
```

- [ ] **Step 3: Extend `build_decision_parser()` additively**

Add `handoff` under the existing `decision` namespace. Reuse current helpers `_now_iso()` and UUID generation style; add `_new_handoff_id()` returning `qrh:<uuidhex>`.

In the handler:

```python
store = InvestigationDecisionStore(args.db)
node = store.get_question_node(args.question_id)
decision = store.get_current(args.question_id)
```

Fail if either is absent. Never accept a caller-supplied historical `decision_id`; exporting only the current decision is the stale-prevention boundary at source.

Build fully in memory before creating directories or writing output. Only write after validation succeeds.

- [ ] **Step 4: Run CLI compatibility tests**

```bash
pytest tests/test_handoff_cli.py tests/test_decision_cli.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/question_radar/cli_v09.py tests/test_handoff_cli.py
git commit -m "feat: add investigation handoff cli"
```

---

### Task 4: Freeze the two routing dogfood exports without inventing claims

**Files:**
- Create: `benchmarks/dogfood-cross-repo-handoff-2026-09-04.md`
- Create: `tests/fixtures/handoffs/question_research_water_san_juan_v01.json`
- Create: `tests/fixtures/handoffs/question_research_public_github_v01.json`
- Create: `tests/test_handoff_dogfood.py`
- Modify: `README.md` only to document the new export command and authority boundary.

**Interfaces:**
- Produces two sanitized Contract 1 fixtures consumed later by destination-repo tests.

- [ ] **Step 1: Write a failing dogfood regression**

The primary fixture question is exactly:

```text
¿Qué decisión recurrente relacionada con agua en San Juan podría mejorar utilizando evidencia territorial o satelital, quién toma hoy esa decisión y qué información le falta?
```

It must route to `TERRITORIAL_RESEARCH` and remain `RESEARCH` unless the fixture explicitly documents another operator judgment.

The secondary fixture question is exactly:

```text
¿Qué problema público de software geoespacial puedo resolver en un repositorio externo donde exista una tarea explícita y disponible?
```

It must route to `PUBLIC_CONTRIBUTION_RESEARCH`.

The test validates both fixtures through `QuestionResearchHandoff.from_dict()` and asserts no field claims a buyer, customer, job opening, contact permission, or task availability merely from routing.

- [ ] **Step 2: Run and confirm RED because fixtures are absent**

```bash
pytest tests/test_handoff_dogfood.py -q
```

- [ ] **Step 3: Add sanitized fixtures and benchmark note**

Use fictional IDs and deterministic timestamps. The benchmark note must state:

```text
route != opportunity
handoff != evidence
current_at_export != current_now
```

Do not include real recipient/contact data.

- [ ] **Step 4: Update README minimally**

Document only:

- purpose of `decision handoff`;
- the two explicit routes;
- snapshot freshness semantics;
- no automatic chaining or external action.

- [ ] **Step 5: Run full repository verification**

```bash
pytest -q
python -m compileall -q src
git diff --check origin/main...HEAD
```

Expected: existing v0.1-v0.9 regressions plus new handoff tests all pass; compile and whitespace checks succeed.

- [ ] **Step 6: Commit**

```bash
git add benchmarks/dogfood-cross-repo-handoff-2026-09-04.md \
  tests/fixtures/handoffs \
  tests/test_handoff_dogfood.py \
  README.md
git commit -m "docs: dogfood question research handoff v0.1"
```

---

## Question Radar Completion Gate

Before opening the runtime PR, verify:

```text
current decision only -> export
PARKED/KILLED -> fail closed
route -> explicit operator input
canonical question -> no hidden rewrite
profile ref -> null unless explicitly linked
fingerprint -> deterministic
artifact -> snapshot AS_OF_EXPORT
external action authority -> none
```

Run one final clean check:

```bash
pytest -q
python -m compileall -q src
git diff --check origin/main...HEAD
```

Only after this slice is green should the generated Contract 1 fixture be used as the fixed input for the Andes Context OS implementation plan.