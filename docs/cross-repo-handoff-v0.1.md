# Cross-Repo Research Handoff v0.1

Question Radar can export an operator-authorized investigation state as a deterministic JSON artifact without importing or calling another repository at runtime.

## CLI

```bash
question-radar --db data/questions.sqlite3 \
  decision handoff <question_id> \
  --route TERRITORIAL_RESEARCH \
  --out exports/handoff.json
```

Supported routes:

```text
TERRITORIAL_RESEARCH          -> andes-context-os
PUBLIC_CONTRIBUTION_RESEARCH -> opportunity-os
```

Optional flags:

```text
--canonical-question <text>
--constraint <text>            # repeatable; order is preserved
--handoff-id <id>
--created-at <timezone-aware ISO timestamp>
```

## Current-decision boundary

The CLI always reads the current `InvestigationDecision` for the selected `QuestionNode` from SQLite.

A caller cannot supply a historical `decision_id` to export. If decision B supersedes decision A, a new handoff references B.

Only `DO_NOW` and `RESEARCH` are actionable export states. `PARKED` and `KILLED` fail closed with exit code `2`, and validation completes before the output path is created.

## Authority boundaries

```text
route != opportunity
handoff != evidence
current_at_export != current_now
```

A handoff says that an operator authorized a bounded next investigation at export time. It does not establish:

- a buyer or customer;
- actor authority or problem ownership;
- willingness to pay;
- contact permission;
- a job opening or employment interest;
- public-task availability or claim state;
- live freshness after export.

Question Radar does not call Andes Context OS or Opportunity OS. The JSON file is the versioned boundary between independent systems.

## Sanitized dogfood

Executable regression fixtures:

- `tests/fixtures/handoffs/question_research_water_san_juan_v01.json`
- `tests/fixtures/handoffs/question_research_public_github_v01.json`

Dogfood note:

- `benchmarks/dogfood-cross-repo-handoff-2026-09-04.md`

A downstream result of `NO_ACTIONABLE_CANDIDATE` is valid. Research must not fabricate an opportunity merely to complete the pipeline.
