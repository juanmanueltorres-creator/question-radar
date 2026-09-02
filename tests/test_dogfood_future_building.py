import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOGFOOD = ROOT / "corpus" / "dogfood-future-building-2026-09-01.jsonl"


def _jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_future_building_dogfood_preserves_exact_six_questions():
    records = _jsonl(DOGFOOD)

    assert len(records) == 6
    assert [record["id"] for record in records] == [
        f"future-building-dogfood-2026-09-01-{index:03d}"
        for index in range(1, 7)
    ]
    assert [set(record) for record in records] == [{"id", "question"}] * 6
    assert [record["question"] for record in records] == [
        "¿En qué momento dejamos de construir el futuro para dedicarnos exclusivamente a mantener funcionando la infraestructura que heredamos?",
        "¿Qué es la inteligencia?",
        "¿Cómo emerge una mente de millones de parámetros?",
        "¿Qué nuevas formas de computación pueden existir?",
        "¿Qué ocurre cuando un sistema matemático adquiere comportamientos que nadie programó explícitamente?",
        "¿Acaso se les olvidó lo hermoso que era el futuro?",
    ]
