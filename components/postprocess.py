"""
PostProcessComponent — 后处理特效状态容器
==========================================
源自：renderer.PostProcess（静态方法集合）+ renderer 主循环中的 effect_name 变量

职责：
    持有当前激活的特效名称 + 特效所需的帧缓冲（如 motion_trail 的历史帧）。
    将 renderer.PostProcess 从「静态方法集」升级为「有状态组件 + 无状态系统」。
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


# 所有支持的特效名称（对应 renderer.PostProcess.EFFECTS）
EFFECT_NAMES = ('none', 'bloom', 'edge', 'motion_trail', 'invert', 'vignette')


@dataclass
class PostProcessComponent:
    """后处理特效的运行时状态。

    属性映射（renderer.py → PostProcessComponent）：
        effect_name 变量           → active_effect
        PostProcess._trail_buffer  → trail_buffer
        PostProcess._trail_decay   → trail_decay
    """

    active_effect: str = 'none'     # 当前激活的特效

    # motion_trail 专属缓冲（原来以类变量形式挂在 PostProcess 上，现在归属明确）
    trail_buffer: np.ndarray | None = None
    trail_decay: float = 0.85

    def set_effect(self, name: str) -> bool:
        """切换特效，返回是否切换成功"""
        if name not in EFFECT_NAMES:
            return False
        if name != self.active_effect:
            self.active_effect = name
            if name != 'motion_trail':
                self.trail_buffer = None   # 切换特效时清空轨迹缓冲
        return True

    def cycle_next(self):
        """循环切换到下一个特效"""
        idx = list(EFFECT_NAMES).index(self.active_effect)
        self.active_effect = EFFECT_NAMES[(idx + 1) % len(EFFECT_NAMES)]
        if self.active_effect != 'motion_trail':
            self.trail_buffer = None
