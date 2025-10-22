def check_probs(probs: dict[str, float]):
    """Валидация величин вероятности"""
    for value in probs.values():
        assert 0 <= value <= 1

    assert abs(sum(probs.values()) - 1) < 1e-6