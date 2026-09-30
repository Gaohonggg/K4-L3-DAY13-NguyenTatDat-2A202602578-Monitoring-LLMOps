from app.metrics import percentile


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) == 200
    assert percentile([100, 200, 300, 400], 95) == 400
