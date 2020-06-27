#!/usr/bin/env python
# coding: utf-8
"""
Lumber Parts
===============
References:

- Table of standard lumber sizes  
  http://mistupid.com/homeimpr/lumber.htm
"""

# !conda install -y -n cq pandas requests beautifulsoup4 requests_cache

import json
import pprint
from fractions import Fraction
from typing import Dict, Iterator, List, Tuple

import requests
import requests_cache
import bs4

import pytest


requests_cache.install_cache("db_lumber_sizes")


def get_lumber_sizes_html() -> bs4.BeautifulSoup:
    LUMBER_SIZES_URL = "http://mistupid.com/homeimpr/lumber.htm"
    resp = requests.get(LUMBER_SIZES_URL)
    bs = bs4.BeautifulSoup(resp.text)
    return bs


def extract_lumber_sizes_table(
    bs: bs4.BeautifulSoup,
) -> Iterator[Tuple[str, str, str]]:
    tbl_html = bs.find_all("table")[2]
    # colnames = ['nominal', 'imperial', 'metric']
    # yield colnames
    for row in tbl_html.find_all("tr")[2:]:
        values = []
        for cell in row.find_all("td"):
            value = cell.text.replace(" ", "").replace("\n", "")
            values.append(value)
        yield tuple(values)


def get_lumber_sizes_table() -> Iterator[Tuple[str, str, str]]:
    return extract_lumber_sizes_table(get_lumber_sizes_html())


@pytest.fixture
def lumber_sizes_table() -> Iterator[Tuple[str, str, str]]:
    return list(get_lumber_sizes_table())


def nominal2fraction(nominalstr: str) -> Fraction:
    _str = nominalstr.rstrip('"')
    components = _str.split("-")
    value = Fraction(components.pop(0))
    if components:
        value += Fraction(components.pop())
    return value


@pytest.mark.parametrize(
    "nominal,fraction",
    [
        ['3/4"', Fraction("3/4")],
        ["1-1/2", Fraction("3/2")],
        ["3-1/2", Fraction("7/2")],
    ],
)
def test_nominal2fraction(nominal, fraction):
    output = nominal2fraction(nominal)
    assert output == fraction


def generate_object(row: Iterator[Tuple[str, str, str]]) -> Dict:
    nominal, imperial, metric = row
    obj = {
        "_row": row,
        "nominal": nominal,
        "imperial": imperial,
        "metric": metric,
    }
    obj["nominal_h__str"], obj["nominal_w__str"] = nominal.split("x")
    obj["imperial_h__str"], obj["imperial_w__str"] = imperial.split("x")
    obj["metric_h__str"], obj["metric_w__str"] = metric.rstrip("m").split("x")

    obj["nominal_h_fraction"] = nominal2fraction(obj["nominal_h__str"])
    obj["nominal_w_fraction"] = nominal2fraction(obj["nominal_w__str"])
    obj["nominal_h_float"] = float(obj["nominal_h_fraction"])
    obj["nominal_w_float"] = float(obj["nominal_w_fraction"])

    obj["imperial_h_fraction"] = nominal2fraction(obj["imperial_h__str"])
    obj["imperial_w_fraction"] = nominal2fraction(obj["imperial_w__str"])
    obj["imperial_h_float"] = float(obj["imperial_h_fraction"])
    obj["imperial_w_float"] = float(obj["imperial_w_fraction"])

    obj["metric_h_float"] = float(obj["metric_h__str"])
    obj["metric_w_float"] = float(obj["metric_w__str"])

    obj["clsstr"] = nominal2clsstr(obj["nominal"])

    return obj


def nominal2clsstr(nominalstr: str) -> str:
    return nominalstr.replace('"', "").replace("-", "__").replace("/", "_")


@pytest.mark.parametrize(
    "nominal,classstr", [["1x4", "1x4"], ['1-1/4"x3-3/4"', "1__1_4x3__3_4"],]
)
def test_nominal2clsstr(nominal, classstr):
    assert nominal2clsstr(nominal) == classstr


class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Fraction):
            return repr(obj)
        return json.JSONEncoder.default(self, obj)


def test_generate_object(lumber_sizes_table):
    obj_keys = [
        "imperial_h__str",
        "imperial_h_float",
        "imperial_h_fraction",
        "imperial_w__str",
        "imperial_w_float",
        "imperial_w_fraction",
        "metric_h__str",
        "metric_h_float",
        "metric_w__str",
        "metric_w_float",
        "nominal",
        "nominal_h__str",
        "nominal_h_float",
        "nominal_h_fraction",
        "nominal_w__str",
        "nominal_w_float",
        "nominal_w_fraction",
    ]
    for row in lumber_sizes_table:
        obj = generate_object(row)
        assert obj
        for key in obj_keys:
            assert key in obj
        # print(pprint.pformat(obj, indent=2))
        # print(obj)
        print(
            json.dumps(obj, cls=DecimalJSONEncoder, indent=1, sort_keys=True)
        )
    # assert False


UNIT_TEXT = {"metric": "metric (mm)", "imperial": "imperial (in)"}


def generate_class(obj, unit="imperial"):
    if unit not in ["metric", "imperial"]:
        raise ValueError("unit must be either 'metric' or 'imperial'")
    class_template = '''
@register("{dict_entry}")
class Lumber{clsstr}(Lumber):
    """a {nominal} ({actual_size}) piece of Lumber"""
    height = PositiveFloat({height}, doc="height of lumber in {unit_text} units (default: {height})")
    width = PositiveFloat({width}, doc="thickness of lumber in {unit_text} units (default: {width})")
'''

    context = {}
    context["unit_text"] = UNIT_TEXT.get(unit)
    context["height"] = obj["%s_h_float" % unit]
    context["width"] = obj["%s_w_float" % unit]
    context["actual_size"] = obj[unit]
    context["dict_entry"] = obj["nominal"].replace('"', "")
    return class_template.format(**context, **obj)


DEFAULT_LENGTH = {"metric": 304.8, "imperial": 12.0}  # ~= 12.0in


def generate_classes(objects, unit="imperial", template="wood_dark"):
    length = DEFAULT_LENGTH.get(unit)
    if length is None:
        raise ValueError("units must be either 'metric' (mm) or 'imperial'")
    unit_text = UNIT_TEXT.get(unit)
    lumbercls = '''
"""
Lumber classes for {unit_text} units
"""
import cqparts
from cqparts.params import PositiveFloat
from cqparts.display import render_props

class Lumber(cqparts.Part):
    length = PositiveFloat({length}, doc="length of lumber in {unit_text} units (default: {length})")
    _render = render_props(template='{template}')

    def make(self):
        return (
            cq.Workplane("XY")
            .box(self.length, self.height, self.width))


CLASSES = {{}}

def register(cls, *keys):
    for key in keys:
        CLASSES[key] = cls
    return cls
'''
    output = []
    output.append(
        lumbercls.format(length=length, unit_text=unit_text, template=template)
    )
    for obj in objects:
        output.append(generate_class(obj, unit=unit))
    return "\n".join(output)


def test_generate_classes(lumber_sizes_table):
    objs = [generate_object(row) for row in lumber_sizes_table]
    for unit in ["imperial", "metric"]:
        print("\n####  %s\n" % unit)
        output = generate_classes(objs, unit=unit)
        assert output
        print(output)
