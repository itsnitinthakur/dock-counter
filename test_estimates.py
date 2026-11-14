import pytest
from odoo_push import compare
from weight_estimate import estimate_units


def test_estimate_units():
    assert estimate_units(14250, 9180, 50, 40) == (101, 5030)


def test_negative_net_rejected():
    with pytest.raises(ValueError):
        estimate_units(1000, 2000, 50)


def test_compare_ok_within_tolerance():
    assert compare(100, 99) == ("OK", -1)


def test_compare_short_and_excess():
    assert compare(100, 90)[0] == "SHORT"
    assert compare(100, 110)[0] == "EXCESS"
