# Public question corpora

This directory contains intentionally published question-evaluation corpora and blind calibration inputs.

These files are **calibration judgments or source questions, not truth labels and not scores of people**.

## Anti IA seed v0.1

`anti-ia-seed-v0.1.jsonl` is the first calibration cohort derived from the Anti IA master question library.

It contains 15 representative questions spanning territory, evidence, uncertainty, decision-making, power, coordination, memory, interdisciplinarity, technology, AI, and epistemology.

The scores are **not truth claims and do not rank people**. They are a reproducible first-pass evaluation under rubric `v0.1` intended to expose strengths, gaps, and stronger follow-up questions.

Calibration rule: if repeated human review shows that a dimension or score does not reflect useful question quality, change the rubric/version rather than silently changing historical evaluations.

## Anti IA calibration v0.2

`anti-ia-calibration-v0.2.jsonl` profiles a deliberately heterogeneous set of Anti IA questions by:

- question type;
- readiness;
- formulation dimensions;
- descriptive traits;
- assumptions;
- evidence requirements;
- stronger next-question direction.

Question Radar v0.2 intentionally does **not** define a global ranking across question types. A factual question, an operational question, and a philosophical question can all be excellent for different purposes.

The v0.2 corpus is an explicit new evaluation. It is not an automatic conversion of v0.1 scores, and the v0.1 corpus remains historical calibration evidence.

## Real chat corpus — 2026-08-29

`chat-2026-08-29.jsonl` preserves 12 questions that emerged naturally during a live conversation about education, expertise, question quality, and the design of Question Radar itself.

The source wording is kept as the `question`. Any refinement lives separately in `next_question`, so the dataset preserves the difference between a spontaneous question and its proposed evolution.

This corpus is useful for testing Question Radar against questions produced during real thinking rather than questions selected in advance from an editorial library.

## Personal Learning Frontier calibration v0.3

`learning-frontier-chat-2026-08-29-v0.3.jsonl` contains three intentionally published learning observations derived only from evidence IDs in the 12-question real chat corpus.

These records are **revisable hypotheses about observable question patterns**, not truth labels about a person. The evidence references stay explicit and ordered so every observation can be inspected against its source questions.

The calibration deliberately includes repeated educational questions that remain `possible_gap` rather than becoming `recurring_gap`: recurrence is ambiguous and can reflect emphasis, disagreement, changed context, weak prior explanations, or an unresolved evidence question.

No learner is ranked or scored by this corpus.

## Blind organizational-memory benchmark — 2026-09-01

`blind-memory-2026-09-01.jsonl` preserves the 25-question output of a separate blind chat about organizational memory, knowledge loss, tacit knowledge, documentation, incentives, and forgetting.

The generating chat was not given the Question Radar repository, rubric, lineage vocabulary, master-question library, or prior benchmark interpretation. The wording is preserved exactly as generated and the file contains only candidate IDs plus raw questions.

This file is **not canonical lineage and is not imported as master questions**. It is a v0.5 calibration input used to test corpus-relative retrieval, residual-token evidence, and provisional clustering without contaminating the corpus it is compared against.

In particular, the benchmark exposed a useful failure mode for simple “best question” selection: a highly rated question may already be represented by the corpus, while a less obvious question may introduce a residual mechanism such as obsolescence or adaptive forgetting. v0.5 surfaces evidence for review; it does not promote that interpretation automatically.

## Blind decision-under-uncertainty benchmark — 2026-09-01

`blind-decision-uncertainty-2026-09-01.jsonl` preserves the first 25-question output of a separate blind chat about decision-making under incomplete, contradictory, uncertain, or changing evidence.

The generating chat was instructed not to use prior conversations, repositories, memory, external research, or Question Radar context. The 25 question strings are preserved exactly and the file contains only candidate IDs plus raw questions.

This file is **calibration input, not canonical corpus**. It was generated after v0.5 had already been merged and exposed a retrieval-recall failure: v0.5 treated every blind question as a possible new branch even though v0.2 already contained relevant prior questions outside the v0.4 lineage snapshot.

The primary v0.6 golden regression uses blind question 7 — `¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?` — and requires candidate retrieval to surface `qv2-cal-013`, `¿Cuál es el costo de actuar y de no actuar?`, within the top five results. The regression asserts retrieval only; it does not claim semantic equivalence, a lineage relation, or master promotion.

## Blind system-trust benchmark — 2026-09-01

`blind-system-trust-2026-09-01.jsonl` preserves the first 24-question output of a separate blind chat about deciding with software, models, sensors, automation, and other systems that users do not fully understand.

The generating chat was instructed not to use prior conversations, repositories, memory, external research, or Question Radar context. The questions are stored exactly as generated and remain **external calibration input, not canonical lineage or profiles**.

This benchmark exposed the next retrieval boundary after v0.6: corpus visibility had improved, but BM25 could still overvalue low-information lexical collisions and Spanish plural morphology could hide useful prior questions. It also exposed that a zero-evidence query should be allowed to abstain rather than return arbitrary rows.

v0.7 pre-registers only strong retrieval labels that fit its declared lexical scope:

- Q1 must retrieve `vault-2026-08-31-001` within the top five;
- Q14 must retrieve `qv2-cal-013` within the top five;
- the earlier decision-under-uncertainty Q7 must remain a top-five `qv2-cal-013` hit.

Q16 and Q24 are deliberately preserved as diagnostic controls rather than forced successes. Q16 gains weak `persona/personas` evidence once plural normalization is introduced, so forcing abstention would contradict the normalizer. Q24 still depends on the unimplemented verbal relation `entienden/entender`, so forcing it into the top five would require stemming or semantic assistance outside v0.7 scope.

## Blind representations benchmark + Gold v1 — 2026-09-01

`blind-representations-2026-09-01.jsonl` preserves the 23-question output of a separate blind chat about metrics, maps, categories, indicators, dashboards, rankings, and other simplified representations of complex realities.

The raw benchmark is **evaluation input, not canonical retrieval corpus**. It was generated after v0.7 had been frozen and is not imported into v0.2 profiles or v0.4 lineage.

`gold/blind-representations-2026-09-01-gold-v1.jsonl` freezes eight editorial review cases before any semantic retrieval layer is implemented. The labels mean that a prior question is useful to review before treating the candidate as new; they do **not** claim semantic equivalence, lineage, or duplication.

Gold v1 deliberately mixes two judgment scopes:

- `positive_only`: listed positive antecedents are judged useful, while every unlisted corpus entry remains **unjudged**, not negative;
- `exhaustive`: the case has been reviewed as an explicit control. Q13 and Q22 are exhaustive expected-abstention controls.

Because the positive cases are sparse rather than exhaustively judged, v0.8 reports Hit Rate@5, macro Recall@5, MRR, false abstentions, and abstention-control accuracy but withholds Precision@5. Treating every unjudged result as a negative would manufacture a precision number unsupported by the annotation protocol.

The frozen pre-semantic v0.7 snapshot is:

`baselines/blind-representations-2026-09-01-v0.7-baseline.json`

At `k=5` over the 51-entry canonical evaluation snapshot it records:

- Hit Rate@5: `0.5`;
- macro Recall@5: `0.5`;
- MRR: `0.5`;
- false abstentions on positive cases: `2`;
- abstention controls: `2/2` correct;
- Precision@5: unavailable by design because Gold v1 contains `positive_only` judgments.

That baseline is intended for later comparisons with candidate retrieval methods. A future semantic system must improve against the frozen gold without rewriting the gold after seeing its results.