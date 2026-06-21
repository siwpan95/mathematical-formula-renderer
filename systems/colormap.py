"""
ColorSystem — 颜色映射系统
============================
源自：engine.CARenderEngine
    - _eval_channel()     → _eval_channel()
    - get_color_array()   → get_rgb()
    - fill_color_wh()     → fill_rgb_wh()
    - ColorPresets.apply() → apply_preset()（从 renderer 迁入）

职责：
    每帧读取 GridComponent.data，计算 RGB 三通道并写入 GridComponent.rgb_hw。
    支持运行时颜色预设覆盖（不改变 ConfigComponent，临时覆盖 FormulaComponent.color_fns）。
"""

from __future__ import annotations
import numpy as np

from entities.recipe import RecipeEntity
from components.grid import GridComponent
from components.formula import FormulaComponent


# 颜色预设（从 renderer.ColorPresets 迁入）
COLOR_PRESETS = {
    'default': {'red': 'v', 'green': 'v', 'blue': 'v'},
    'fire':    {'red': 'minimum(v*3, 1.0)',
                'green': 'maximum(0, minimum((v-0.33)*3, 1.0))',
                'blue':  'maximum(0, (v-0.66)*3)'},
    'ocean':   {'red': 'v*0.1',
                'green': 'v*0.6 + 0.2*sin(v*15)',
                'blue':  'v*0.8 + 0.2'},
    'sunset':  {'red': 'v*0.9 + (1-v)*0.05',
                'green': 'v*0.3 + (1-v)*0.05',
                'blue':  'v*0.1 + (1-v)*0.3'},
    'rainbow': {'red': '0.5+0.5*sin(v*12)',
                'green': '0.5+0.5*sin(v*12+2.094)',
                'blue':  '0.5+0.5*sin(v*12+4.189)'},
    'neon':    {'red': 'v*0.5 + 0.5*sin(v*25)',
                'green': 'v*0.5 + 0.5*sin(v*25+2.094)',
                'blue':  'v*0.8 + 0.2*sin(v*20)'},
    'ice':     {'red': 'v*0.3', 'green': 'v*0.8', 'blue': '1.0 - v*0.4'},
    'invert':  {'red': '1-v', 'green': '1-v', 'blue': '1-v'},
    'thermal': {'red': 'v', 'green': 'v*0.5', 'blue': '0.5 + 0.5*sin(v*10)'},
}


class ColorSystem:
    """颜色映射系统（对应 engine.get_color_array + renderer.ColorPresets）。

    使用方式：
        system = ColorSystem()
        system.update(entity)   # 每帧调用，写入 entity.grid.rgb_hw
    """

    def update(self, entity: RecipeEntity):
        """计算当前帧 RGB（写入 grid.rgb_hw）"""
        grid = entity.grid
        formula = entity.formula

        if grid.data is None or not formula.is_ready:
            return

        v = grid.data.astype(np.float64)
        r = self._eval_channel(formula.color_fns['red'],   v, grid)
        g = self._eval_channel(formula.color_fns['green'],  v, grid)
        b = self._eval_channel(formula.color_fns['blue'],   v, grid)

        # 直接写入 rgb_wh (w,h,3) 格式，供 blit_array 零拷贝使用
        if grid.rgb_wh is None:
            grid.rgb_wh = np.zeros((grid.w, grid.h, 3), dtype=np.uint8)
        grid.rgb_wh[:, :, 0] = (r.T * 255).astype(np.uint8)
        grid.rgb_wh[:, :, 1] = (g.T * 255).astype(np.uint8)
        grid.rgb_wh[:, :, 2] = (b.T * 255).astype(np.uint8)
        # 同步 rgb_hw（视图，零拷贝）
        grid.rgb_hw = grid.rgb_wh.transpose(1, 0, 2)

        # 后处理已统一收口到 RenderSystem，此处不再重复执行
        pass

    # ── 颜色预设（对应 renderer.ColorPresets.apply）─────────────────────

    def apply_preset(self, entity: RecipeEntity, preset_name: str,
                     evolution_system: 'EvolutionSystem') -> bool:
        """覆盖颜色函数为预设（对应 ColorPresets.apply）"""
        from systems.evolution import EvolutionSystem
        if preset_name not in COLOR_PRESETS:
            return False
        col = COLOR_PRESETS[preset_name]
        formula = entity.formula
        for ch in ['red', 'green', 'blue']:
            expr = col.get(ch, '0.0')
            formula.color_fns[ch] = evolution_system._compile(
                expr, ['v', 'x', 'y'], formula._cache)
        return True

    # ── 内部 ────────────────────────────────────────────────────────────

    def _eval_channel(self, func, v: np.ndarray,
                      grid: GridComponent) -> np.ndarray:
        """计算单通道（对应 engine._eval_channel）"""
        ch = func(v=v, x=grid.x_coords, y=grid.y_coords)
        ch = np.asarray(ch, dtype=np.float64)
        if ch.shape != (grid.h, grid.w):
            ch = np.broadcast_to(
                ch.ravel()[0:1], (grid.h, grid.w)).astype(np.float64)
        return np.clip(ch, 0.0, 1.0)

    def get_rgb_hw(self, entity: RecipeEntity) -> np.ndarray:
        """获取 (h,w,3) uint8 数组（对应 engine.get_color_array）"""
        if entity.grid.rgb_hw is None:
            self.update(entity)
        return entity.grid.rgb_hw

    def _apply_postprocess(self, grid: GridComponent, effect: str):
        """应用后处理特效"""
        rgb = grid.rgb_wh.astype(np.float32) / 255.0

        if effect == 'invert':
            rgb = 1.0 - rgb
        elif effect == 'vignette':
            h, w = rgb.shape[:2]
            y = np.linspace(-1, 1, h)[:, None]
            x = np.linspace(-1, 1, w)[None, :]
            vignette = 1.0 - 0.5 * (x**2 + y**2)
            rgb *= vignette[:, :, None]
        elif effect == 'gaussian_blur':
            import numpy as _np
            from scipy.ndimage import convolve1d
            sigma = 1.0
            radius = int(3 * sigma)
            x = _np.arange(-radius, radius + 1, dtype=_np.float32)
            kernel = _np.exp(-0.5 * (x / sigma) ** 2)
            kernel /= kernel.sum()
            for c in range(3):
                h = convolve1d(rgb[:, :, c], kernel, mode='nearest')
                rgb[:, :, c] = convolve1d(h, kernel, axis=0, mode='nearest')

        grid.rgb_wh = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
        grid.rgb_hw = grid.rgb_wh.transpose(1, 0, 2)
