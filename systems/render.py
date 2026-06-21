"""
RenderSystem — Pygame 帧渲染系统（SDL2 硬件加速版）
=============================================
源自：renderer.py 主循环中的 Pygame Surface 绘制逻辑
    - surfarray.blit_array()  → _draw_sw()
    - pygame.Renderer.copy()   → _draw_hw()  [硬件加速]
    - PostProcess.apply()       → _apply_postfx()
    - TransitionManager         → 保留为内部 helper

加速策略：
    1. 用 pygame.Renderer + Texture 代替 Surface blit（硬件缩放）
    2. Texture.update() 直接从 numpy 数组上传 GPU
    3. 后处理已使用分离高斯模糊（O(n·σ)）

System 接口：
    system = RenderSystem()
    system.set_screen(screen_or_renderer, ca_rect)
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
    """Pygame 帧渲染系统（自动选择硬件/软件路径）。

    硬件加速路径（优先）：
        - 当 set_screen() 收到 pygame.Renderer 对象时激活
        - 使用 Texture.update() + renderer.copy()
        - 缩放由 GPU 完成，无软件缩放瓶颈

    软件回退路径：
        - 当收到 pygame.Surface 时激活
        - 使用 Surface blit_array + pygame.transform.scale()
        - 兼容不支持 RENDERER 的环境
    """

    def __init__(self):
        self._screen_or_renderer = None   # pygame.Surface | pygame.Renderer
        self._is_renderer = False
        self.ca_rect = (0, 0, 640, 480)  # (x, y, w, h)
        self._transition = _TransitionManager()

        # 软件路径缓存
        self._surf_wh = None      # pygame.Surface (w,h,3)

        # 硬件路径缓存
        self._texture = None       # pygame.Texture
        self._upload_surf = None  # pygame.Surface（用于 Texture.update()）

    # ── 公开接口 ─────────────────────────────────────────────────────

    def set_screen(self, screen_or_renderer, ca_rect: tuple):
        """设置画布（自动检测 Renderer / Surface）。

        参数：
            screen_or_renderer: pygame.Surface 或 pygame.Renderer
            ca_rect: (x, y, w, h) CA 画面在窗口中的位置和大小
        """
        self._screen_or_renderer = screen_or_renderer
        self.ca_rect = ca_rect
        self._is_renderer = (
            _PYGAME_AVAILABLE
            and hasattr(pygame, 'Renderer')
            and isinstance(screen_or_renderer, pygame.Renderer)
        )
        # 清空缓存（尺寸可能变了）
        self._surf_wh = None
        self._texture = None
        self._upload_surf = None

    def draw(self, entity: RecipeEntity):
        """渲染一帧（自动选择硬件/软件路径）。"""
        if not _PYGAME_AVAILABLE or self._screen_or_renderer is None:
            return
        grid = entity.grid
        if grid.rgb_wh is None:
            return

        # 后处理：在 grid.rgb_hw 上原地操作
        if entity.postfx.active_effect != 'none':
            self._apply_postfx(grid.rgb_hw, entity.postfx)

        # 使用 rgb_wh (w,h,3) 格式，与 pygame Surface/blit_array 一致
        gw, gh = grid.rgb_wh.shape[:2]
        x, y, dw, dh = self.ca_rect

        if self._is_renderer:
            self._draw_hw(grid.rgb_wh, gw, gh, dw, dh, x, y)
        else:
            self._draw_sw(grid.rgb_wh, gw, gh, dw, dh, x, y)

        # 过渡动画覆盖层
        if self._transition.is_active():
            self._transition.apply_overlay(
                self._screen_or_renderer, x, y, dw, dh)

    # ── 硬件加速路径（pygame.Renderer）────────────────────────────

    def _draw_hw(self, rgb_wh, gw, gh, dw, dh, x, y):
        """SDL2 Renderer 路径：Texture.update() + renderer.copy()。"""
        renderer = self._screen_or_renderer  # type: pygame.Renderer

        # rgb_wh 已是 (w,h,3) uint8 数组

        # 创建或更新 Upload Surface
        if (self._upload_surf is None
                or self._upload_surf.get_size() != (gw, gh)):
            self._upload_surf = pygame.Surface((gw, gh))
        pygame.surfarray.blit_array(self._upload_surf, rgb_wh)

        # 创建或更新 Texture
        if (self._texture is None
                or self._texture.width != gw
                or self._texture.height != gh):
            self._texture = pygame.Texture(renderer, self._upload_surf)

        self._texture.update(self._upload_surf)

        # 硬件缩放 + 绘制
        dst_rect = pygame.Rect(x, y, dw, dh)
        renderer.copy(self._texture, dstrect=dst_rect)

    # ── 软件渲染路径（兼容回退）──────────────────────────────────

    def _draw_sw(self, rgb_wh, gw, gh, dw, dh, x, y):
        """Surface blit 路径（软件缩放）。"""
        screen = self._screen_or_renderer  # type: pygame.Surface

        if (self._surf_wh is None
                or self._surf_wh.get_size() != (gw, gh)):
            self._surf_wh = pygame.Surface((gw, gh))

        # rgb_wh 已是 (w,h,3) 格式，与 Surface (w,h) 匹配
        pygame.surfarray.blit_array(self._surf_wh, rgb_wh)

        if (dw, dh) == (gw, gh):
            screen.blit(self._surf_wh, (x, y))
        else:
            # 软件缩放：smoothscale 质量优于 scale（双线性插值）
            scaled = pygame.transform.smoothscale(self._surf_wh, (dw, dh))
            screen.blit(scaled, (x, y))

    # ── 过渡动画 ───────────────────────────────────────────────────

    def start_transition(self):
        """配方切换时触发淡入过渡。"""
        if self._surf_wh is not None:
            self._transition.start(self._surf_wh)

    def update_transition(self):
        """更新过渡动画帧（在主循环中每帧调用）。"""
        self._transition.update()

    def apply_transition(self, screen, surf, x, y):
        """兼容旧接口：在屏幕上应用过渡效果。

        新架构下，过渡效果直接在 draw() 中处理，
        此方法保留以兼容 world.py 中的调用。
        """
        if not self._transition.is_active():
            return False
        # 旧逻辑：用 Surface blit 做交叉淡入
        if hasattr(surf, 'get_width'):
            w, h = surf.get_width(), surf.get_height()
        else:
            w, h = self.ca_rect[2], self.ca_rect[3]
        self._transition.apply_overlay(screen, x, y, w, h)
        return True

    # ── 后处理（对应 renderer.PostProcess）───────────────────────

    def _apply_postfx(self, rgb: np.ndarray,
                      postfx: PostProcessComponent) -> np.ndarray:
        """应用后处理特效，返回处理后的 (h,w,3) uint8 数组。"""
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

    # ── 后处理静态方法 ───────────────────────────────────────────

    @staticmethod
    def _bloom(rgb: np.ndarray) -> np.ndarray:
        """分离高斯模糊（O(n·σ)），避免 gaussian_filter 的 O(n·σ²)。"""
        import numpy as _np
        from scipy.ndimage import convolve1d
        sigma = 1.2
        radius = int(3 * sigma)
        x = _np.arange(-radius, radius + 1, dtype=_np.float32)
        kernel = _np.exp(-0.5 * (x / sigma) ** 2)
        kernel /= kernel.sum()
        blurred = _np.zeros_like(rgb, dtype=_np.float32)
        for c in range(3):
            h = convolve1d(rgb[:, :, c].astype(_np.float32), kernel, mode='nearest')
            blurred[:, :, c] = convolve1d(h, kernel, axis=0, mode='nearest')
        return _np.clip(rgb.astype(_np.float32) + blurred * 0.4, 0, 255).astype(_np.uint8)

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
    """配方切换过渡动画（SDL2 兼容版）。"""

    def __init__(self, duration_frames: int = 30):
        self.active = False
        self.duration = duration_frames
        self.progress = 0
        self.old_frame_surf = None   # pygame.Surface（旧帧快照）

    def start(self, old_surface: pygame.Surface):
        """开始过渡动画（传入旧帧 Surface）。"""
        self.active = True
        self.progress = 0
        self.old_frame_surf = old_surface.copy()

    def update(self):
        if self.active:
            self.progress += 1
            if self.progress >= self.duration:
                self.active = False
                self.old_frame_surf = None

    def is_active(self) -> bool:
        return self.active

    def apply_overlay(self, screen_or_renderer, x, y, w, h):
        """将过渡效果绘制到屏幕（兼容 Surface / Renderer）。"""
        if not self.active or self.old_frame_surf is None:
            return
        t = self.progress / self.duration
        old_copy = self.old_frame_surf.copy()
        old_copy.set_alpha(int(255 * (1 - t)))
        new_surf = pygame.Surface((w, h))
        new_surf.set_alpha(int(255 * t))

        if (hasattr(pygame, 'Renderer')
                and isinstance(screen_or_renderer, pygame.Renderer)):
            # Renderer 路径：先绘制到临时 Surface，再转为 Texture 绘制
            renderer = screen_or_renderer
            tmp = pygame.Surface((w, h))
            tmp.blit(old_copy, (0, 0))
            tex_old = pygame.Texture(renderer, tmp)
            renderer.copy(tex_old, dstrect=(x, y, w, h))
        else:
            # Surface 路径：直接 blit
            screen_or_renderer.blit(old_copy, (x, y))
            screen_or_renderer.blit(new_surf, (x, y))
        self.update()
