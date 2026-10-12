"""LLM 输出解析：从可能很脏的文本中稳健地提取 JSON。"""
from __future__ import annotations

import json
import re
from typing import Any


class JSONParseError(ValueError):
    """无法从文本中解析出 JSON。"""


_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def _strip_fences(text: str) -> str:
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _balanced_slice(text: str, open_ch: str, close_ch: str) -> str | None:
    """从第一个 open_ch 起，按括号配对截取到匹配的 close_ch（忽略字符串内的括号）。"""
    start = text.find(open_ch)
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    # 未闭合：返回剩余部分，交给修复逻辑
    return text[start:]


def _try_loads(candidate: str) -> Any | None:
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    fixed = _TRAILING_COMMA_RE.sub(r"\1", candidate)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        return None


def extract_json(text: str) -> Any:
    """尽力从文本中提取 JSON 对象/数组。失败抛 JSONParseError。"""
    if text is None:
        raise JSONParseError("输入为空")
    cleaned = _strip_fences(str(text))

    # 1) 直接解析
    result = _try_loads(cleaned)
    if result is not None:
        return result

    # 2) 从第一个 { 或 [ 做括号配对
    candidates = []
    obj = _balanced_slice(cleaned, "{", "}")
    arr = _balanced_slice(cleaned, "[", "]")
    # 谁先出现先试谁
    ordered = sorted(
        [c for c in (obj, arr) if c],
        key=lambda c: cleaned.find(c[0]),
    )
    candidates.extend(ordered)

    # 3) 首 { 到末 } 的粗暴截取
    lb, rb = cleaned.find("{"), cleaned.rfind("}")
    if lb != -1 and rb > lb:
        candidates.append(cleaned[lb : rb + 1])
    la, ra = cleaned.find("["), cleaned.rfind("]")
    if la != -1 and ra > la:
        candidates.append(cleaned[la : ra + 1])

    for cand in candidates:
        result = _try_loads(cand)
        if result is not None:
            return result

    raise JSONParseError(f"无法解析 JSON，原始文本前 200 字: {cleaned[:200]!r}")
