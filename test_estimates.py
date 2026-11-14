from odoo_push import compare


def test_compare_ok_within_tolerance():
    assert compare(100, 99) == ("OK", -1)


def test_compare_short_and_excess():
    assert compare(100, 90)[0] == "SHORT"
    assert compare(100, 110)[0] == "EXCESS"
