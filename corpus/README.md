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
