"""
兼容性保留 — v1 遗留别名

CanvasState 是 CanvasGraph 的旧名称，保留以免破坏外部 import。
"""

from models.domain import CanvasGraph

CanvasState = CanvasGraph
