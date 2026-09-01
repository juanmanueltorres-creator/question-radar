import pytest

from question_radar.novelty import normalize_tokens
from question_radar.retrieval_text import normalize_retrieval_tokens


def test_retrieval_normalizer_handles_accents_and_case():
    assert normalize_retrieval_tokens("DECISIÓN Técnica") == ("decision", "tecnica")


def test_retrieval_normalizer_removes_low_information_words():
    tokens = normalize_retrieval_tokens(
        "pero tan sus sin más sobre principal cuando quien sistema"
    )
    assert tokens == ("sistema",)


def test_retrieval_normalizer_applies_conservative_spanish_plural_rules():
    assert normalize_retrieval_tokens(
        "costos sistemas personas errores decisiones sensores"
    ) == ("costo", "sistema", "persona", "error", "decision", "sensor")


def test_retrieval_normalizer_does_not_stem_conjugated_verbs():
    assert normalize_retrieval_tokens(
        "entienden modifica pierde puedes tomas usas trabajas"
    ) == (
        "entienden",
        "modifica",
        "pierde",
        "puedes",
        "tomas",
        "usas",
        "trabajas",
    )


def test_retrieval_normalizer_rejects_blank_text():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        normalize_retrieval_tokens("   ")


def test_v05_novelty_normalizer_remains_unchanged():
    # v0.7 must not silently rewrite the frozen v0.5 normalization contract.
    assert normalize_tokens("costos sistemas pero") == ("costos", "sistemas", "pero")
