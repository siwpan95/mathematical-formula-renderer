"""
CAWorld — ECS 世界调度器（真正使用 ECS 系统的主循环）
=====================================================

架构：
    main.pyw → CAWorld.run()            # 入口
                 ├── EvolutionSystem    # 网格演化
                 ├── ColorSystem        # 颜色映射
                 ├── RenderSystem       # Pygame 帧绘制
                 └── UISystem           # 事件/UI（调用 renderer.py 的 Widget）

数据流（每帧）：
    事件 → UISystem（分发到各类 Widget，更新 World 状态）
    EvolutionSystem.update(entity) → 更新 grid.data
    ColorSystem.update(entity) → 更新 grid.rgb_hw
    RenderSystem.draw(entity) → blit 到 screen
    UISystem.draw() → 覆盖绘制工具栏/侧边栏/HUD
    pygame.display.flip()
"""

from __future__ import annotations
import time as _time
import json as _json
from pathlib import Path
from typing import Optional

import numpy as np

from entities.recipe import RecipeEntity
from entities.registry import TemplateRegistry
from systems.evolution import EvolutionSystem
from systems.colormap import ColorSystem, COLOR_PRESETS
from systems.render import RenderSystem
from systems.ui import UISystem


class CAWorld:
    """CA ECS 世界 — 持有 Entity、Systems、Pygame 资源，驱动主循环。

    使用方式：
        world = CAWorld()
        world.run('effects/')   # 自动完成：扫描 → 加载 → 主循环
    """

    def __init__(self):
        # ── 注册表 ──
        self.registry = TemplateRegistry()

        # ── 活跃 Entity ──
        self.entity: Optional[RecipeEntity] = None

        # ── Systems ──
        self.evolution_sys = EvolutionSystem()
        self.color_sys = ColorSystem()
        self.render_sys = RenderSystem()
        self.ui_sys = UISystem(self)

        # ── 运行时状态 ──
        self.paused = False
        self.auto_play = False
        self.auto_interval = 600       # 自动播放切换帧数
        self._auto_counter = 0
        self._effect_list: list[str] = []
        self._effect_index = 0
        self.running = False

        # ── Pygame 资源（延迟初始化）──
        self.screen = None
        self.clock = None
        self.font = None
        self.font_small = None
        self.script_dir = None

        # ── Notification ──
        self.notify_msg = None
        self.notify_timer = 0
        self.error_msg = None
        self.error_timer = 0

        # ── 当前颜色预设 ──
        self.current_preset = 'default'

        # ── 渲染缓存（避免每帧分配 Surface）──
        self._ca_surf = None       # 原生分辨率 Surface
        self._ca_scaled = None     # 缩放后 Surface

    # ================================================================
    #  入口
    # ================================================================

    def run(self, effects_dir: str | Path):
        """启动 ECS 主循环（完整流程：加载 → 初始化 → 循环）"""
        effects_dir = Path(effects_dir)
        self.script_dir = effects_dir.parent

        # 1. 扫描 effects/
        self._load_effects(effects_dir)
        if not self._effect_list:
            print("[World] 未找到任何配方，退出")
            return

        # 2. 初始化 Pygame
        self._init_pygame()

        # 3. 主循环（配方由用户选择后渲染，启动时不自动加载）
        try:
            self._run_loop()
        except KeyboardInterrupt:
            pass

        # 5. 清理
        self._quit()

    # ================================================================
    #  配方加载
    # ================================================================

    def _load_effects(self, effects_dir: Path):
        """带加载界面的 effects 扫描"""
        import pygame
        pygame.init()
        LOAD_W, LOAD_H = 480, 220
        load_screen = pygame.display.set_mode((LOAD_W, LOAD_H))
        pygame.display.set_caption("正在加载...")

        fp = self.script_dir / 'resources' / 'NotoSansSC-VF.ttf'
        if not fp.exists():
            fp = self.script_dir / 'resources' / 'simhei.ttf'
        if fp.exists():
            title_font = pygame.font.Font(str(fp), 22)
            info_font = pygame.font.Font(str(fp), 14)
            small_font = pygame.font.Font(str(fp), 11)
        else:
            title_font = pygame.font.Font(None, 24)
            info_font = pygame.font.Font(None, 16)
            small_font = pygame.font.Font(None, 12)

        progress = [0.0]
        detail_text = [""]

        def _draw(pct, status, detail, error=None):
            load_screen.fill((18, 18, 24))
            t = title_font.render("CA 渲染引擎 (ECS)", True, (210, 210, 230))
            load_screen.blit(t, (LOAD_W // 2 - t.get_width() // 2, 22))
            s = info_font.render(status, True, (160, 160, 185))
            load_screen.blit(s, (LOAD_W // 2 - s.get_width() // 2, 56))
            bx, by, bw, bh = 44, 92, LOAD_W - 88, 20
            pygame.draw.rect(load_screen, (38, 38, 48), (bx, by, bw, bh), border_radius=5)
            if pct > 0:
                fw = int(bw * pct)
                pygame.draw.rect(load_screen,
                                 (int(40 + 170 * pct), int(100 + 100 * pct), int(190 + 45 * pct)),
                                 (bx, by, fw, bh), border_radius=5)
            pct_t = small_font.render(f"{int(pct * 100)}%", True, (225, 225, 240))
            load_screen.blit(pct_t, (bx + bw // 2 - pct_t.get_width() // 2, by + 2))
            if detail:
                d = small_font.render(detail[:52], True, (120, 120, 140))
                load_screen.blit(d, (LOAD_W // 2 - d.get_width() // 2, 126))
            if error:
                e = small_font.render(error[:58], True, (255, 120, 120))
                load_screen.blit(e, (LOAD_W // 2 - e.get_width() // 2, 192))
            pygame.display.flip()

        def _progress(i, total, fname):
            progress[0] = 0.12 + (i / total) * 0.58
            detail_text[0] = fname
            _draw(progress[0], f"加载配方文件 ({i}/{total})", detail_text[0])
            for _ in pygame.event.get():
                pass

        _draw(0.0, "正在扫描配方目录", "")
        pygame.time.wait(120)

        try:
            self.registry.load_effects(effects_dir, progress_cb=_progress)
        except Exception as e:
            _draw(0, "加载失败", "", str(e))
            pygame.time.wait(2500)
            return

        self._effect_list = self.registry.effect_names
        if not self._effect_list:
            _draw(0, "加载失败", "", "未找到任何 .json 配方文件")
            pygame.time.wait(2500)
            return

        # 编译首个配方
        _draw(0.78, "编译配方...", "")
        for _ in pygame.event.get():
            pass

        _draw(1.0, "初始化完成",
              f"已加载 {len(self._effect_list)} 个配方，即将启动...")
        pygame.time.wait(500)

    def load_recipe_by_name(self, name: str) -> bool:
        """按名称切换配方"""
        path = self.registry.get_effect_path(name)
        if path is None:
            return False
        return self._load_recipe(str(path))

    def load_recipe_by_index(self, idx: int) -> bool:
        """按索引切换配方"""
        if not self._effect_list:
            return False
        idx = idx % len(self._effect_list)
        self._effect_index = idx
        return self.load_recipe_by_name(self._effect_list[idx])

    def _load_recipe(self, path: str) -> bool:
        """内部加载配方，触发 ECS 初始化"""
        try:
            self.render_sys.start_transition()
            self.entity = RecipeEntity.from_json(path)
            # ECS 初始化（编译公式 + 建网格）
            self.evolution_sys._initialize(self.entity)
            self._apply_current_preset()
            return True
        except Exception as e:
            self.error_msg = f"配方加载失败\n{str(e)[:200]}"
            self.error_timer = 300
            return False

    def reload_recipe(self):
        """重载当前配方"""
        if self.entity is None:
            return
        path = self.registry.get_effect_path(self.entity.entity_id)
        if path:
            self._load_recipe(str(path))

    def reset(self):
        """重置当前网格"""
        if self.entity:
            self.evolution_sys.reset(self.entity)

    # ================================================================
    #  Pygame 初始化
    # ================================================================

    def _init_pygame(self):
        import pygame
        pygame.init()

        SIDEBAR_W = 220
        TOOLBAR_H = 28
        w = self.entity.grid.w if self.entity else 256
        h = self.entity.grid.h if self.entity else 192
        scale = max(1, 800 // max(w, h))

        self.win_w = SIDEBAR_W + w * scale
        self.win_h = TOOLBAR_H + h * scale
        self.SIDEBAR_W = SIDEBAR_W
        self.TOOLBAR_H = TOOLBAR_H
        self.scale_level = scale
        self.fullscreen = False

        # SDL2 硬件加速：尝试使用 RENDERER 标志（仅 pygame-ce 支持）
        self._renderer_flag = getattr(pygame, 'RENDERER', 0)
        self.screen = pygame.display.set_mode(
            (self.win_w, self.win_h),
            pygame.RESIZABLE | self._renderer_flag
        )
        # 获取 Renderer 对象（硬件加速渲染上下文）- 仅 pygame-ce
        _get_renderer = getattr(pygame.display, 'get_renderer', None)
        self.renderer = _get_renderer() if _get_renderer else None

        self.clock = pygame.time.Clock()

        name = self._fmt_name()
        pygame.display.set_caption(f"CA Render — {name}")

        fp = self.script_dir / 'resources' / 'NotoSansSC-VF.ttf'
        if not fp.exists():
            fp = self.script_dir / 'resources' / 'simhei.ttf'
        if fp.exists():
            self.font = pygame.font.Font(str(fp), 13)
            self.font_small = pygame.font.Font(str(fp), 11)
        else:
            self.font = pygame.font.Font(None, 13)
            self.font_small = pygame.font.Font(None, 11)

        # 设置 RenderSystem 的画布（传 renderer 或 screen）
        self.render_sys.set_screen(
            self.renderer if self.renderer is not None else self.screen,
            (SIDEBAR_W, TOOLBAR_H, w * scale, h * scale)
        )

    # ================================================================
    #  主循环（ECS 管道）
    # ================================================================

    def _run_loop(self):
        """ECS 主循环：依次调用各 System"""
        import pygame
        from ui.widgets import (CategoryDropdown, SearchBox,
                                  ParamPanel, HUD, PostProcess, RecipePreview)
        from ui.thumbnail_grid import ThumbnailGrid
        import re as _re

        sw = self.SIDEBAR_W
        th = self.TOOLBAR_H
        HUD_BAR_H = 22   # HUD 信息条高度

        # ── 构建 UI 组件 ──
        cat_list = list(self.registry.categories.keys())
        total_count = len(self._effect_list)
        cat_counts = {'全部': total_count}
        for cn, effect_names in self.registry.categories.items():
            cat_counts[cn] = len(effect_names)

        sidebar_top = th + HUD_BAR_H + 4   # 工具栏 + HUD 条 + 间距

        # 顺序：搜索框 → 下拉菜单 → 配方列表
        search_box = SearchBox(
            self.font_small, 4, sidebar_top, sw - 8, hint='搜索配方…')
        dropdown = CategoryDropdown(
            self.font_small, 4, sidebar_top + SearchBox.H + 4,
            sw - 8, cat_list, counts=cat_counts)
        preview = RecipePreview(self.font, self.font_small)
        param_panel = ParamPanel.__new__(ParamPanel)  # 延迟初始化

        hud = HUD(self.font, self.font_small, self.win_w, self.win_h)

        # ── 缩略图网格浏览器 ──
        grid = ThumbnailGrid(
            self.font, self.font_small,
            sw, th, self.win_w - sw, self.win_h - th
        )
        grid.set_recipes(self._effect_list, self.registry)
        grid.set_thumb_dir(self.script_dir / 'effects' / 'thumbs')
        grid.apply_filter('', '全部')

        # 工具栏
        TOOLBAR_BTNS = [
            ('pause', '| |', '暂停/继续'),
            ('reset', 'Rst', '重置网格'),
            ('screenshot', 'Shot', '截图'),
            ('effect', 'FX', '切换特效'),
            ('preset', 'Col', '切换颜色'),
            ('auto', 'Auto', '自动播放'),
        ]

        # ── UI 状态 ──
        sidebar_scroll = 0
        list_kb_idx = 0
        list_hover_idx = -1
        toolbar_hover = -1
        toolbar_rects = []

        # ── 特效状态 ──
        self.current_effect = 'none'
        EFFECT_NAMES = ('none', 'bloom', 'edge', 'motion_trail', 'invert', 'vignette')

        self.running = True
        fps_history = []
        frame_count = 0
        self._cached_stats = {'mean': 0, 'std': 0, 'alive': 0}

        while self.running:
            frame_count += 1
            # ── 事件处理 ─────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                elif event.type == pygame.VIDEORESIZE:
                    self.win_w = event.w
                    self.win_h = event.h
                    self.screen = pygame.display.set_mode(
                        (self.win_w, self.win_h),
                        pygame.RESIZABLE | self._renderer_flag
                    )
                    # 更新 renderer 引用
                    _get_renderer = getattr(pygame.display, 'get_renderer', None)
                    self.renderer = _get_renderer() if _get_renderer else None
                    # 更新 render_sys 的 screen 引用
                    self.render_sys.set_screen(
                        self.renderer if self.renderer is not None else self.screen,
                        (self.SIDEBAR_W, self.TOOLBAR_H,
                         self.win_w - self.SIDEBAR_W,
                         self.win_h - self.TOOLBAR_H)
                    )
                    hud = HUD(self.font, self.font_small, self.win_w, self.win_h)
                    grid.resize(sw, th, self.win_w - sw, self.win_h - th)
                    continue

                # ── 键盘：B 键切换浏览模式 ──
                if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                    grid.visible = not grid.visible
                    if grid.visible:
                        grid.apply_filter(search_box.text, dropdown.current)
                        grid.resize(sw, th, self.win_w - sw, self.win_h - th)
                    continue

                # ── 浏览模式：键盘事件发给网格 ──
                if grid.visible and event.type == pygame.KEYDOWN:
                    grid_result = grid.handle_event(event)
                    if grid_result is not None:
                        action = grid_result[0] if isinstance(grid_result, tuple) else grid_result
                        if action == 'select':
                            _, (sel_name, sel_path) = grid_result
                            grid.visible = False
                            self.load_recipe_by_name(sel_name)
                            self.notify(f"已切换: {self._fmt_name(sel_name)[:24]}", (100, 220, 100))
                            self._rebuild_after_recipe_change()
                        elif action == 'mode_change':
                            pass  # grid 自己处理了 B/ESC
                    continue

                if event.type == pygame.KEYDOWN:
                    changed = search_box.handle_key(event)
                    if changed:
                        sidebar_scroll = 0
                        list_kb_idx = 0
                        if grid.visible:
                            grid.apply_filter(search_box.text, dropdown.current)
                        continue
                    else:
                        # 列表导航
                        filtered = self._filter_for_ui(dropdown, search_box)
                        if filtered:
                            visible_rows = (self.win_h - self._list_y(dropdown, search_box)
                                            - (param_panel.panel_height() if hasattr(param_panel, 'visible') and param_panel.visible else 0)) // 20
                            if event.key == pygame.K_DOWN:
                                list_kb_idx = min(list_kb_idx + 1, len(filtered) - 1)
                                if list_kb_idx < sidebar_scroll:
                                    sidebar_scroll = max(0, list_kb_idx - 2)
                                elif list_kb_idx >= sidebar_scroll + visible_rows:
                                    sidebar_scroll = min(list_kb_idx - visible_rows + 3, list_kb_idx)
                            elif event.key == pygame.K_UP:
                                list_kb_idx = max(list_kb_idx - 1, 0)
                                if list_kb_idx < sidebar_scroll:
                                    sidebar_scroll = max(0, list_kb_idx - 2)
                                elif list_kb_idx >= sidebar_scroll + visible_rows:
                                    sidebar_scroll = min(list_kb_idx - visible_rows + 3, list_kb_idx)
                            elif event.key == pygame.K_RETURN:
                                if 0 <= list_kb_idx < len(filtered):
                                    name, path = filtered[list_kb_idx]
                                    preview.show(name, str(path))
                            elif event.key == pygame.K_ESCAPE:
                                if preview.visible:
                                    preview.hide()
                                search_box.clear()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos

                    # ── 浏览模式：主区域事件发给网格 ──
                    if grid.visible and mx >= sw:
                        grid_result = grid.handle_event(event)
                        if grid_result is not None:
                            action = grid_result[0] if isinstance(grid_result, tuple) else grid_result
                            if action == 'select':
                                _, (sel_name, sel_path) = grid_result
                                grid.visible = False
                                self.load_recipe_by_name(sel_name)
                                self.notify(f"已切换: {self._fmt_name(sel_name)[:24]}", (100, 220, 100))
                                self._rebuild_after_recipe_change()
                        continue

                    if event.button in (4, 5):
                        # 滚轮
                        if mx < sw:
                            filtered = self._filter_for_ui(dropdown, search_box)
                            lst_y = self._list_y(dropdown, search_box)
                            ph = param_panel.panel_height() if hasattr(param_panel, 'visible') and param_panel.visible else 0
                            visible_rows = (self.win_h - lst_y - ph) // 20
                            max_scroll = max(0, len(filtered) - visible_rows)
                            sidebar_scroll = max(0, sidebar_scroll - 2) if event.button == 4 else min(max_scroll, sidebar_scroll + 2)
                    elif event.button == 1:
                        # 左键点击
                        if my < th:
                            # 工具栏
                            for i, br in enumerate(toolbar_rects):
                                if br.collidepoint(mx, my):
                                    self._do_toolbar(i, TOOLBAR_BTNS, param_panel)
                                    break
                            continue

                        # 右侧预览面板（优先处理，即使鼠标在右区）
                        ca_area = (sw, th, self.win_w - sw, self.win_h - th)
                        action = preview.handle_mouse_down(mx, my)
                        if action == 'render':
                            name = preview.name
                            preview.hide()
                            self.load_recipe_by_name(name)
                            self.notify(f"已切换: {self._fmt_name(name)[:24]}", (100, 220, 100))
                            sidebar_scroll = 0
                            list_kb_idx = 0
                            self._rebuild_after_recipe_change()
                            continue
                        elif action == 'cancel':
                            preview.hide()
                            continue

                        if mx >= sw:
                            if dropdown.open:
                                dropdown.open = False
                            continue

                        # 下拉菜单
                        consumed, new_cat = dropdown.handle_mouse_down(mx, my)
                        if consumed:
                            if new_cat is not None:
                                sidebar_scroll = 0
                                search_box.clear()
                            if grid.visible:
                                grid.apply_filter(search_box.text, dropdown.current)
                            continue

                        # 搜索框
                        if search_box.handle_mouse_down(mx, my):
                            continue

                        # 列表点击
                        filtered = self._filter_for_ui(dropdown, search_box)
                        lst_y = self._list_y(dropdown, search_box)
                        if my >= lst_y and filtered:
                            ph = param_panel.panel_height() if hasattr(param_panel, 'visible') and param_panel.visible else 0
                            avail = self.win_h - lst_y - ph
                            row = (my - lst_y + sidebar_scroll * 20) // 20
                            if 0 <= row < len(filtered):
                                name, path = filtered[row]
                                list_kb_idx = row
                                preview.show(name, str(path))

                elif event.type == pygame.MOUSEBUTTONUP:
                    # ── 浏览模式：鼠标松开事件发给网格（无论在哪松开）──
                    if grid.visible:
                        grid.handle_event(event)

                elif event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    # ── 浏览模式：所有主区域事件发给网格 ──
                    if grid.visible and mx >= sw:
                        grid.handle_event(event)
                        continue

                    toolbar_hover = -1
                    if my < th:
                        for i, br in enumerate(toolbar_rects):
                            if br.collidepoint(mx, my):
                                toolbar_hover = i
                                break
                    dropdown.handle_mouse_move(mx, my)
                    preview.handle_mouse_move(mx, my)
                    # 列表hover
                    list_hover_idx = -1
                    if mx < sw:
                        filtered = self._filter_for_ui(dropdown, search_box)
                        lst_y = self._list_y(dropdown, search_box)
                        if my >= lst_y and filtered:
                            row = (my - lst_y + sidebar_scroll * 20) // 20
                            if 0 <= row < len(filtered):
                                list_hover_idx = row

            if not self.running:
                break

            # ── 时间更新 ──
            self._update_timers()

            # ── 自动播放 ──
            if self.auto_play and not self.paused:
                self._auto_counter += 1
                if self._auto_counter >= self.auto_interval:
                    self._auto_counter = 0
                    idx = self._effect_list.index(self.entity.config.name) if self.entity and self.entity.config.name in self._effect_list else self._effect_index
                    self.load_recipe_by_index(idx + 1)
                    self._rebuild_after_recipe_change()

            # ── 演化 ──
            if not self.paused and self.entity is not None:
                for _ in range(self.entity.config.steps_per_frame):
                    self.evolution_sys._step(self.entity.grid, self.entity.formula, self.entity.config)
                if self.entity.grid.t == 0 and self.entity.grid.total_cycles > 0:
                    self.entity.postfx.trail_buffer = None

            # ── 颜色映射 ──
            if self.entity is not None:
                self.color_sys.update(self.entity)

            # ── 渲染 CA 帧 / 网格浏览器 ──
            screen_bg = (14, 14, 20)
            self.screen.fill(screen_bg)

            # 浏览模式：主区域画网格，覆盖 CA / 预览
            if grid.visible:
                grid.update()   # 增量预加载缩略图（不阻塞）
                grid.draw(self.screen)
            elif preview.visible:
                ca_area = (sw, th, self.win_w - sw, self.win_h - th)
                preview.draw(self.screen, ca_area)
            elif self.entity is not None:
                # 同步特效状态到 PostProcessComponent
                self.entity.postfx.active_effect = self.current_effect
                # 统一走 RenderSystem，不再直接操作 Surface
                self.render_sys.update_transition()
                self.render_sys.draw(self.entity)
            else:
                # 未选择配方时：显示占位提示
                ca_w = self.win_w - sw
                ca_h = self.win_h - th
                hint = self.font.render("请从左侧列表选择一个配方", True, (120, 120, 150))
                hint2 = self.font_small.render("点击配方 → 预览 → 确认渲染", True, (100, 100, 130))
                self.screen.blit(hint, (sw + ca_w // 2 - hint.get_width() // 2,
                                        th + ca_h // 2 - 16))
                self.screen.blit(hint2, (sw + ca_w // 2 - hint2.get_width() // 2,
                                          th + ca_h // 2 + 6))

            # ── 绘制 UI ──
            # 工具栏
            self._draw_toolbar(TOOLBAR_BTNS, toolbar_hover, toolbar_rects)

            # 侧边栏
            self._draw_sidebar(dropdown, search_box, param_panel,
                               sidebar_scroll, list_hover_idx,
                               list_kb_idx)

            # HUD
            notify = self.notify_msg if self.notify_timer > 0 else None
            error = self.error_msg if self.error_timer > 0 else None
            if self.entity:
                # 每10帧更新一次统计，避免每帧5次全网格遍历
                if frame_count % 10 == 0:
                    self._cached_stats = self.entity.grid.get_stats()
                stats = self._cached_stats
                cycle_info = ""
                if self.entity.config.cycle_steps > 0:
                    cycle_info = f" | cycle:{self.entity.grid.t}/{self.entity.config.cycle_steps}(#{self.entity.grid.total_cycles})"
                name = self._fmt_name()
                t = self.entity.grid.t
            else:
                stats = {'mean': 0, 'std': 0, 'alive': 0}
                cycle_info = ""
                name = "?"
                t = 0
            fps_history.append(self.clock.get_fps())
            if len(fps_history) > 30:
                fps_history = fps_history[-30:]
            avg_fps = sum(fps_history) / len(fps_history) if fps_history else 0
            self._draw_hud(name, t, stats, cycle_info, avg_fps, self.current_effect, notify, error)

            # 循环进度条
            if self.entity and self.entity.config.cycle_steps > 0:
                self._draw_cycle_bar()

            # 呈现帧：Renderer 模式用 present()，否则用 flip()
            if hasattr(self, 'renderer') and self.renderer is not None:
                self.renderer.present()
            else:
                pygame.display.flip()
            self.clock.tick(self.entity.config.fps if self.entity else 30)

        pygame.quit()

    # ================================================================
    #  UI 辅助方法
    # ================================================================

    def _filter_for_ui(self, dropdown, search_box):
        """返回 [(name, Path), ...] — 按分类（effect名）+ 搜索词过滤"""
        cat = dropdown.current
        query = search_box.text.strip().lower()

        if cat == '全部':
            names = list(self.registry._effects.keys())
        else:
            names = self.registry.categories.get(cat, [])

        candidates = [(n, self.registry._effects[n])
                      for n in names if n in self.registry._effects]

        if query:
            candidates = [(k, v) for k, v in candidates if query in k.lower()]
        return candidates

    def _list_y(self, dropdown, search_box):
        dd = dropdown
        if dd.open:
            return dd.y + dd.header_h + len(dd.categories) * dd.ITEM_H + 4
        return dd.y + dd.header_h + 4

    def _scroll_to(self, scroll, idx, visible_rows):
        if idx < scroll:
            return max(0, idx - 2)
        elif idx >= scroll + visible_rows:
            return min(idx - visible_rows + 3, idx)
        return scroll

    def _do_toolbar(self, i, btns, param_panel):
        bid, _, _ = btns[i]
        if bid == 'pause':
            self.paused = not self.paused
            if not self.paused:
                self.auto_play = False
            self.notify("暂停" if self.paused else "继续", (200, 200, 255))
        elif bid == 'reset':
            self.reset()
            if self.entity:
                self.entity.postfx.trail_buffer = None
            self.notify("已重置网格")
        elif bid == 'screenshot':
            self._take_screenshot()
        elif bid == 'effect':
            import components.postprocess as ppc
            effects = list(ppc.EFFECT_NAMES)
            cur = effects.index(self.current_effect)
            self.current_effect = effects[(cur + 1) % len(effects)]
            # 同步到 PostProcessComponent
            if self.entity:
                self.entity.postfx.active_effect = self.current_effect
            self.notify(f"特效: {self.current_effect}", (160, 160, 255))
        elif bid == 'preset':
            presets = list(COLOR_PRESETS.keys())
            idx = presets.index(self.current_preset)
            idx = (idx + 1) % len(presets)
            self.current_preset = presets[idx]
            self._apply_current_preset()
            self.notify(f"颜色: {self.current_preset}", (180, 180, 255))
        elif bid == 'auto':
            self.auto_play = not self.auto_play
            self.paused = False
            self.notify("自动播放 ON" if self.auto_play else "自动播放 OFF", (255, 200, 60))
        elif bid == 'param':
            self.notify("参数面板：请使用旧版界面", (120, 120, 120))

    def _draw_toolbar(self, btns, hover, rects_out):
        import pygame
        TH = self.TOOLBAR_H
        sw = self.SIDEBAR_W
        pygame.draw.rect(self.screen, (18, 18, 26), (0, 0, self.win_w, TH))
        pygame.draw.line(self.screen, (45, 45, 55), (0, TH - 1), (self.win_w, TH - 1))
        title = self.font_small.render("CA Render Engine (ECS)", True, (80, 90, 110))
        self.screen.blit(title, (8, 8))

        BTN_W, BTN_H, PAD = 38, 20, 4
        bx = self.win_w - (BTN_W + PAD) * len(btns) - 8
        by = (TH - BTN_H) // 2
        rects_out.clear()
        px, py = 0, 0
        for i, (bid, lbl, tip) in enumerate(btns):
            br = pygame.Rect(bx + i * (BTN_W + PAD), by, BTN_W, BTN_H)
            rects_out.append(br)
            if i == hover:
                bg = (60, 120, 200)
            elif bid == 'pause' and self.paused:
                bg = (160, 100, 20)
            elif bid == 'auto' and self.auto_play:
                bg = (80, 150, 30)
            else:
                bg = (35, 35, 45)
            pygame.draw.rect(self.screen, bg, br, border_radius=3)
            t = self.font_small.render(lbl, True, (210, 210, 225))
            self.screen.blit(t, (br.x + (BTN_W - t.get_width()) // 2,
                                  br.y + (BTN_H - t.get_height()) // 2))

    def _draw_sidebar(self, dropdown, search_box, param_panel,
                      scroll, hover_idx, kb_idx):
        import pygame
        sw = self.SIDEBAR_W
        th = self.TOOLBAR_H
        ROW_H = 20

        # 背景（位于 HUD 条下方）
        sidebar_y = th + 22
        pygame.draw.rect(self.screen, (22, 22, 30), (0, sidebar_y, sw, self.win_h - sidebar_y))
        pygame.draw.line(self.screen, (48, 48, 56), (sw - 1, sidebar_y), (sw - 1, self.win_h))

        # 搜索框（顶部固定位置，不需要动态 Y）
        search_box.draw(self.screen)

        # 下拉菜单（搜索框下方，动态展开）
        dropdown.draw(self.screen)

        # 列表区域（下拉菜单下方）
        lst_y = self._list_y(dropdown, search_box)
        items = self._filter_for_ui(dropdown, search_box)
        ph = (param_panel.panel_height()
              if hasattr(param_panel, 'visible') and param_panel.visible and param_panel.params
              else 0)
        avail = self.win_h - lst_y - ph
        visible_rows = max(0, avail // ROW_H)
        max_scroll = max(0, len(items) - visible_rows)

        current_name = self.entity.config.name if self.entity else ''
        query = search_box.text.strip().lower()

        for vi, rel_i in enumerate(range(scroll, min(scroll + visible_rows, len(items)))):
            name, path = items[rel_i]
            y = lst_y + vi * ROW_H
            row_rect = pygame.Rect(2, y, sw - 4, ROW_H)

            is_current = (name == current_name)
            is_hover = (rel_i == hover_idx)
            is_kb = (rel_i == kb_idx)

            if is_current:
                bg = (160, 120, 30) if self.auto_play else (40, 95, 175)
                pygame.draw.rect(self.screen, bg, row_rect, border_radius=4)
                tc = (240, 240, 255)
            elif is_hover:
                pygame.draw.rect(self.screen, (50, 60, 80), row_rect, border_radius=4)
                tc = (210, 220, 240)
            elif is_kb:
                pygame.draw.rect(self.screen, (38, 44, 58), row_rect, border_radius=4)
                pygame.draw.rect(self.screen, (70, 110, 180), row_rect, 1, border_radius=4)
                tc = (200, 210, 230)
            elif rel_i % 2 == 1:
                pygame.draw.rect(self.screen, (24, 24, 34), row_rect, border_radius=4)
                tc = (140, 140, 158)
            else:
                tc = (145, 145, 162)

            # 名称+高亮（带编号前缀）
            rid = self.registry.get_effect_id(name)
            id_prefix = f'#{rid:03d} ' if rid else ''
            full_display = id_prefix + name
            if query and query in name.lower():
                pos = name.lower().find(query)
                before = id_prefix + name[:pos]
                match = name[pos:pos + len(query)]
                after = name[pos + len(query):]
                x = 8
                if before:
                    bt = self.font_small.render(before, True, tc)
                    self.screen.blit(bt, (x, y + 4))
                    x += bt.get_width()
                mt = self.font_small.render(match, True, (255, 220, 60))
                self.screen.blit(mt, (x, y + 4))
                x += mt.get_width()
                if after and x < sw - 10:
                    at = self.font_small.render(after, True, tc)
                    self.screen.blit(at, (x, y + 4))
            else:
                display = full_display if len(full_display) <= 22 else full_display[:21] + '…'
                txt = self.font_small.render(display, True, tc)
                self.screen.blit(txt, (8, y + 4))

        # 滚动条
        if len(items) > visible_rows and visible_rows > 0:
            thumb_ratio = visible_rows / len(items)
            thumb_h = max(18, int(avail * thumb_ratio))
            ratio = scroll / max(max_scroll, 1)
            thumb_y = lst_y + int((avail - thumb_h) * ratio)
            pygame.draw.rect(self.screen, (65, 65, 78), (sw - 5, thumb_y, 3, thumb_h), border_radius=2)

        # 计数
        count_txt = self.font_small.render(f"{len(items)}/{len(self._effect_list)}", True, (80, 80, 95))
        self.screen.blit(count_txt, (6, self.win_h - ph - 14))

    def _draw_hud(self, name, t, stats, cycle_info, fps, effect, notify, error):
        import pygame
        BAR_H = 22
        bar = pygame.Surface((self.win_w, BAR_H), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 140))
        self.screen.blit(bar, (0, self.TOOLBAR_H))

        status = f"{'||' if self.paused else '▶'} " if self.paused or self.auto_play else ""
        info = f"{status}{name} | t:{t} | μ:{stats['mean']:.3f} σ:{stats['std']:.3f} active:{stats['alive']:.1%}{cycle_info}"
        txt = self.font_small.render(info[:120], True, (200, 200, 220))
        self.screen.blit(txt, (6, self.TOOLBAR_H + 4))

        ft = self.font_small.render(f"FPS:{fps:.0f}", True, (140, 220, 140))
        self.screen.blit(ft, (self.win_w - ft.get_width() - 8, self.TOOLBAR_H + 4))

        if self.auto_play:
            at = self.font_small.render("[AUTO]", True, (255, 200, 60))
            self.screen.blit(at, (self.win_w - ft.get_width() - 100, self.TOOLBAR_H + 4))

        if effect and effect != 'none':
            et = self.font_small.render(f"FX:{effect}", True, (160, 160, 255))
            self.screen.blit(et, (self.win_w // 2 - et.get_width() // 2, self.TOOLBAR_H + 4))

        if notify:
            nt, nc = notify
            nt_surf = self.font.render(nt[:80], True, nc)
            tw, th2 = nt_surf.get_size()
            nb = pygame.Surface((tw + 12, th2 + 6), pygame.SRCALPHA)
            nb.fill((0, 0, 0, 180))
            self.screen.blit(nb, (6, self.TOOLBAR_H + BAR_H + 4))
            self.screen.blit(nt_surf, (12, self.TOOLBAR_H + BAR_H + 7))

        if error:
            lines = error.split('\n')[:3]
            eh = 18 * len(lines) + 6
            eb = pygame.Surface((self.win_w, eh), pygame.SRCALPHA)
            eb.fill((80, 10, 10, 200))
            self.screen.blit(eb, (0, self.win_h - eh))
            for i, line in enumerate(lines):
                et = self.font_small.render(line[:70], True, (255, 150, 150))
                self.screen.blit(et, (6, self.win_h - eh + 3 + i * 18))

    def _draw_cycle_bar(self):
        import pygame
        if not self.entity or self.entity.config.cycle_steps <= 0:
            return
        progress = self.entity.grid.t / self.entity.config.cycle_steps
        bar_w = self.entity.grid.w * self.scale_level - 16
        bar_x = self.SIDEBAR_W + 8
        bar_y = self.win_h - 10
        pygame.draw.rect(self.screen, (30, 30, 38), (bar_x, bar_y, bar_w, 4), border_radius=2)
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            pygame.draw.rect(self.screen,
                             (int(80 + 175 * progress), int(160 - 100 * progress), int(220 - 140 * progress)),
                             (bar_x, bar_y, fill_w, 4), border_radius=2)
        txt = self.font_small.render(f"cycle {self.entity.grid.t}/{self.entity.config.cycle_steps}", True, (140, 140, 160))
        self.screen.blit(txt, (bar_x, bar_y - 14))

    # ================================================================
    #  辅助
    # ================================================================

    def _apply_current_preset(self):
        if self.entity and self.current_preset != 'default':
            self.color_sys.apply_preset(self.entity, self.current_preset, self.evolution_sys)

    def _rebuild_after_recipe_change(self):
        import pygame
        if self.entity is None:
            return
        self._ca_surf = None       # 强制重建缓存（新尺寸）
        self._ca_scaled = None
        name = self._fmt_name()
        pygame.display.set_caption(f"CA Render — {name}")
        # 保持当前窗口大小不变，只更新 render_sys 的 CA 显示区域
        _get_renderer = getattr(pygame.display, 'get_renderer', None)
        self.renderer = _get_renderer() if _get_renderer else None
        self.render_sys.set_screen(
            self.renderer if self.renderer is not None else self.screen,
            (self.SIDEBAR_W, self.TOOLBAR_H,
             self.win_w - self.SIDEBAR_W,
             self.win_h - self.TOOLBAR_H)
        )

    def _take_screenshot(self):
        shot_dir = self.script_dir / 'screenshots'
        shot_dir.mkdir(exist_ok=True)
        fname = shot_dir / f"screenshot_{_time.strftime('%Y%m%d_%H%M%S')}.png"
        try:
            import pygame
            pygame.image.save(self.screen, str(fname))
            self.notify(f"已保存: {fname.name}")
        except Exception as e:
            self.notify(f"保存失败: {str(e)[:80]}", (255, 120, 120))

    def notify(self, text, color=(120, 255, 120), duration=90):
        self.notify_msg = (text, color)
        self.notify_timer = duration

    def _update_timers(self):
        if self.notify_timer > 0:
            self.notify_timer -= 1
            if self.notify_timer <= 0:
                self.notify_msg = None
        if self.error_timer > 0:
            self.error_timer -= 1
            if self.error_timer <= 0:
                self.error_msg = None

    def _quit(self, msg=None):
        if msg:
            print(f"[World] {msg}")
        import pygame
        pygame.quit()

    def _fmt_name(self, name: str = None) -> str:
        """格式化配方显示名：#编号 名称"""
        if name is None:
            if self.entity:
                name = self.entity.config.name
                rid = self.entity.config.recipe_id
            else:
                return "CA"
        else:
            rid = self.registry.get_effect_id(name)
        if rid:
            return f'#{rid:03d} {name}'
        return name

    def __repr__(self):
        n = len(self._effect_list)
        cur = self.entity.config.name if self.entity else '(无)'
        return f"<CAWorld effects={n} current='{cur}' paused={self.paused}>"
