"""
响应解析器 — 从 LLM 输出中提取 JSON。

从 conversation.py 和 skill_router.py 提取，v2 重构。
"""

import json
import re
import logging

log = logging.getLogger("response_parser")


def parse_json_response(text: str, field: str = "reply") -> dict:
    """
    从 LLM 文本输出中提取 JSON。

    尝试顺序：
      1. ```json ``` 代码块
      2. 整段 JSON
      3. 降级：纯文本作为 reply
    """
    # 1. 尝试 code block
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            log.warning(f"JSON parse error in code block: {e}")

    # 2. 尝试整段 JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. 降级
    cleaned = re.sub(r"```json.*?```", "", text, flags=re.DOTALL).strip()
    if not cleaned or cleaned.startswith("{"):
        cleaned = text[:500]
    log.warning(f"Response parse failed, using raw text ({len(cleaned)} chars)")
    return {field: cleaned, "canvas_updates": {}}


def parse_router_response(text: str) -> list[tuple[str, str]]:
    """
    从路由 LLM 输出中提取技能列表。

    返回: [(skill_id, reason), ...]
    """
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            items = json.loads(match.group())
            return [(item["skill_id"], item["reason"]) for item in items]
        except (json.JSONDecodeError, KeyError) as e:
            log.warning(f"Router response parse error: {e}")
    return []
