#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the demoflask module.
"""
import pytest

from demoflask import demoflask


def test_something():
    assert True


def test_with_error():
    with pytest.raises(ValueError):
        # Do something that raises a ValueError
        raise(ValueError)


# Fixture example
@pytest.fixture
def an_object():
    return {}


def test_demoflask(an_object):
    assert an_object == {}
