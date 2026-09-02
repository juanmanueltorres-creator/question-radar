# Dogfood — Future-building questions (2026-09-01)

## Status

This is an external **dogfood case**, not a blind benchmark, not gold, and not canonical retrieval corpus.

The source post had already been read and discussed with knowledge of Question Radar before these records were committed. The six explicit questions are preserved verbatim in `corpus/dogfood-future-building-2026-09-01.jsonl` so later retrieval methods can inspect the same input without pretending the case was blind.

## Why keep this case

The questions span two related neighborhoods:

1. engineering maintenance versus building what does not yet exist;
2. intelligence, emergent behavior, and future forms of computation.

That makes the set useful for probing boundaries that a lexical retriever can expose but cannot resolve semantically.

## Diagnostic cases to inspect

- **Q2 — `¿Qué es la inteligencia?`**: useful semantic-recall probe. A human may want to review prior questions about conscious experience, knowledge representation, or creativity even when no strong lexical bridge exists.
- **Q3 — `¿Cómo emerge una mente de millones de parámetros?`**: useful accidental-collision probe. The token `millones` can connect unrelated questions such as geological timescales even though the underlying mechanisms differ.
- **Q4 — `¿Qué nuevas formas de computación pueden existir?`**: useful abstention/semantic-recall probe because a lexical layer may have no justified overlap even when broader conceptual neighbors exist.
- **Q5 — `¿Qué ocurre cuando un sistema matemático adquiere comportamientos que nadie programó explícitamente?`**: useful high-IDF weak-term probe. Rare words such as `nadie` can dominate lexical ranking without carrying the main mechanism of the question.
- **Q6 — `¿Acaso se les olvidó lo hermoso que era el futuro?`**: useful rhetorical-language control. Abstention can be preferable to manufacturing a semantic relation from weak evidence.

## Review boundary

Do **not** convert the current lexical misses or collisions into golden expected rankings. Those are the behaviors this case is meant to reveal, not behavior the system should preserve forever.

If a future semantic retrieval layer is evaluated on this case, freeze editorial judgments before tuning against them and keep the candidate questions outside the retrieval corpus. A useful comparison should distinguish:

- retrieval evidence;
- human-reviewed relevance;
- explicit lineage decisions;
- rhetorical or exploratory questions where abstention remains acceptable.
