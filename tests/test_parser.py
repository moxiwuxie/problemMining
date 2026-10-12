import pytest

from trendminer.llm.parser import JSONParseError, extract_json


def test_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_json_in_code_fence():
    text = '好的，结果如下：\n```json\n{"old_era": [], "gaps": ["x"]}\n```\n希望有帮助'
    assert extract_json(text) == {"old_era": [], "gaps": ["x"]}


def test_json_with_surrounding_prose():
    text = '分析如下 {"nodes": [{"node_type": "技术落地"}]} 以上。'
    assert extract_json(text)["nodes"][0]["node_type"] == "技术落地"


def test_trailing_comma_is_fixed():
    assert extract_json('{"a": [1, 2,],}') == {"a": [1, 2]}


def test_braces_inside_string_are_ignored():
    text = '{"note": "使用 {a} 占位", "ok": true}'
    assert extract_json(text) == {"note": "使用 {a} 占位", "ok": True}


def test_top_level_array():
    assert extract_json('[{"id": "P1"}]') == [{"id": "P1"}]


def test_invalid_raises():
    with pytest.raises(JSONParseError):
        extract_json("这里完全没有 JSON")
