from humility.responses import compassionate_response, reframe_instructions


def test_compassionate_response_never_empty():
    out = compassionate_response(["Humility 1: metaphysical"])
    assert "What you can do" in out
    assert "SAIVAS" in out


def test_reframe_returns_none_for_hard_deny_only():
    assert reframe_instructions(["Humility 1: metaphysical"]) is None


def test_reframe_for_uncertainty():
    out = reframe_instructions(["Humility 2: uncertainty"])
    assert out is not None
    assert "uncertainty" in out.lower()
