"""Component 层 — 纯数据容器，不含业务逻辑"""
from components.config import ConfigComponent
from components.grid import GridComponent
from components.formula import FormulaComponent
from components.postprocess import PostProcessComponent

__all__ = [
    'ConfigComponent',
    'GridComponent',
    'FormulaComponent',
    'PostProcessComponent',
]
