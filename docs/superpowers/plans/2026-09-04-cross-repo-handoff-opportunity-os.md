# Opportunity OS Cross-Repo Handoff V0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a strict, read-only `research-opportunity-handoff/v0.1` preview boundary that can review territorial actor-need hypotheses and public GitHub contribution candidates without coercing actors into employment targets or creating a second contribution-import path.

**Architecture:** A new isolated `app/handoffs/` package parses Contract 2 as a Pydantic discriminated candidate union. A pure preview service exposes `AS_OF_EXPORT` freshness, evidence/assumptions/missing context, and only dispositions legal for the candidate kind. Public contribution candidates may be validated in memory against the existing `PublicContributionEntry` contract using explicit local identity/timestamp inputs, but actual persistence remains exclusively behind the existing GitHub Contribution Observation Bridge and its human-confirmed import flow.

**Tech Stack:** Python 3.12+, Pydantic 2, existing Opportunity OS contribution models, stdlib JSON/path handling, pytest.

**Spec:** Canonical spec is in `juanmanueltorres-creator/question-radar` at `docs/superpowers/specs/2026-09-04-cross-repo-problem-opportunity-handoff-v0.1-design.md`.

## Global Constraints

- Add the feature as an isolated package; do not refactor existing vacancy, targets, relationship, CV, outreach, process-email, or contribution domains.
- No new FastAPI route in V0.1.
- No shared package or runtime import from Question Radar or Andes Context OS.
- Incoming handoffs are snapshots with `source_freshness = "AS_OF_EXPORT"`; Opportunity OS does not call upstream repos to verify currentness.
- Contract identifier is exactly `research-opportunity-handoff/v0.1`.
- Candidate kinds are exactly `ACTOR_NEED_HYPOTHESIS` and `PUBLIC_CONTRIBUTION_CANDIDATE`.
- Territorial actors are never coerced into `TargetAccount` or Relationship state.
- Legal territorial preview dispositions: `RESEARCH_ACTOR`, `WATCH`, `DISCARD`; omit `RESEARCH_ACTOR` when `actor_refs` is empty.
- Legal public-contribution preview dispositions: `WATCH`, `DISCARD`, plus `IMPORT_PUBLIC_CONTRIBUTION` only when the existing `PublicContributionEntry` contract can be satisfied with explicit local metadata.
- `IMPORT_PUBLIC_CONTRIBUTION` in this preview means **eligible to continue through the existing contribution intake/bridge**, not permission for this package to write SQLite.
- The handoff package has no import/write method and must not initialize `state/contributions.local.sqlite3`.
- No network call occurs during handoff parsing or preview.
- No send/apply/follow-up/contact authority is introduced.
- Existing invariants remain authoritative: `PUBLIC_CONTRIBUTION_ENTRY != JOB_OPENING`, `PR_OPENED != EMPLOYMENT_INTEREST`, `PR_MERGED != EMPLOYMENT_INTEREST`, `GOOD_PROBLEM != AVAILABLE_PROBLEM`.
- Unknown fields and unsupported versions fail closed.
- Public fixtures are sanitized/public-only.

---

### Task 1: Model Contract 2 as a strict tagged candidate union

**Files:**
- Create: `app/handoffs/__init__.py`
- Create: `app/handoffs/models.py`
- Create: `tests/test_handoff_models.py`

**Interfaces:**
- Produces:

```python
ResearchOpportunityHandoff
ActorNeedHypothesisCandidate
PublicContributionCandidate
HandoffSource
```

Constants:

```python
RESEARCH_OPPORTUNITY_CONTRACT = "research-opportunity-handoff/v0.1"
SOURCE_FRESHNESS = "AS_OF_EXPORT"
```

- [ ] **Step 1: Write failing Pydantic contract tests**

Cover:

```python
def test_parses_actor_need_candidate(): ...
def test_parses_public_contribution_candidate(): ...
def test_rejects_unknown_contract_version(): ...
def test_rejects_unknown_candidate_kind(): ...
def test_rejects_unknown_fields(): ...
def test_actor_need_requires_assumptions_and_missing_context_fields(): ...
def test_public_candidate_preserves_claim_state_and_need_basis(): ...
```

Add semantic validators:

- `ACTOR_NEED_HYPOTHESIS` source system must be `andes-context-os`, with non-null `research_intent_ref` and `hypothesis_ref`.
- `PUBLIC_CONTRIBUTION_CANDIDATE` source system must be `question-radar`, with `research_intent_ref=None` and `hypothesis_ref=None` in V0.1.
- `created_at` must be timezone-aware.
- Public contribution `origin`, `need_basis`, `task_claim_state`, `expected_effort`, and `risk_level` use the same closed values as the existing contribution domain. Import those type aliases/constants from `app.contributions.models`; do not duplicate divergent vocabularies.

- [ ] **Step 2: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_models.py -v
```

- [ ] **Step 3: Implement minimal strict models**

Use `ConfigDict(extra="forbid")` consistently. Keep evidence refs as references; do not fetch them or copy source bodies.

Use a discriminated union or an equivalent explicit model validator on `candidate.kind`; do not infer kind from present fields.

- [ ] **Step 4: Run and confirm GREEN**

```bash
python -m pytest tests/test_handoff_models.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/handoffs tests/test_handoff_models.py
git commit -m "feat: add research opportunity handoff models"
```

---

### Task 2: Build a read-only territorial preview with no `TargetAccount` coercion

**Files:**
- Create: `app/handoffs/preview.py`
- Create: `tests/test_handoff_preview.py`
- Read only: `app/targets/models.py`, `app/relationships/` contracts if needed for negative assertions.

**Interfaces:**
- Produces:

```python
PreviewStatus = Literal["REVIEWABLE", "BLOCKED"]
TerritorialDisposition = Literal["RESEARCH_ACTOR", "WATCH", "DISCARD"]
PublicContributionDisposition = Literal[
    "IMPORT_PUBLIC_CONTRIBUTION", "WATCH", "DISCARD"
]

class OpportunityHandoffPreview(BaseModel):
    status: PreviewStatus
    handoff_id: str
    candidate_kind: str
    source_freshness: Literal["AS_OF_EXPORT"]
    evidence_refs: list[str]
    assumptions: list[str]
    missing_context: list[str]
    allowed_dispositions: list[str]
    blocked_reasons: list[str]
    contribution_entry: PublicContributionEntry | None

preview_research_opportunity_handoff(
    handoff: ResearchOpportunityHandoff,
    *,
    contribution_entry_id: str | None = None,
    contribution_discovered_at: datetime | None = None,
) -> OpportunityHandoffPreview
```

- [ ] **Step 1: Write failing territorial preview tests**

Required regressions:

1. actor refs present -> allowed dispositions exactly `RESEARCH_ACTOR`, `WATCH`, `DISCARD`.
2. actor refs empty -> `WATCH`, `DISCARD`; `RESEARCH_ACTOR` absent.
3. evidence refs, assumptions, missing context and `research_status` are displayed without strengthening them.
4. `source_freshness == "AS_OF_EXPORT"`.
5. no `TargetAccount` object is constructed.
6. preview creates no SQLite file and makes no network call.

Use `tmp_path` and assert no `state/` or DB artifact is created as a side effect.

- [ ] **Step 2: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_preview.py -v
```

- [ ] **Step 3: Implement pure territorial preview**

For `ACTOR_NEED_HYPOTHESIS`, return `contribution_entry=None` unconditionally. The preview module must not import `app.targets.models` in production code.

`research_status` remains display context only; it does not map to Opportunity OS vacancy/relationship states.

- [ ] **Step 4: Run and confirm GREEN**

```bash
python -m pytest tests/test_handoff_models.py tests/test_handoff_preview.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/handoffs/preview.py tests/test_handoff_preview.py
git commit -m "feat: preview territorial opportunity handoffs"
```

---

### Task 3: Validate public contribution compatibility in memory only

**Files:**
- Modify: `app/handoffs/preview.py`
- Modify: `tests/test_handoff_preview.py`
- Create: `tests/test_handoff_contribution_compatibility.py`
- Preserve unchanged: `app/contributions/bridge.py`, `app/contributions/repository.py`, `app/contributions/intake_cli.py`.

**Interfaces:**
- Consumes: `PublicContributionCandidate` plus explicit local metadata.
- Produces an **ephemeral** `PublicContributionEntry` only when the existing model validates.

- [ ] **Step 1: Write failing compatibility tests**

Cover:

```python
def test_public_candidate_without_local_identity_is_reviewable_but_not_import_eligible(): ...
def test_public_candidate_with_explicit_identity_and_timestamp_builds_ephemeral_entry(): ...
def test_maintainer_stated_need_without_evidence_fails_closed(): ...
def test_available_task_without_task_ref_fails_closed(): ...
def test_claimed_other_remains_claimed_other(): ...
def test_handoff_preview_never_calls_contribution_repository(): ...
```

When local metadata is absent:

```text
allowed_dispositions = ["WATCH", "DISCARD"]
blocked_reasons includes local_import_metadata_required
```

When explicit `contribution_entry_id` and timezone-aware `contribution_discovered_at` are supplied and `PublicContributionEntry(...)` validates:

```text
allowed_dispositions = ["IMPORT_PUBLIC_CONTRIBUTION", "WATCH", "DISCARD"]
```

- [ ] **Step 2: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_contribution_compatibility.py -v
```

- [ ] **Step 3: Map candidate fields exactly into the existing model**

Construct in memory:

```python
PublicContributionEntry(
    entry_id=contribution_entry_id,
    repository_full_name=candidate.repository_full_name,
    repository_url=candidate.repository_url,
    account_id=None,
    origin=candidate.origin,
    need_basis=candidate.need_basis,
    need_statement=candidate.need_statement,
    evidence_refs=list(candidate.evidence_refs),
    task_ref=candidate.task_ref,
    bounded_task=candidate.bounded_task,
    task_claim_state=candidate.task_claim_state,
    expected_effort=candidate.expected_effort,
    risk_level=candidate.risk_level,
    discovered_at=contribution_discovered_at,
)
```

Do not catch validation errors and silently weaken fields. Convert them into a blocked preview reason.

Critically, do **not** call `SQLiteContributionRepository.initialize()`, `ContributionObservationBridge.import_preview()`, or any GitHub provider here.

- [ ] **Step 4: Run focused contribution and existing bridge regressions**

```bash
python -m pytest \
  tests/test_handoff_contribution_compatibility.py \
  tests/test_contribution_models.py \
  tests/test_contribution_bridge.py \
  tests/test_contribution_intake_cli.py -v
```

Expected: all pass; existing bridge behavior is unchanged.

- [ ] **Step 5: Commit**

```bash
git add app/handoffs/preview.py \
  tests/test_handoff_preview.py \
  tests/test_handoff_contribution_compatibility.py
git commit -m "feat: validate contribution handoff compatibility"
```

---

### Task 4: Add a file-in/file-out preview CLI with zero mutation authority

**Files:**
- Create: `app/handoffs/intake_cli.py`
- Create: `tests/test_handoff_cli.py`

**Interfaces:**
- Produces CLI:

```text
python -m app.handoffs.intake_cli preview
  --handoff-file <json>
  --out <json>
  [--contribution-entry-id <id>]
  [--contribution-discovered-at <aware-iso>]
```

There is intentionally **no `import` subcommand** in this package.

- [ ] **Step 1: Write failing CLI tests**

Test:

1. valid territorial fixture -> reviewable preview file.
2. valid contribution fixture without local metadata -> no import disposition.
3. valid contribution fixture with explicit local metadata -> import disposition is offered.
4. malformed/unsupported handoff -> exit `2`; output file absent.
5. preview does not create contribution SQLite state.
6. no HTTP client/provider is constructed.
7. output JSON is stable for identical inputs.

- [ ] **Step 2: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_cli.py -v
```

- [ ] **Step 3: Implement minimal CLI**

Parse with `ResearchOpportunityHandoff.model_validate_json()` and call the pure preview service. Write only after full validation succeeds.

On errors, print a bounded machine-readable error such as:

```json
{"status":"BLOCKED","errors":["invalid_handoff_file"]}
```

Do not expose raw Pydantic/provider internals or source file content in error output.

- [ ] **Step 4: Run and confirm GREEN**

```bash
python -m pytest tests/test_handoff_cli.py tests/test_handoff_preview.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/handoffs/intake_cli.py tests/test_handoff_cli.py
git commit -m "feat: add read only handoff preview cli"
```

---

### Task 5: Protect authority boundaries with a release-contract regression

**Files:**
- Create: `tests/test_handoff_release_contract.py`
- Modify: `README.md` minimally.

**Interfaces:**
- Protects architecture rather than adding runtime behavior.

- [ ] **Step 1: Write failing release-contract tests**

Assert the production `app/handoffs/` slice contains no imports/calls for:

```text
app.targets
app.outreach
app.application
app.relationships
SQLiteContributionRepository
ContributionObservationBridge.import_preview
GitHubPublicContributionProvider
httpx.Client
```

Also assert:

```text
ACTOR_NEED_HYPOTHESIS != TargetAccount
PUBLIC_CONTRIBUTION_CANDIDATE != JOB_OPENING
preview != import
IMPORT_PUBLIC_CONTRIBUTION != automatic import
```

The test should inspect the package surface/source deliberately, following the repository's existing release-contract style; avoid brittle assertions on unrelated formatting.

- [ ] **Step 2: Run and confirm RED before final documentation/exports are in place**

```bash
python -m pytest tests/test_handoff_release_contract.py -v
```

- [ ] **Step 3: Update README minimally**

Document:

- Contract 2 is file-in/read-only-preview in V0.1;
- territorial actors are not target accounts;
- contribution import eligibility continues through the existing Contribution Observation Bridge;
- no new mutation route exists;
- freshness is `AS_OF_EXPORT`.

- [ ] **Step 4: Run release and contribution regressions**

```bash
python -m pytest \
  tests/test_handoff_release_contract.py \
  tests/test_contribution_intake_release_contract.py \
  tests/test_contribution_bridge.py -v
```

- [ ] **Step 5: Commit**

```bash
git add tests/test_handoff_release_contract.py README.md
git commit -m "docs: protect handoff authority boundary"
```

---

### Task 6: Prove both cross-repo paths with sanitized fixtures

**Files:**
- Create: `tests/fixtures/handoffs/research_opportunity_water_san_juan_v01.json`
- Create: `tests/fixtures/handoffs/public_contribution_candidate_v01.json`
- Create: `tests/test_cross_repo_handoff_dogfood.py`
- Create: `docs/CROSS_REPO_HANDOFF_V01.md`

**Interfaces:**
- Consumes deterministic Contract 2 fixtures produced by the Andes/public-research design.
- Produces review previews only.

- [ ] **Step 1: Write failing dogfood tests**

Territorial fixture must prove:

```text
candidate.kind = ACTOR_NEED_HYPOTHESIS
source_freshness = AS_OF_EXPORT
evidence / assumptions / missing_context remain separate
no TargetAccount is created
no external action is authorized
```

Public GitHub fixture must prove:

```text
candidate.kind = PUBLIC_CONTRIBUTION_CANDIDATE
task availability is preserved from explicit public evidence
PR/issue evidence never becomes employment-interest evidence
IMPORT_PUBLIC_CONTRIBUTION appears only after explicit local identity/timestamp inputs
```

- [ ] **Step 2: Run and confirm RED because fixtures/docs are absent**

```bash
python -m pytest tests/test_cross_repo_handoff_dogfood.py -v
```

- [ ] **Step 3: Add sanitized fixtures and operator guide**

The water fixture may legitimately end with `WATCH` or `DISCARD` if the actor/problem-owner evidence is incomplete. Do not manufacture a positive result to satisfy the dogfood.

The public contribution fixture uses a public/fictitious repository reference suitable for regression tests; no private contact or job-search data is checked in.

Document the continuation boundary:

```text
handoff preview
  -> operator sees IMPORT_PUBLIC_CONTRIBUTION eligibility
  -> operator separately runs existing contribution intake against explicit public GitHub evidence
  -> existing exact preview + human confirmation + import
```

- [ ] **Step 4: Run full local verification**

```bash
python -m pytest -v
python -m compileall app
git diff --check origin/main...HEAD
```

Expected: all existing application/CV/outreach/relationship/contribution behavior remains green.

- [ ] **Step 5: Verify repository CI gates on the runtime PR**

Require the existing GitHub Actions suite to pass, including the repository's private/generated-file guard, recruiter preview checks, and SHA-bound offline runtime build/verification on supported Python versions. Do not weaken those gates for this feature.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/handoffs \
  tests/test_cross_repo_handoff_dogfood.py \
  docs/CROSS_REPO_HANDOFF_V01.md
git commit -m "docs: dogfood cross repo opportunity previews"
```

---

## Opportunity OS Completion Gate

Before considering V0.1 complete, verify:

```text
Contract 2 -> strict tagged union
source freshness -> AS_OF_EXPORT
actor hypothesis -> read-only preview only
actor -> never coerced to TargetAccount
public contribution -> exact existing vocabulary
entry compatibility -> validated in memory
handoff package -> no DB write path
actual contribution import -> existing bridge only
send/apply/follow-up authority -> none
PR/merge -> never employment interest
```

Final clean check:

```bash
python -m pytest -v
python -m compileall app
git diff --check origin/main...HEAD
```

Then require the complete existing GitHub Actions workflow to pass on the exact PR head before merge.