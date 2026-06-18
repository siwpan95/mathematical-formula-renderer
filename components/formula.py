"""
FormulaComponent — 编译后的公式函数容器
=========================================
源自：engine.CARenderEngine._compile / _compile_numeric / _compile_logic
      以及 self.init_func / self.rule_func / self.color_funcs / self._compile_cache

职责：
    持有三类已编译函数（init / evolution / color 各通道）及编译缓存。
    不含编译逻辑——编译由 FormulaCompiler（systems/formula_compiler.py）完成。
    System 通过本组件获取函数，直接调用进行数值计算。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any


# 函数签名约定（与 engine.py 保持一致）：
#   init_func  (**{x, y, i, j, random}) → np.ndarray | float
#   rule_func  (**{c, sum_n, avg_n, x, y, t, i, j}) → np.ndarray | float
#   color_func (**{v, x, y}) → np.ndarray | float

FormulaFn = Callable[..., Any]


@dataclass
class FormulaComponent:
    """编译后的公式函数 + 共享编译缓存。

    工作流：
        1. ConfigComponent 持有原始表达式字符串
        2. FormulaCompilerSystem（新增辅助 System）读取 ConfigComponent，
           调用 engine._compile（或其 ECS 等价实现），将结果写入本组件
        3. EvolutionSystem / ColorSystem 直接从本组件取函数调用

    属性映射（engine.py → FormulaComponent）：
        self.init_func          → init_fn
        self.rule_func          → rule_fn
        self.color_funcs['red'] → color_fns['red']
        self._compile_cache     → _cache
    """

    # ── 已编译的函数 ──
    init_fn: FormulaFn | None = None       # 初始化公式
    rule_fn: FormulaFn | None = None       # 演化规则公式
    color_fns: dict[str, FormulaFn] = field(
        default_factory=lambda: {'red': None, 'green': None, 'blue': None})

    # ── 编译缓存（可在同一 World 中跨 Entity 共享）──
    _cache: dict = field(default_factory=dict)

    @property
    def is_ready(self) -> bool:
        """所有公式均已编译完成"""
        return (self.init_fn is not None
                and self.rule_fn is not None
                and all(v is not None for v in self.color_fns.values()))

    def invalidate(self):
        """清空编译结果（配方切换时调用）"""
        self.init_fn = None
        self.rule_fn = None
        self.color_fns = {'red': None, 'green': None, 'blue': None}
        # 注意：_cache 保留，跨 Entity 共享编译结果
