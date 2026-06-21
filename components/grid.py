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

    def build_kernel(self, topology: str = 'square',
                      nb_type: str = 'moore', nb_radius: int = 1) -> np.ndarray:
        """
        根据拓扑和邻域类型构建卷积核。
        topology:  'square' | 'hexagonal' | 'triangular'
        nb_type:   'moore' | 'von_neumann' | 'hex' | 'radius2' | 'weighted'
        nb_radius: 卷积核半径（目前仅 radius2 使用 >1）
        """
        # radius2 强制用半径2，忽略 nb_radius
        radius = 2 if nb_type == 'radius2' else nb_radius
        size = 2 * radius + 1
        k = np.zeros((size, size), dtype=np.float32)
        cx = cy = radius

        if topology == 'hexagonal':
            # 六边形近似：在方形格点上给6个近邻更高权重
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, 1), (1, -1)]  # 六边形6邻域（偏移奇偶行）
            for dx, dy in offsets:
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    k[y, x] = 1.0
        elif topology == 'triangular':
            # 三角形格点近似：12邻域
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, -1), (-1, 1), (1, 1),
                       (-2, 0), (2, 0), (0, -2), (0, 2)]
            for dx, dy in offsets:
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    k[y, x] = 1.0 / (abs(dx) + abs(dy))
        else:  # square
            if nb_type == 'moore':
                for dx in range(-nb_radius, nb_radius + 1):
                    for dy in range(-nb_radius, nb_radius + 1):
                        if dx == 0 and dy == 0:
                            continue
                        k[cy + dy, cx + dx] = 1.0
            elif nb_type == 'von_neumann':
                for dx in range(-nb_radius, nb_radius + 1):
                    for dy in range(-nb_radius, nb_radius + 1):
                        if dx == 0 and dy == 0:
                            continue
                        if abs(dx) + abs(dy) <= nb_radius:
                            k[cy + dy, cx + dx] = 1.0
            elif nb_type == 'radius2':
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx == 0 and dy == 0:
                            continue
                        if dx*dx + dy*dy <= 4:
                            k[cy + dy, cx + dx] = 1.0
            elif nb_type == 'weighted':
                for dx in range(-nb_radius, nb_radius + 1):
                    for dy in range(-nb_radius, nb_radius + 1):
                        if dx == 0 and dy == 0:
                            continue
                        w = 1.0 / max(1, abs(dx) + abs(dy))
                        k[cy + dy, cx + dx] = w
            else:  # 默认 moore
                for dx in range(-nb_radius, nb_radius + 1):
                    for dy in range(-nb_radius, nb_radius + 1):
                        if dx == 0 and dy == 0:
                            continue
                        k[cy + dy, cx + dx] = 1.0

        # 归一化（使核和为1，保持总量守恒）
        s = k.sum()
        if s > 0:
            k /= s
        else:
            k[cy, cx] = 1.0  # 退化情况

        self.kernel = k
        return k
