# Public question corpora

This directory contains intentionally published question-evaluation corpora.

These files are **calibration judgments, not truth labels and not scores of people**.

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
