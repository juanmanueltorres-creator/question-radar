# Opportunity OS Cross-Repo Handoff V0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a strict, read-only cross-repo handoff boundary that can review territorial actor-need hypotheses and turn an explicitly selected, already-validated public GitHub contribution preview into a `PUBLIC_CONTRIBUTION_CANDIDATE` without coercing actors into employment targets or creating a second contribution-import path.

**Architecture:** A new isolated `app/handoffs/` package independently validates the direct `question-research-handoff/v0.1` route and Contract 2 as Pydantic models. For GitHub, the operator first uses the existing read-only Contribution Observation Bridge against one explicit issue; a pure adapter combines that exact `ContributionPreview` with the Question Radar handoff and emits `research-opportunity-handoff/v0.1`. A separate pure preview exposes `AS_OF_EXPORT` freshness and legal dispositions. Actual contribution persistence remains exclusively behind the original exact-preview + human-confirmed contribution import flow.

**Tech Stack:** Python 3.12+, Pydantic 2, existing Opportunity OS contribution models/preview contracts, stdlib JSON/path handling, pytest.

**Spec:** Canonical spec is in `juanmanueltorres-creator/question-radar` at `docs/superpowers/specs/2026-09-04-cross-repo-problem-opportunity-handoff-v0.1-design.md`.

## Global Constraints

- Add the feature as an isolated package; do not refactor existing vacancy, targets, relationship, CV, outreach, process-email, or contribution domains.
- No new FastAPI route in V0.1.
- No shared package or runtime import from Question Radar or Andes Context OS.
- Incoming handoffs are snapshots with `source_freshness = "AS_OF_EXPORT"`; Opportunity OS does not call upstream repos to verify currentness.
- Contract 1 direct route is exactly `PUBLIC_CONTRIBUTION_RESEARCH -> opportunity-os`.
- Contract 2 identifier is exactly `research-opportunity-handoff/v0.1`.
- Candidate kinds are exactly `ACTOR_NEED_HYPOTHESIS` and `PUBLIC_CONTRIBUTION_CANDIDATE`.
- Territorial actors are never coerced into `TargetAccount` or Relationship state.
- Legal territorial preview dispositions: `RESEARCH_ACTOR`, `WATCH`, `DISCARD`; omit `RESEARCH_ACTOR` when `actor_refs` is empty.
- Legal public-contribution preview dispositions: `WATCH`, `DISCARD`, plus `IMPORT_PUBLIC_CONTRIBUTION` only when the existing `PublicContributionEntry` contract can be satisfied with explicit local metadata.
- `IMPORT_PUBLIC_CONTRIBUTION` means **eligible to continue through the already-existing contribution import preview**, not permission for `app/handoffs` to write SQLite.
- The handoff package has no import/write method and must not initialize `state/contributions.local.sqlite3`.
- The handoff package makes no network call. Public GitHub acquisition remains in the existing `app.contributions.intake_cli preview` / `GitHubPublicContributionProvider` path.
- A `PUBLIC_CONTRIBUTION_CANDIDATE` may be built only from an existing `ContributionPreview` whose status is `IMPORTABLE` and whose `proposed_entry` is non-null. Other contribution lifecycle updates are out of V0.1 scope.
- No send/apply/follow-up/contact authority is introduced.
- Existing invariants remain authoritative: `PUBLIC_CONTRIBUTION_ENTRY != JOB_OPENING`, `PR_OPENED != EMPLOYMENT_INTEREST`, `PR_MERGED != EMPLOYMENT_INTEREST`, `GOOD_PROBLEM != AVAILABLE_PROBLEM`.
- Unknown fields and unsupported versions fail closed.
- Public fixtures are sanitized/public-only.

---

### Task 1: Model the direct Contract 1 route and Contract 2 tagged union

**Files:**
- Create: `app/handoffs/__init__.py`
- Create: `app/handoffs/models.py`
- Create: `tests/test_handoff_models.py`

**Interfaces:**
- Produces:

```python
QuestionResearchHandoff
ResearchOpportunityHandoff
ActorNeedHypothesisCandidate
PublicContributionCandidate
HandoffSource
```

Constants:

```python
QUESTION_RESEARCH_CONTRACT = "question-research-handoff/v0.1"
RESEARCH_OPPORTUNITY_CONTRACT = "research-opportunity-handoff/v0.1"
PUBLIC_CONTRIBUTION_ROUTE = "PUBLIC_CONTRIBUTION_RESEARCH"
SOURCE_FRESHNESS = "AS_OF_EXPORT"
```

- [ ] **Step 1: Write failing Pydantic contract tests**

Cover:

```python
def test_parses_direct_public_contribution_question_handoff(): ...
def test_direct_question_handoff_rejects_territorial_route(): ...
def test_parses_actor_need_candidate(): ...
def test_parses_public_contribution_candidate(): ...
def test_rejects_unknown_contract_version(): ...
def test_rejects_unknown_candidate_kind(): ...
def test_rejects_unknown_fields(): ...
def test_actor_need_requires_assumptions_and_missing_context_fields(): ...
def test_public_candidate_preserves_claim_state_and_need_basis(): ...
```

Semantic validators:

- direct Contract 1 requires `routing.kind == "PUBLIC_CONTRIBUTION_RESEARCH"` and `routing.destination == "opportunity-os"`;
- Contract 1 decision is `DO_NOW` or `RESEARCH` and includes `decision_fingerprint`;
- `ACTOR_NEED_HYPOTHESIS` source system is `andes-context-os`, with non-null `research_intent_ref` and `hypothesis_ref`;
- `PUBLIC_CONTRIBUTION_CANDIDATE` source system is `question-radar`, with `research_intent_ref=None` and `hypothesis_ref=None`;
- timestamps are timezone-aware;
- public contribution `origin`, `need_basis`, `task_claim_state`, `expected_effort`, and `risk_level` reuse the existing aliases from `app.contributions.models`, never duplicated vocabularies.

- [ ] **Step 2: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_models.py -v
```

- [ ] **Step 3: Implement minimal strict models**

Use `ConfigDict(extra="forbid")`. Use an explicit discriminator on `candidate.kind`; never infer kind from present fields. Evidence refs remain refs; models perform no I/O.

- [ ] **Step 4: Run and confirm GREEN**

```bash
python -m pytest tests/test_handoff_models.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/handoffs tests/test_handoff_models.py
git commit -m "feat: add cross repo handoff models"
```

---

### Task 2: Convert an existing GitHub contribution preview into Contract 2

**Files:**
- Create: `app/handoffs/public_contribution_research.py`
- Create: `tests/test_handoff_public_contribution_research.py`
- Preserve unchanged: `app/contributions/bridge.py`, `app/contributions/github_provider.py`, `app/contributions/normalizer.py`, `app/contributions/repository.py`, `app/contributions/intake_cli.py`.

**Interfaces:**
- Consumes the direct Question Radar Contract 1 snapshot plus the **existing** Opportunity OS `ContributionPreview` generated for one explicit GitHub issue.
- Produces:

```python
build_public_contribution_candidate_handoff(
    question_handoff: QuestionResearchHandoff,
    contribution_preview: ContributionPreview,
    *,
    handoff_id: str,
    created_at: datetime,
) -> ResearchOpportunityHandoff

render_research_opportunity_handoff_json(
    handoff: ResearchOpportunityHandoff,
) -> str
```

- [ ] **Step 1: Write failing adapter tests**

Cover:

```python
def test_builds_candidate_from_importable_proposed_entry(): ...
def test_rejects_no_change_preview(): ...
def test_rejects_blocked_preview(): ...
def test_rejects_candidate_event_only_preview(): ...
def test_preserves_available_claim_state(): ...
def test_preserves_claimed_other_state(): ...
def test_preserves_need_basis_and_evidence_refs(): ...
def test_adapter_never_imports_or_mutates_contribution_state(): ...
def test_export_is_byte_deterministic_for_same_inputs(): ...
```

The fixed source preview must satisfy:

```python
contribution_preview.status == "IMPORTABLE"
contribution_preview.proposed_entry is not None
contribution_preview.candidate_event is None
```

- [ ] **Step 2: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_public_contribution_research.py -v
```

- [ ] **Step 3: Implement exact mapping from `proposed_entry`**

Map only existing validated fields:

```text
proposed_entry.repository_full_name -> candidate.repository_full_name
proposed_entry.repository_url       -> candidate.repository_url
proposed_entry.origin               -> candidate.origin
proposed_entry.need_basis           -> candidate.need_basis
proposed_entry.need_statement       -> candidate.need_statement
proposed_entry.evidence_refs        -> candidate.evidence_refs
proposed_entry.task_ref             -> candidate.task_ref
proposed_entry.bounded_task         -> candidate.bounded_task
proposed_entry.task_claim_state     -> candidate.task_claim_state
proposed_entry.expected_effort      -> candidate.expected_effort
proposed_entry.risk_level           -> candidate.risk_level
```

Source lineage comes from the Question Radar handoff:

```text
source.system              = question-radar
source.source_question_ref = question_handoff.source.question_id
source.research_intent_ref = null
source.hypothesis_ref      = null
```

Do not copy `entry_id` or `discovered_at` into Contract 2 because they are Opportunity OS local identity/lifecycle metadata, not part of the approved public candidate contract.

- [ ] **Step 4: Run adapter plus existing contribution regressions**

```bash
python -m pytest \
  tests/test_handoff_public_contribution_research.py \
  tests/test_contribution_bridge.py \
  tests/test_contribution_intake_cli.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/handoffs/public_contribution_research.py \
  tests/test_handoff_public_contribution_research.py
git commit -m "feat: adapt contribution preview into handoff candidate"
```

---

### Task 3: Build a read-only candidate preview with no domain coercion

**Files:**
- Create: `app/handoffs/preview.py`
- Create: `tests/test_handoff_preview.py`
- Read only: `app/targets/models.py` for negative compatibility assertions.

**Interfaces:**
- Produces:

```python
PreviewStatus = Literal["REVIEWABLE", "BLOCKED"]

class OpportunityHandoffPreview(BaseModel):
    status: PreviewStatus
    handoff_id: str
    candidate_kind: str
    source_freshness: Literal["AS_OF_EXPORT"]
    statement: str
    research_status: str | None
    actor_refs: list[str]
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

For public contribution candidates, `statement` is the candidate `need_statement`, `research_status=None`, `actor_refs=[]`, and assumptions/missing context are empty because Contract 2 Candidate B does not claim those fields.

- [ ] **Step 1: Write failing territorial preview tests**

Required regressions:

1. actor refs present -> dispositions exactly `RESEARCH_ACTOR`, `WATCH`, `DISCARD`;
2. actor refs empty -> `WATCH`, `DISCARD`;
3. evidence refs, assumptions, missing context and `research_status` are displayed verbatim;
4. `source_freshness == "AS_OF_EXPORT"`;
5. no `TargetAccount` object is constructed;
6. preview creates no SQLite file and makes no network call.

- [ ] **Step 2: Add failing public-candidate compatibility tests**

Cover:

```python
def test_public_candidate_without_local_identity_is_reviewable_but_not_import_eligible(): ...
def test_public_candidate_with_explicit_identity_and_timestamp_builds_ephemeral_entry(): ...
def test_maintainer_stated_need_without_evidence_fails_closed(): ...
def test_available_task_without_task_ref_fails_closed(): ...
def test_claimed_other_remains_claimed_other(): ...
def test_handoff_preview_never_calls_contribution_repository(): ...
```

Without local metadata:

```text
allowed_dispositions = ["WATCH", "DISCARD"]
blocked_reasons includes local_import_metadata_required
```

With explicit `contribution_entry_id` and timezone-aware `contribution_discovered_at`, construct an **ephemeral** existing-domain model:

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

If it validates, offer:

```text
IMPORT_PUBLIC_CONTRIBUTION
WATCH
DISCARD
```

This ephemeral object is compatibility evidence only. Do not persist it.

- [ ] **Step 3: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_preview.py -v
```

- [ ] **Step 4: Implement the pure preview**

Do not import `app.targets`, `SQLiteContributionRepository`, GitHub providers, or any outreach/application module in production handoff code.

Validation errors from the ephemeral contribution model become bounded blocked reasons; never weaken the candidate to make validation pass.

- [ ] **Step 5: Run focused tests and existing contribution model regressions**

```bash
python -m pytest \
  tests/test_handoff_models.py \
  tests/test_handoff_preview.py \
  tests/test_contribution_models.py -v
```

- [ ] **Step 6: Commit**

```bash
git add app/handoffs/preview.py tests/test_handoff_preview.py
git commit -m "feat: preview cross repo opportunity candidates"
```

---

### Task 4: Add file-in/file-out CLI commands with zero mutation authority

**Files:**
- Create: `app/handoffs/intake_cli.py`
- Create: `tests/test_handoff_cli.py`

**Interfaces:**
- Produces two commands:

```text
python -m app.handoffs.intake_cli build-public-candidate
  --question-handoff-file <contract1.json>
  --contribution-preview-file <existing-contribution-preview.json>
  --handoff-id <id>
  --created-at <aware-iso>
  --out <contract2.json>

python -m app.handoffs.intake_cli preview
  --handoff-file <contract2.json>
  --out <preview.json>
  [--contribution-entry-id <id>]
  [--contribution-discovered-at <aware-iso>]
```

There is intentionally **no `import` subcommand** in `app.handoffs.intake_cli`.

- [ ] **Step 1: Write failing CLI tests**

Test:

1. `build-public-candidate` accepts an exact Contract 1 direct-route file plus an existing `IMPORTABLE` `ContributionPreview` with `proposed_entry`;
2. it rejects blocked/no-change/event-only contribution previews;
3. `preview` accepts territorial Contract 2 and produces a reviewable preview;
4. public candidate without local metadata does not offer import;
5. public candidate with explicit local metadata offers import eligibility;
6. malformed/unsupported input -> exit `2`; output file absent;
7. neither command creates SQLite state or constructs an HTTP client;
8. output JSON is stable for identical explicit inputs.

- [ ] **Step 2: Run and confirm RED**

```bash
python -m pytest tests/test_handoff_cli.py -v
```

- [ ] **Step 3: Implement minimal CLI**

Use `QuestionResearchHandoff.model_validate_json()`, `ContributionPreview.model_validate_json()`, and `ResearchOpportunityHandoff.model_validate_json()`.

Build fully in memory before writing output. Emit bounded errors such as:

```json
{"status":"BLOCKED","errors":["invalid_handoff_file"]}
```

Do not expose raw source content or validation internals.

- [ ] **Step 4: Prove the direct GitHub command chain using the existing contribution reader**

The documented operator sequence is:

```bash
python -m app.contributions.intake_cli preview \
  --url https://github.com/example/project/issues/42 \
  --operator-login example-operator \
  --entry-id entry-example-42 \
  --db state/contributions.local.sqlite3 \
  --out /tmp/contribution-preview.json

python -m app.handoffs.intake_cli build-public-candidate \
  --question-handoff-file /tmp/question-handoff.json \
  --contribution-preview-file /tmp/contribution-preview.json \
  --handoff-id roh:example:42 \
  --created-at 2026-09-04T23:00:00+00:00 \
  --out /tmp/research-opportunity-handoff.json
```

The first command is existing read-only provider evidence acquisition; the second is pure adaptation. Neither imports contribution state.

- [ ] **Step 5: Run and confirm GREEN**

```bash
python -m pytest \
  tests/test_handoff_cli.py \
  tests/test_contribution_intake_cli.py -v
```

- [ ] **Step 6: Commit**

```bash
git add app/handoffs/intake_cli.py tests/test_handoff_cli.py
git commit -m "feat: add read only cross repo handoff cli"
```

---

### Task 5: Protect authority boundaries with a release-contract regression

**Files:**
- Create: `tests/test_handoff_release_contract.py`
- Modify: `README.md` minimally.

**Interfaces:**
- Protects architecture rather than adding mutation behavior.

- [ ] **Step 1: Write the release-contract test before README changes**

Assert production `app/handoffs/` has no imports/calls for:

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

Also require a README section containing the exact boundary statements:

```text
handoff preview != import
IMPORT_PUBLIC_CONTRIBUTION != automatic import
PUBLIC_CONTRIBUTION_CANDIDATE != JOB_OPENING
```

The source-architecture assertions may already pass; the new README contract assertion is the intentional RED before Step 3.

- [ ] **Step 2: Run and confirm RED on the missing README contract**

```bash
python -m pytest tests/test_handoff_release_contract.py -v
```

- [ ] **Step 3: Update README minimally**

Document:

- Contract 2 is file-in/read-only-preview in V0.1;
- territorial actors are not target accounts;
- direct GitHub research reuses the existing contribution preview against one explicit resource;
- handoff adaptation does not import state;
- actual contribution import remains the existing exact-preview + human-confirmation path;
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
- Create: `tests/fixtures/handoffs/question_research_public_github_v01.json`
- Create: `tests/fixtures/handoffs/contribution_preview_public_issue_v01.json`
- Create: `tests/fixtures/handoffs/public_contribution_candidate_v01.json`
- Create: `tests/fixtures/handoffs/research_opportunity_water_san_juan_v01.json`
- Create: `tests/test_cross_repo_handoff_dogfood.py`
- Create: `docs/CROSS_REPO_HANDOFF_V01.md`

**Interfaces:**
- Consumes deterministic Contract 1/ContributionPreview/Contract 2 fixtures.
- Produces read-only previews only.

- [ ] **Step 1: Write failing dogfood tests**

Territorial fixture proves:

```text
candidate.kind = ACTOR_NEED_HYPOTHESIS
source_freshness = AS_OF_EXPORT
evidence / assumptions / missing_context remain separate
no TargetAccount is created
no external action is authorized
```

Public GitHub chain proves:

```text
Question Radar Contract 1 direct route
+ existing IMPORTABLE ContributionPreview for one explicit issue
-> PUBLIC_CONTRIBUTION_CANDIDATE
-> read-only handoff preview
```

Also prove task availability/claim state is preserved and no issue/PR state becomes employment-interest evidence.

- [ ] **Step 2: Run and confirm RED because fixtures/docs are absent**

```bash
python -m pytest tests/test_cross_repo_handoff_dogfood.py -v
```

- [ ] **Step 3: Add sanitized fixtures and operator guide**

Fixtures must be fictional or derived only from public evidence and contain no private contacts/job-search state. The water fixture may legitimately yield `WATCH`/`DISCARD`; do not manufacture a customer or buyer.

Document the contribution continuation boundary:

```text
existing ContributionPreview
  -> Contract 2 PUBLIC_CONTRIBUTION_CANDIDATE
  -> handoff preview
  -> operator sees IMPORT_PUBLIC_CONTRIBUTION eligibility
  -> operator returns to the original existing ContributionPreview
  -> explicit confirmed import through ContributionObservationBridge
```

The handoff-generated ephemeral entry is never used as the import payload.

- [ ] **Step 4: Run full local verification**

```bash
python -m pytest -v
python -m compileall app
git diff --check origin/main...HEAD
```

- [ ] **Step 5: Verify repository CI gates on the exact runtime PR head**

Require the existing GitHub Actions suite, including private/generated-file guard, recruiter preview checks, and SHA-bound offline runtime build/verification on supported Python versions. Do not weaken those gates.

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
Contract 1 direct route -> independently validated
public GitHub evidence -> existing Contribution Observation Bridge preview
Contract 2 -> strict tagged union
source freshness -> AS_OF_EXPORT
actor hypothesis -> read-only preview only
actor -> never coerced to TargetAccount
public candidate -> derived only from valid proposed_entry
handoff package -> no DB/network/import path
actual contribution import -> original existing ContributionPreview + bridge only
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