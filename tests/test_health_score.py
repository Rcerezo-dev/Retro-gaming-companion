from rom_manager.web.builders.library import _health_score


def test_health_score():
    assert _health_score(0, 0, 0)["score"] is None
    assert _health_score(100, 100, 0)["score"] == 100
    h = _health_score(100, 80, 40)  # 80% identificados, 60% sin copias
    assert (h["identified_pct"], h["unique_pct"], h["score"]) == (80, 60, 70)
    assert _health_score(10, 0, 50)["unique_pct"] == 0  # nunca negativo
