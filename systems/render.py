"""
RenderSystem — Pygame 帧渲染系统
===================================
源自：renderer.py 主循环中的 Pygame Surface 绘制逻辑
    - surfarray.blit_array()  → draw()
    - PostProcess.apply()     → _apply_postfx()
    - TransitionManager       → 保留为内部 helper

职责：
    读取 GridComponent.rgb_hw，应用后处理特效，blit 到 Pygame Surface。
    不含演化逻辑，不读取 formula/config（只需要最终 RGB）。

System 接口：
    system = RenderSystem(screen, ca_rect)
    system.draw(entity)          # 每帧调用
    system.start_transition()    # 切换配方时调用
"""

from __future__ import annotations
import numpy as np

from entities.recipe import RecipeEntity
from components.postprocess import PostProcessComponent, EFFECT_NAMES

try:
    import pygame
    import pygame.surfarray as surfarray
    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False


class RenderSystem:
    """Pygame 帧渲染系统（对应 renderer.py 主循环的绘制段）。

    使用方式：
        system = RenderSystem(screen, ca_rect=(x, y, w, h))
        system.draw(entity)

    ca_rect: (x, y, w, h) — CA 画面在窗口中的位置和大小（像素坐标）
    """

    def __init__(self, screen=None, ca_rect: tuple = (0, 0, 640, 480)):
        self.screen = screen
        self.ca_rect = ca_rect   # (x, y, w, h)
        self._transition = _TransitionManager()
        self._ca_surface = None  # 缓存 Surface

    def set_screen(self, screen, ca_rect: tuple):
        """延迟设置屏幕（World 初始化后调用）"""
        self.screen = screen
        self.ca_rect = ca_rect
        self._ca_surface = None

    def draw(self, entity: RecipeEntity):
        """渲染一帧（对应 renderer 主循环的绘制段）"""
        if not _PYGAME_AVAILABLE or self.screen is None:
            return
        grid = entity.grid
        if grid.rgb_hw is None:
            return

        x, y, dw, dh = self.ca_rect
        gw, gh = grid.w, grid.h

        # 获取/创建 CA Surface
        if (self._ca_surface is None
                or self._ca_surface.get_size() != (gw, gh)):
            self._ca_surface = pygame.Surface((gw, gh))

        # 应用后处理
        rgb = self._apply_postfx(grid.rgb_hw, entity.postfx, entity)
        # rgb shape: (h, w, 3) → surfarray 需要 (w, h, 3)
        surfarray.blit_array(self._ca_surface, rgb.transpose(1, 0, 2))

        # 缩放到目标区域
        if (dw, dh) == (gw, gh):
            scaled = self._ca_surface
        else:
            scaled = pygame.transform.scale(self._ca_surface, (dw, dh))

        # 过渡动画
        if self._transition.is_active():
            self._transition.apply(self.screen, scaled, x, y)
        else:
            self.screen.blit(scaled, (x, y))

    def start_transition(self):
        """配方切换时触发淡入过渡（对应 renderer.TransitionManager.start）"""
        if self._ca_surface is not None:
            self._transition.start(self._ca_surface)

    def update_transition(self):
        """更新过渡动画帧"""
        self._transition.update()

    def apply_transition(self, screen, surf, x, y):
        """在屏幕上应用过渡效果"""
        if self._transition.is_active():
            self._transition.apply(screen, surf, x, y)
            return True
        return False

    # ── 后处理（对应 renderer.PostProcess，逻辑搬过来，状态在 Component）──

    def _apply_postfx(self, rgb: np.ndarray,
                      postfx: PostProcessComponent,
                      entity: RecipeEntity) -> np.ndarray:
        """应用后处理特效，返回处理后的 (h,w,3) uint8 数组"""
        name = postfx.active_effect
        if name == 'none':
            return rgb
        elif name == 'bloom':
            return self._bloom(rgb)
        elif name == 'edge':
            return self._edge(rgb)
        elif name == 'motion_trail':
            return self._motion_trail(rgb, postfx)
        elif name == 'invert':
            return 255 - rgb
        elif name == 'vignette':
            return self._vignette(rgb)
        return rgb

    @staticmethod
    def _bloom(rgb: np.ndarray) -> np.ndarray:
        from scipy.ndimage import gaussian_filter
        blurred = np.zeros_like(rgb, dtype=np.float32)
        for c in range(3):
            blurred[:, :, c] = gaussian_filter(
                rgb[:, :, c].astype(np.float32), sigma=1.2)
        return np.clip(rgb.astype(np.float32) + blurred * 0.4, 0, 255
                       ).astype(np.uint8)

    @staticmethod
    def _edge(rgb: np.ndarray) -> np.ndarray:
        from scipy.ndimage import sobel
        v = rgb.astype(np.float32).mean(axis=2)
        edges = np.sqrt(sobel(v, axis=0) ** 2 + sobel(v, axis=1) ** 2)
        if edges.max() > 0:
            edges = np.clip(edges / edges.max() * 255, 0, 255).astype(np.uint8)
        result = rgb.copy()
        edge_mask = edges > 30
        result[edge_mask] = np.clip(
            result[edge_mask].astype(np.int16) + 60, 0, 255).astype(np.uint8)
        return result

    @staticmethod
    def _motion_trail(rgb: np.ndarray,
                      postfx: PostProcessComponent) -> np.ndarray:
        if postfx.trail_buffer is None or postfx.trail_buffer.shape != rgb.shape:
            postfx.trail_buffer = rgb.astype(np.float32)
        else:
            postfx.trail_buffer = (postfx.trail_buffer * postfx.trail_decay
                                   + rgb.astype(np.float32) * (1 - postfx.trail_decay))
        return np.clip(postfx.trail_buffer, 0, 255).astype(np.uint8)

    @staticmethod
    def _vignette(rgb: np.ndarray) -> np.ndarray:
        h, w = rgb.shape[:2]
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2)
        mask = np.clip(1.0 - dist * 0.7, 0.3, 1.0)
        return np.clip(rgb.astype(np.float32) * mask[:, :, np.newaxis],
                       0, 255).astype(np.uint8)


class _TransitionManager:
    """内部用的配方切换过渡动画（对应 renderer.TransitionManager）"""

    def __init__(self, duration_frames: int = 30):
        self.active = False
        self.duration = duration_frames
        self.progress = 0
        self.old_frame = None

    def start(self, old_surface):
        self.active = True
        self.progress = 0
        self.old_frame = old_surface.copy()

    def update(self):
        if self.active:
            self.progress += 1
            if self.progress >= self.duration:
                self.active = False
                self.old_frame = None

    def is_active(self) -> bool:
        return self.active

    def apply(self, screen, new_surf, x, y):
        if not self.active or self.old_frame is None:
            return
        t = self.progress / self.duration
        old_copy = self.old_frame.copy()
        old_copy.set_alpha(int(255 * (1 - t)))
        new_copy = new_surf.copy()
        new_copy.set_alpha(int(255 * t))
        screen.blit(old_copy, (x, y))
        screen.blit(new_copy, (x, y))
        self.update()
