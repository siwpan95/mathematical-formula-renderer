"""
UISystem — 用户界面系统（ECS 事件路由层）
==========================================
UI Widget 类从 renderer.py 导入（避免重复实现），UISystem 提供统一的
事件分发和绘制接口给 CAWorld 使用。

使用方式：
    ui = UISystem(world)                # 创建
    ui.build(font, font_small, sw, th)  # 构建 Widget
    ui.handle_event(event)              # 处理单个事件
    ui.draw(screen)                     # 绘制所有 UI 覆盖层
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from world import CAWorld


class UISystem:
    """统一的 UI 事件/绘制系统。

    持有所有 renderer.py 的 Widget 实例，将 CAWorld 与 UI 层隔离。
    """

    def __init__(self, world: 'CAWorld'):
        self.world = world
        self._dropdown = None
        self._search = None
        self._selection = None

    def build(self, font, font_small, sidebar_w: int, toolbar_h: int,
              categories: list, cat_counts: dict):
        """构建所有 UI Widget"""
        from ui.widgets import CategoryDropdown, SearchBox, SelectionPanel

        pad = 4
        sw = sidebar_w
        y = toolbar_h + pad

        self._dropdown = CategoryDropdown(
            font_small, pad, y, sw - pad * 2, categories, counts=cat_counts)
        y += self._dropdown.header_h + pad

        self._search = SearchBox(
            font_small, pad, y, sw - pad * 2, hint='搜索配方…')
        y += self._search.H + pad

        self._selection = SelectionPanel(font, font_small, sw)

    @property
    def dropdown(self):
        return self._dropdown

    @property
    def search(self):
        return self._search

    @property
    def selection(self):
        return self._selection

    def filtered_recipes(self, recipe_entries: list, categories: dict, recipe_files: set):
        """根据下拉菜单和搜索词过滤配方列表"""
        from pathlib import Path
        cat = self._dropdown.current if self._dropdown else '全部'
        query = self._search.text.strip().lower() if self._search else ''

        if cat == '全部':
            candidates = [(k, v) for k, v in recipe_entries]
        else:
            cat_info = categories.get(cat, {})
            cat_files = set(cat_info.get('files', []) if isinstance(cat_info, dict) else cat_info)
            candidates = [(k, v) for k, v in recipe_entries
                          if Path(v).name in cat_files]

        if query:
            candidates = [(k, v) for k, v in candidates if query in k.lower()]

        return candidates

    def drop_visible_y(self) -> int:
        """下拉菜单展开时的额外偏移"""
        if self._dropdown is None:
            return 0
        dd = self._dropdown
        if dd.open:
            return dd.y + dd.header_h + len(dd.categories) * dd.ITEM_H + 4 + self._search.H + 4
        return dd.y + dd.header_h + 4 + self._search.H + 4

    def draw_all(self, screen, win_h: int):
        """按 Z 顺序绘制所有 UI 层"""
        if self._dropdown:
            self._dropdown.draw(screen)
        if self._search:
            self._search.draw(screen)
        if self._selection:
            self._selection.draw(screen, win_h)
