from utils.helpers import get_current_month

def test_get_current_month_format():
    m = get_current_month()
    assert len(m) == 7
    assert m[4] == "-"
    assert m[:4].isdigit()
    assert m[5:].isdigit()
