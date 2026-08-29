import json
from pathlib import Path

from question_radar.profile_export import load_profiles
from question_radar.profiles import QUESTION_TYPES, READINESS_STATES


CORPUS = Path("corpus/anti-ia-calibration-v0.2.jsonl")


def test_calibration_corpus_is_heterogeneous_and_valid():
    profiles = load_profiles(CORPUS, "jsonl")
    assert len(profiles) >= 25
    assert {profile.question_type for profile in profiles} == set(QUESTION_TYPES)
    assert {profile.readiness for profile in profiles} == set(READINESS_STATES)
    assert len({profile.id for profile in profiles}) == len(profiles)


def test_calibration_corpus_encodes_profiles_not_global_ranks():
    rows = [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    forbidden = {"rank", "global_rank", "overall_rank", "leaderboard_position"}
    assert all(not (forbidden & row.keys()) for row in rows)


def test_calibration_includes_low_medium_and_high_formulation_scores():
    scores = [profile.formulation_score for profile in load_profiles(CORPUS, "jsonl")]
    assert min(scores) <= 60
    assert any(65 <= score <= 84 for score in scores)
    assert max(scores) >= 95
