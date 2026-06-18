"""
GridComponent — 网格状态数据容器
==================================
源自：engine.CARenderEngine 中的 self.grid / x_grid / y_grid / kernel 等字段

职责：
    持有 CA 网格的所有运行时数组数据。
    不含演化逻辑——EvolutionSystem 负责读写本组件。
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


@dataclass
class GridComponent:
    """CA 网格的运行时数组状态。

    所有数组由 EvolutionSystem 初始化后挂载到此组件，
    后续每帧由 EvolutionSystem 就地更新。

    属性（原来散落在 engine.py __init__ 和 _reset_grid / _build_coordinate_grids）：

        self.grid      → data       (h×w float32，细胞状态，0~1)
        self.x_grid    → x_coords   (h×w float64，归一化 x 坐标)
        self.y_grid    → y_coords   (h×w float64，归一化 y 坐标)
        self.kernel    → kernel     (邻域核矩阵 float32)
        self.t         → t          (时间步计数)
        self.w,self.h  → w,h        (网格尺寸)
        self.wrap      → wrap
        self._total_cycles → total_cycles
    """

    # ── 尺寸 & 边界 ──
    w: int = 256
    h: int = 192
    wrap: bool = True

    # ── 核心数组（None 表示尚未初始化，由 EvolutionSystem 负责初始化）──
    data: np.ndarray | None = None        # (h, w) float32
    x_coords: np.ndarray | None = None   # (h, w) float64
    y_coords: np.ndarray | None = None   # (h, w) float64
    kernel: np.ndarray | None = None     # (2r+1, 2r+1) float32

    # ── 时间状态 ──
    t: int = 0
    total_cycles: int = 0

    # ── 预分配的颜色输出缓冲区（由 ColorSystem 使用）──
    rgb_hw: np.ndarray | None = None     # (h, w, 3) uint8
    rgb_wh: np.ndarray | None = None     # (w, h, 3) uint8

    def reset_t(self):
        """重置时间步"""
        self.t = 0
        self.total_cycles = 0

    @property
    def is_ready(self) -> bool:
        """返回网格是否已完成初始化"""
        return (self.data is not None
                and self.x_coords is not None
                and self.kernel is not None)

    def get_stats(self) -> dict:
        """获取网格统计信息（对应 engine.get_grid_stats）"""
        if self.data is None:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0, 'alive': 0}
        return {
            'min':   float(self.data.min()),
            'max':   float(self.data.max()),
            'mean':  float(self.data.mean()),
            'std':   float(self.data.std()),
            'alive': float((self.data > 0.01).mean()),
        }
