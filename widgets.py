"""
ECS Widgets — 纯 UI 组件，无框架依赖
======================================
从旧 renderer.py 提取，移除对 engine/CARenderer 的依赖。
仅依赖: pygame, numpy, pathlib, json, re
"""

import re
import json as _json
from pathlib import Path

import numpy as np
import pygame


# ================================================================
#  后处理特效器
# ================================================================
class PostProcess:
    """可组合的后处理特效链"""

    EFFECT_NAMES = ('none', 'bloom', 'edge', 'motion_trail', 'invert', 'vignette')

    @staticmethod
    def none(rgb):
        return rgb

    @staticmethod
    def bloom(rgb):
        from scipy.ndimage import gaussian_filter
        blurred = np.zeros_like(rgb, dtype=np.float32)
        for c in range(3):
            blurred[:, :, c] = gaussian_filter(rgb[:, :, c].astype(np.float32), sigma=1.2)
        return np.clip(rgb.astype(np.float32) + blurred * 0.4, 0, 255).astype(np.uint8)

    @staticmethod
    def edge(rgb):
        from scipy.ndimage import sobel
        v = rgb.astype(np.float32).mean(axis=2)
        edges = np.sqrt(sobel(v, axis=0) ** 2 + sobel(v, axis=1) ** 2)
        if edges.max() > 0:
            edges = np.clip(edges / edges.max() * 255, 0, 255).astype(np.uint8)
        result = rgb.copy()
        result[edges > 30] = np.clip(result[edges > 30].astype(np.int16) + 60, 0, 255).astype(np.uint8)
        return result

    @staticmethod
    def motion_trail(rgb, trail_buffer=None, trail_decay=0.85):
        if trail_buffer is None or trail_buffer.shape != rgb.shape:
            trail_buffer = rgb.astype(np.float32)
        else:
            trail_buffer = (trail_buffer * trail_decay +
                            rgb.astype(np.float32) * (1 - trail_decay))
        return np.clip(trail_buffer, 0, 255).astype(np.uint8), trail_buffer

    @staticmethod
    def invert(rgb):
        return 255 - rgb

    @staticmethod
    def vignette(rgb):
        h, w = rgb.shape[:2]
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2)
        mask = np.clip(1.0 - dist * 0.7, 0.3, 1.0)
        return np.clip(rgb.astype(np.float32) * mask[:, :, np.newaxis], 0, 255).astype(np.uint8)

    @staticmethod
    def apply(effect_name, rgb):
        func = getattr(PostProcess, effect_name, PostProcess.none)
        return func(rgb)


# ================================================================
#  HUD 渲染器
# ================================================================
class HUD:
    """屏幕抬头显示：FPS、步数、统计、通知"""

    def __init__(self, font, font_small, win_w, win_h):
        self.font = font
        self.font_small = font_small
        self.win_w = win_w
        self.win_h = win_h

    def draw(self, screen, info_text, fps_val, paused=False, auto_play=False,
             effect_name='none', notify=None, error=None):
        BAR_H = 22
        bar = pygame.Surface((self.win_w, BAR_H), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 140))
        screen.blit(bar, (0, 0))

        txt = self.font_small.render(info_text[:120], True, (200, 200, 220))
        screen.blit(txt, (6, 4))

        ft = self.font_small.render(f"FPS:{fps_val:.0f}", True, (140, 220, 140))
        fx = ft.get_width()
        screen.blit(ft, (self.win_w - fx - 8, 4))

        if auto_play:
            at = self.font_small.render("[AUTO]", True, (255, 200, 60))
            screen.blit(at, (self.win_w - fx - 100, 4))

        if paused:
            pt = self.font_small.render("[PAUSED]", True, (255, 160, 60))
            screen.blit(pt, (self.win_w // 2 - pt.get_width() // 2, 4))

        if effect_name != 'none':
            et = self.font_small.render(f"FX:{effect_name}", True, (160, 160, 255))
            screen.blit(et, (self.win_w // 2 - et.get_width() // 2, 4))

        if notify:
            n_text, n_color = notify
            nt = self.font.render(n_text[:80], True, n_color)
            tw, th = nt.get_size()
            noverlay = pygame.Surface((tw + 12, th + 6), pygame.SRCALPHA)
            noverlay.fill((0, 0, 0, 180))
            screen.blit(noverlay, (6, BAR_H + 4))
            screen.blit(nt, (12, BAR_H + 7))

        if error:
            lines = error.split('\n')[:3]
            eh = 18 * len(lines) + 6
            bar = pygame.Surface((self.win_w, eh), pygame.SRCALPHA)
            bar.fill((80, 10, 10, 200))
            screen.blit(bar, (0, self.win_h - eh))
            for i, line in enumerate(lines):
                et = self.font_small.render(line[:70], True, (255, 150, 150))
                screen.blit(et, (6, self.win_h - eh + 3 + i * 18))


# ================================================================
#  配方切换过渡动画
# ================================================================
class TransitionManager:
    """配方切换时的平滑过渡效果"""

    def __init__(self, duration_frames=30):
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

    def is_active(self):
        return self.active

    def apply(self, screen, new_surf, x, y):
        if not self.active or self.old_frame is None:
            return False
        t = self.progress / self.duration
        alpha_old = int(255 * (1 - t))
        alpha_new = int(255 * t)
        old_copy = self.old_frame.copy()
        old_copy.set_alpha(alpha_old)
        new_copy = new_surf.copy()
        new_copy.set_alpha(alpha_new)
        screen.blit(old_copy, (x, y))
        screen.blit(new_copy, (x, y))
        return True


# ================================================================
#  参数实时调节面板
# ================================================================
class ParamPanel:
    """侧边栏底部的参数滑块面板（鼠标拖拽调节）"""

    SLIDER_H = 18
    LABEL_H  = 14
    PAD      = 4
    MAX_PARAMS = 5

    COLORS = {
        'bg':       (22, 22, 30),
        'border':   (50, 50, 58),
        'label':    (140, 140, 160),
        'value':    (200, 200, 220),
        'track':    (38, 38, 48),
        'fill':     (60, 120, 200),
        'handle':   (100, 160, 240),
        'selected': (255, 200, 60),
        'header':   (100, 140, 180),
    }

    def __init__(self, sidebar_w, font_small, engine=None, config=None):
        self.sidebar_w = sidebar_w
        self.font = font_small
        self.engine = engine
        self.config = config or {}
        self.visible = False
        self.params = []
        self.selected = 0
        self.dragging = None
        self._extract_params()

    def _extract_params(self):
        self.params = []
        rule_expr = ''
        if self.engine is not None:
            rule_expr = self.engine.config.get('evolution', {}).get('rule', '')
        elif self.config:
            rule_expr = self.config.get('evolution', {}).get('rule', '')
        if not rule_expr:
            return

        pattern = re.compile(r'(?<![a-zA-Z_])(\d+\.\d+|\d+\.\d*|\.\d+)(?![a-zA-Z_\d])')
        matches = list(pattern.finditer(rule_expr))
        seen = {}
        for m in matches:
            val_str = m.group()
            val = float(val_str)
            if val_str not in seen:
                seen[val_str] = {'value': val, 'positions': [m.start()]}
            else:
                seen[val_str]['positions'].append(m.start())

        for i, (val_str, info) in enumerate(seen.items()):
            if i >= self.MAX_PARAMS:
                break
            v = info['value']
            if v == 0.0:
                lo, hi = -1.0, 1.0
            elif v < 0.01:
                lo, hi = -v * 5, v * 5
            elif v < 1.0:
                lo, hi = 0.0, max(1.0, v * 4)
            else:
                lo, hi = 0.0, v * 4
            self.params.append({
                'val_str':  val_str,
                'value':    v,
                'min':      round(lo, 6),
                'max':      round(hi, 6),
                'orig':     v,
            })

    def reset(self, engine=None, config=None):
        self.engine = engine
        self.config = config or {}
        self.selected = 0
        self.dragging = None
        self._extract_params()

    def panel_height(self):
        if not self.params:
            return 0
        return (self.LABEL_H + self.SLIDER_H + self.PAD) * len(self.params) + 26

    def draw(self, screen, win_h):
        if not self.visible or not self.params:
            return
        ph = self.panel_height()
        py = win_h - ph
        pw = self.sidebar_w - 2

        bg_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg_surf.fill((18, 18, 28, 215))
        screen.blit(bg_surf, (1, py))
        pygame.draw.line(screen, self.COLORS['border'], (1, py), (pw, py))

        h_txt = self.font.render("▲ 参数调节", True, self.COLORS['header'])
        screen.blit(h_txt, (6, py + 4))
        py += 20

        for i, p in enumerate(self.params):
            selected = (i == self.selected)
            label_color = self.COLORS['selected'] if selected else self.COLORS['label']
            lbl = self.font.render(f"p{i+1}={p['val_str']}", True, label_color)
            screen.blit(lbl, (6, py))
            val_txt = self.font.render(f"{p['value']:.4g}", True, self.COLORS['value'])
            screen.blit(val_txt, (pw - val_txt.get_width() - 4, py))
            py += self.LABEL_H

            track_rect = pygame.Rect(6, py + 3, pw - 12, self.SLIDER_H - 6)
            pygame.draw.rect(screen, self.COLORS['track'], track_rect, border_radius=3)

            lo, hi = p['min'], p['max']
            ratio = (p['value'] - lo) / (hi - lo) if hi > lo else 0.5
            ratio = max(0.0, min(1.0, ratio))
            fill_w = int(track_rect.w * ratio)
            if fill_w > 0:
                fill_color = self.COLORS['selected'] if selected else self.COLORS['fill']
                pygame.draw.rect(screen, fill_color,
                                 (track_rect.x, track_rect.y, fill_w, track_rect.h),
                                 border_radius=3)
            hx = track_rect.x + fill_w
            pygame.draw.circle(screen, self.COLORS['handle'], (hx, track_rect.centery), 5)
            py += self.SLIDER_H + self.PAD

    def handle_mouse_down(self, mx, my, win_h):
        if not self.visible or not self.params:
            return False
        ph = self.panel_height()
        py = win_h - ph + 20
        pw = self.sidebar_w - 2
        for i, p in enumerate(self.params):
            py += self.LABEL_H
            track_rect = pygame.Rect(6, py + 3, pw - 12, self.SLIDER_H - 6)
            if track_rect.collidepoint(mx, my):
                self.dragging = i
                self.selected = i
                self._set_from_mouse(mx, track_rect, p)
                return True
            py += self.SLIDER_H + self.PAD
        return False

    def handle_mouse_motion(self, mx, my, win_h):
        if self.dragging is None or not self.visible:
            return
        ph = self.panel_height()
        py = win_h - ph + 20
        pw = self.sidebar_w - 2
        for i, p in enumerate(self.params):
            py += self.LABEL_H
            track_rect = pygame.Rect(6, py + 3, pw - 12, self.SLIDER_H - 6)
            if i == self.dragging:
                self._set_from_mouse(mx, track_rect, p)
                break
            py += self.SLIDER_H + self.PAD

    def handle_mouse_up(self):
        self.dragging = None

    def _set_from_mouse(self, mx, track_rect, p):
        ratio = (mx - track_rect.x) / max(track_rect.w, 1)
        ratio = max(0.0, min(1.0, ratio))
        p['value'] = p['min'] + ratio * (p['max'] - p['min'])


# ================================================================
#  下拉分类菜单
# ================================================================
class CategoryDropdown:
    """分类下拉菜单（点击标头展开/收起选项列表）"""

    C_BG      = (30, 30, 38)
    C_BORDER  = (60, 60, 70)
    C_HEADER  = (50, 110, 190)
    C_ITEM    = (40, 40, 52)
    C_ITEM_HV = (60, 130, 220)
    C_TEXT    = (200, 200, 215)
    C_SEL     = (255, 220, 80)
    ITEM_H    = 20

    def __init__(self, font, x, y, w, categories, current='全部', counts=None):
        self.font = font
        self.x = x
        self.y = y
        self.w = w
        self.categories = ['全部'] + list(categories)
        self.counts = counts or {}
        self.current = current if current in self.categories else '全部'
        self.open = False
        self._hover_idx = -1
        self.header_h = 22

    def draw(self, screen):
        hdr_rect = pygame.Rect(self.x, self.y, self.w, self.header_h)
        pygame.draw.rect(screen, self.C_HEADER, hdr_rect, border_radius=4)
        label = self.current if len(self.current) <= 11 else self.current[:10] + '…'
        arrow = '▲' if self.open else '▼'
        txt = self.font.render(label, True, (240, 240, 255))
        screen.blit(txt, (self.x + 6, self.y + 4))
        arr = self.font.render(arrow, True, (200, 200, 220))
        screen.blit(arr, (self.x + self.w - arr.get_width() - 6, self.y + 4))

        if not self.open:
            return

        list_h = len(self.categories) * self.ITEM_H
        list_rect = pygame.Rect(self.x, self.y + self.header_h, self.w, list_h)
        pygame.draw.rect(screen, self.C_BG, list_rect)
        pygame.draw.rect(screen, self.C_BORDER, list_rect, 1)

        for i, cat in enumerate(self.categories):
            iy = self.y + self.header_h + i * self.ITEM_H
            item_rect = pygame.Rect(self.x, iy, self.w, self.ITEM_H)
            if i == self._hover_idx:
                pygame.draw.rect(screen, self.C_ITEM_HV, item_rect)
            elif cat == self.current:
                pygame.draw.rect(screen, (50, 90, 160), item_rect)
            c_name = cat if len(cat) <= 13 else cat[:12] + '…'
            color = self.C_SEL if cat == self.current else self.C_TEXT
            t = self.font.render(c_name, True, color)
            screen.blit(t, (self.x + 8, iy + 3))
            cnt = self.counts.get(cat, 0)
            if cnt > 0:
                cnt_t = self.font.render(str(cnt), True, (90, 100, 120))
                screen.blit(cnt_t, (self.x + self.w - cnt_t.get_width() - 8, iy + 3))

    def handle_mouse_down(self, mx, my):
        hdr = pygame.Rect(self.x, self.y, self.w, self.header_h)
        if hdr.collidepoint(mx, my):
            self.open = not self.open
            return True, None

        if not self.open:
            return False, None

        for i, cat in enumerate(self.categories):
            iy = self.y + self.header_h + i * self.ITEM_H
            if pygame.Rect(self.x, iy, self.w, self.ITEM_H).collidepoint(mx, my):
                self.current = cat
                self.open = False
                return True, cat

        self.open = False
        return False, None

    def handle_mouse_move(self, mx, my):
        if not self.open:
            return
        self._hover_idx = -1
        for i, cat in enumerate(self.categories):
            iy = self.y + self.header_h + i * self.ITEM_H
            if pygame.Rect(self.x, iy, self.w, self.ITEM_H).collidepoint(mx, my):
                self._hover_idx = i
                break


# ================================================================
#  搜索框
# ================================================================
class SearchBox:
    """单行搜索输入框（鼠标点击激活，接受文字输入）"""

    C_BG      = (24, 24, 32)
    C_ACTIVE  = (40, 110, 200)
    C_BORDER  = (55, 55, 65)
    C_TEXT    = (210, 210, 225)
    C_HINT    = (90, 90, 105)
    C_CURSOR  = (160, 200, 255)
    H = 22

    def __init__(self, font, x, y, w, hint='搜索…'):
        self.font = font
        self.x = x
        self.y = y
        self.w = w
        self.hint = hint
        self.text = ''
        self.active = False
        self._cursor_tick = 0

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.H)

    def draw(self, screen):
        r = self.rect()
        border_col = self.C_ACTIVE if self.active else self.C_BORDER
        pygame.draw.rect(screen, self.C_BG, r, border_radius=4)
        pygame.draw.rect(screen, border_col, r, 1, border_radius=4)

        if self.text:
            t = self.font.render(self.text, True, self.C_TEXT)
            max_w = self.w - 10
            if t.get_width() > max_w:
                clip_surf = pygame.Surface((max_w, self.H - 4), pygame.SRCALPHA)
                clip_surf.blit(t, (max_w - t.get_width(), 0))
                screen.blit(clip_surf, (self.x + 4, self.y + 4))
            else:
                screen.blit(t, (self.x + 4, self.y + 4))
        elif not self.active:
            hint_t = self.font.render(self.hint, True, self.C_HINT)
            screen.blit(hint_t, (self.x + 4, self.y + 4))

        if self.active:
            self._cursor_tick += 1
            if (self._cursor_tick // 30) % 2 == 0:
                tx = self.font.render(self.text, True, self.C_TEXT)
                cx = self.x + 4 + min(tx.get_width(), self.w - 10)
                pygame.draw.line(screen, self.C_CURSOR, (cx, self.y + 4), (cx, self.y + self.H - 4), 1)

    def handle_mouse_down(self, mx, my):
        self.active = self.rect().collidepoint(mx, my)
        return self.active

    def handle_key(self, event):
        if not self.active:
            return False
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return True
        elif event.key == pygame.K_ESCAPE:
            self.text = ''
            self.active = False
            return True
        elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN):
            self.active = False
            return False
        elif event.unicode and event.unicode.isprintable():
            self.text += event.unicode
            return True
        return False

    def clear(self):
        self.text = ''
        self.active = False


# ================================================================
#  选择确认面板
# ================================================================
class SelectionPanel:
    """底部确认面板：显示选中配方信息，点击渲染按钮才切换。"""

    H = 80
    C_BG     = (20, 20, 28)
    C_BORDER = (60, 110, 200)
    C_BTN    = (40, 130, 60)
    C_BTN_HV = (60, 180, 80)
    C_BTN_TXT= (220, 255, 220)
    C_CANCEL = (80, 40, 40)
    C_CANCEL_HV = (130, 60, 60)
    C_TITLE  = (200, 210, 255)
    C_META   = (130, 140, 160)
    BTN_W    = 70
    BTN_H    = 26

    def __init__(self, font, font_small, sidebar_w):
        self.font = font
        self.font_small = font_small
        self.sidebar_w = sidebar_w
        self.visible = False
        self.pending_name = None
        self.pending_path = None
        self._desc_cache = ''
        self._btn_render_hover = False
        self._btn_cancel_hover = False

    def show(self, name, path):
        self.pending_name = name
        self.pending_path = path
        self.visible = True
        self._desc_cache = self._read_desc(path)

    def hide(self):
        self.visible = False
        self.pending_name = None
        self.pending_path = None
        self._desc_cache = ''

    def panel_rect(self, win_h):
        return pygame.Rect(0, win_h - self.H, self.sidebar_w, self.H)

    def draw(self, screen, win_h):
        if not self.visible or not self.pending_name:
            return

        pr = self.panel_rect(win_h)
        surf = pygame.Surface((pr.w, pr.h), pygame.SRCALPHA)
        surf.fill((20, 20, 28, 230))
        screen.blit(surf, pr.topleft)
        pygame.draw.rect(screen, self.C_BORDER, pr, 1)

        name = self.pending_name
        display = name if len(name) <= 17 else name[:16] + '…'
        t = self.font_small.render(display, True, self.C_TITLE)
        screen.blit(t, (pr.x + 6, pr.y + 5))

        desc = self._desc_cache
        if desc:
            d = self.font_small.render(desc[:28], True, self.C_META)
            screen.blit(d, (pr.x + 6, pr.y + 20))

        bx = pr.x + 6
        by = pr.y + pr.h - self.BTN_H - 8
        btn_r = pygame.Rect(bx, by, self.BTN_W, self.BTN_H)
        btn_c = self.C_BTN_HV if self._btn_render_hover else self.C_BTN
        pygame.draw.rect(screen, btn_c, btn_r, border_radius=4)
        bt = self.font.render("▶ 渲染", True, self.C_BTN_TXT)
        screen.blit(bt, (bx + (self.BTN_W - bt.get_width()) // 2, by + 4))

        cx = bx + self.BTN_W + 8
        cancel_r = pygame.Rect(cx, by, self.BTN_W - 10, self.BTN_H)
        cc = self.C_CANCEL_HV if self._btn_cancel_hover else self.C_CANCEL
        pygame.draw.rect(screen, cc, cancel_r, border_radius=4)
        ct = self.font.render("取消", True, (220, 180, 180))
        screen.blit(ct, (cx + (cancel_r.w - ct.get_width()) // 2, by + 4))

        self._btn_render_rect = btn_r
        self._btn_cancel_rect = cancel_r

    def _read_desc(self, path):
        if not path:
            return ''
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = _json.load(f)
            return data.get('description', '')[:30]
        except Exception:
            return ''

    def handle_mouse_down(self, mx, my, win_h):
        if not self.visible:
            return None
        if not self.panel_rect(win_h).collidepoint(mx, my):
            return None
        if hasattr(self, '_btn_render_rect') and self._btn_render_rect.collidepoint(mx, my):
            return 'render'
        if hasattr(self, '_btn_cancel_rect') and self._btn_cancel_rect.collidepoint(mx, my):
            return 'cancel'
        return None

    def handle_mouse_move(self, mx, my, win_h):
        if not self.visible:
            return
        self._btn_render_hover = hasattr(self, '_btn_render_rect') and self._btn_render_rect.collidepoint(mx, my)
        self._btn_cancel_hover = hasattr(self, '_btn_cancel_rect') and self._btn_cancel_rect.collidepoint(mx, my)


# ================================================================
#  二级预览面板（占用主内容区）
# ================================================================
class RecipePreview:
    """点击配方后，在主内容区显示配方详情 + 渲染确认（二级界面）。

    不再使用侧边栏底部的小条，而是整个右侧区域切换为预览模式。
    """

    C_BG        = (16, 18, 26)
    C_CARD      = (28, 30, 42)
    C_CARD_BRD  = (60, 120, 200)
    C_TITLE     = (220, 225, 255)
    C_INFO      = (155, 165, 185)
    C_SEP       = (48, 52, 68)
    C_BTN_R     = (42, 145, 60)
    C_BTN_R_HV  = (60, 195, 80)
    C_BTN_R_TXT = (225, 255, 225)
    C_BTN_C     = (105, 38, 38)
    C_BTN_C_HV  = (170, 55, 55)
    C_BTN_C_TXT = (255, 200, 200)

    def __init__(self, font, font_small):
        self.font = font
        self.font_small = font_small
        self.visible = False
        self.name = ''
        self.path = ''
        self._desc = ''
        self._grid_w = 0
        self._grid_h = 0
        self._btn_render_hover = False
        self._btn_cancel_hover = False
        self._btn_render_rect = None
        self._btn_cancel_rect = None

    def show(self, name, path):
        self.name = name
        self.path = path
        self.visible = True
        # 读取配方元数据（不加载完整配方）
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = _json.load(f)
            self._desc = data.get('description', '')
            g = data.get('grid', {})
            self._grid_w = g.get('width', 0)
            self._grid_h = g.get('height', 0)
        except Exception:
            self._desc = ''
            self._grid_w = 0
            self._grid_h = 0

    def hide(self):
        self.visible = False
        self.name = ''
        self.path = ''

    def draw(self, screen, area_rect):
        """area_rect: (x, y, w, h) — 主内容区"""
        if not self.visible:
            return

        ax, ay, aw, ah = area_rect

        # 半透明遮罩
        overlay = pygame.Surface((aw, ah), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 215))
        screen.blit(overlay, (ax, ay))

        # 卡片尺寸
        card_w = min(aw - 80, 420)
        card_h = min(ah - 80, 300)
        cx = ax + (aw - card_w) // 2
        cy = ay + (ah - card_h) // 2

        # 卡片背景
        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((28, 30, 42, 245))
        screen.blit(card, (cx, cy))
        pygame.draw.rect(screen, self.C_CARD_BRD,
                         (cx, cy, card_w, card_h), 2, border_radius=8)

        # 标题
        tname = self.name if len(self.name) <= 22 else self.name[:21] + '…'
        title = self.font.render(tname, True, self.C_TITLE)
        screen.blit(title, (cx + (card_w - title.get_width()) // 2, cy + 16))

        # 分隔线
        sep_y = cy + 42
        pygame.draw.line(screen, self.C_SEP,
                         (cx + 30, sep_y), (cx + card_w - 30, sep_y))

        # 信息行
        info_y = sep_y + 14
        if self._desc:
            d = self.font_small.render(f"描述: {self._desc[:44]}", True, self.C_INFO)
            screen.blit(d, (cx + 30, info_y))
            info_y += 20

        sz = self.font_small.render(f"网格尺寸: {self._grid_w} × {self._grid_h}",
                                     True, self.C_INFO)
        screen.blit(sz, (cx + 30, info_y))
        info_y += 24

        tip = self.font_small.render("点击「开始渲染」将加载配方并启动模拟",
                                     True, (100, 110, 130))
        screen.blit(tip, (cx + 30, info_y))

        # 按钮区
        BTN_W, BTN_H, GAP = 120, 34, 24
        btn_y = cy + card_h - BTN_H - 24
        total_w = BTN_W * 2 + GAP
        bx = cx + (card_w - total_w) // 2

        # 「开始渲染」按钮
        br = pygame.Rect(bx, btn_y, BTN_W, BTN_H)
        bc = self.C_BTN_R_HV if self._btn_render_hover else self.C_BTN_R
        pygame.draw.rect(screen, bc, br, border_radius=6)
        bt = self.font.render("开始渲染", True, self.C_BTN_R_TXT)
        screen.blit(bt, (bx + (BTN_W - bt.get_width()) // 2, btn_y + 7))
        self._btn_render_rect = br

        # 「返回」按钮
        cx2 = bx + BTN_W + GAP
        cr = pygame.Rect(cx2, btn_y, BTN_W, BTN_H)
        cc = self.C_BTN_C_HV if self._btn_cancel_hover else self.C_BTN_C
        pygame.draw.rect(screen, cc, cr, border_radius=6)
        ct = self.font.render("返回", True, self.C_BTN_C_TXT)
        screen.blit(ct, (cx2 + (BTN_W - ct.get_width()) // 2, btn_y + 7))
        self._btn_cancel_rect = cr

    def handle_mouse_down(self, mx, my):
        if not self.visible:
            return None
        if self._btn_render_rect and self._btn_render_rect.collidepoint(mx, my):
            return 'render'
        if self._btn_cancel_rect and self._btn_cancel_rect.collidepoint(mx, my):
            return 'cancel'
        return None

    def handle_mouse_move(self, mx, my):
        if not self.visible:
            return
        self._btn_render_hover = (self._btn_render_rect is not None
                                  and self._btn_render_rect.collidepoint(mx, my))
        self._btn_cancel_hover = (self._btn_cancel_rect is not None
                                  and self._btn_cancel_rect.collidepoint(mx, my))
