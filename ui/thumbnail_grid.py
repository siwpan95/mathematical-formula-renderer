"""
ThumbnailGrid — 缩略图网格浏览器 Widget
========================================

Phase 2 + Phase 3 UI：替换主区域的文本列表，改为缩略图网格浏览。
- 按 B 键切换浏览模式
- 网格占用整个主区域（右侧）
- 缩略图从 effects/thumbs/ 加载
- 支持滚动、搜索过滤、分类筛选
- Phase 3 优化：虚拟滚动、LRU 缓存、增量预加载、键盘导航增强
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from collections import OrderedDict

import pygame

from entities.registry import TemplateRegistry


# ================================================================
#  缩略图网格浏览器
# ================================================================

class ThumbnailGrid:
    """
    缩略图网格浏览器 Widget。

    使用方式：
        grid = ThumbnailGrid(font, font_small, x, y, w, h)
        grid.set_recipes(registry.effect_names, registry)
        grid.handle_event(event)
        grid.draw(screen)
    """

    C_BG         = (14, 14, 20)
    C_CELL_BG    = (28, 30, 40)
    C_CELL_HOVER = (45, 50, 70)
    C_CELL_SEL   = (50, 110, 200)
    C_NAME       = (200, 210, 230)
    C_NAME_SEL   = (255, 255, 255)
    C_SCROLL_BG  = (30, 30, 40)
    C_SCROLL_FG  = (80, 80, 100)
    C_EMPTY      = (60, 60, 75)
    C_LOADING    = (80, 80, 100)

    # 分类标签栏
    C_TAG_BG      = (35, 35, 45)
    C_TAG_HOVER   = (55, 60, 80)
    C_TAG_ACTIVE   = (50, 110, 200)
    C_TAG_TEXT     = (180, 190, 210)
    C_TAG_TEXT_ACT = (255, 255, 255)
    TAG_H          = 28
    TAG_PADDING   = 8
    TAG_MARGIN     = 3

    # 分类图标颜色（每个分类一个标识色）
    CAT_COLORS = {
        '全部':       (120, 120, 140),
        'init':       (80, 180, 120),   # 绿色 — 初始化
        'evolution':  (220, 160, 50),   # 橙色 — 演化
        'color':      (180, 100, 220),   # 紫色 — 颜色
        'boundary':   (60, 160, 220),   # 蓝色 — 边界
        'postprocess': (220, 80, 100),   # 红色 — 后处理
        'topology':   (80, 200, 200),   # 青色 — 拓扑
        'neighborhood': (200, 180, 60),  # 黄色 — 邻域
        '收藏':       (230, 60, 90),     # 桃红 — 收藏
    }
    CAT_ICON_R = 5  # 图标圆圈半径

    # 搜索框
    C_SEARCH_BG   = (25, 25, 35)
    C_SEARCH_BORDER = (60, 60, 80)
    C_SEARCH_TEXT  = (200, 210, 230)
    C_SEARCH_HINT  = (80, 80, 100)
    SEARCH_H       = 26
    SEARCH_PAD     = 6

    # 缩略图尺寸（可配置）
    THUMB_W   = 96
    THUMB_H   = 96
    TEXT_H    = 16   # 名称文字高度
    PADDING   = 6
    COLS_AUTO = 0    # 自动计算列数

    # 性能：LRU 缓存最多保留多少个缩略图 Surface
    MAX_CACHED = 600
    # 每帧预加载多少个缩略图（避免卡顿）
    PRELOAD_PER_FRAME = 6

    def __init__(self, font, font_small, x: int, y: int, w: int, h: int):
        self.font = font
        self.font_small = font_small
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        # 网格布局参数（在 set_recipes 里计算）
        self.cols = 4
        self.rows_visible = 0
        self.total_rows = 0

        # 数据
        self.all_recipes: list[tuple[str, str]] = []   # (name, path_str)
        self.filtered:    list[tuple[str, str]] = []   # 过滤后的配方
        self.thumb_dir:   Optional[Path] = None

        # 视图状态
        self.scroll_y = 0
        self.selected_idx = -1
        self.hover_idx = -1
        self.visible = True           # 浏览模式是否激活（默认显示新UI）

        # 分类标签栏
        self.categories: list[str] = ['全部']
        self._registry = None
        self.tag_scroll_x = 0
        self.tag_hover_idx = -1

        # 网格内搜索框
        self.search_text = ''
        self.search_active = False
        self.search_hover = False

        # 缩略图缓存（LRU，最多 MAX_CACHED 个）
        self._thumb_cache: OrderedDict[str, pygame.Surface] = OrderedDict()

        # 预加载队列：存放需要加载的 (hash8, path_str) 元组
        self._preload_queue: list[tuple[str, str]] = []
        self._preload_set: set[str] = set()  # 去重，避免重复入队

        # 滚动跟踪（检测滚动是否变化，变化时刷新预加载队列）
        self._last_scroll_y = 0
        self._last_filtered_len = 0

        # 滚动条拖拽
        self._scroll_drag = False
        self._scroll_bar_rect = None
        self._fav_btn_rects: dict[int, pygame.Rect] = {}  # idx → 收藏按钮 rect

        # ── 收藏功能 ──
        self.fav_path = Path(__file__).parent.parent / 'effects' / 'favorites.json'
        self.favorites: set[str] = set()   # 存储配方路径（去重，O(1) 查询）
        self._fav_icon_cache: dict[str, pygame.Surface] = {}  # 收藏图标缓存
        self._load_favorites()

    # ------------------------------------------------------------
    #  收藏功能
    # ------------------------------------------------------------

    def _load_favorites(self):
        """从 favorites.json 加载收藏列表"""
        try:
            if self.fav_path.exists():
                import json
                with open(self.fav_path, encoding='utf-8') as fp:
                    data = json.load(fp)
                # 支持两种格式：list[str] 或 {"paths": list[str]}
                if isinstance(data, list):
                    self.favorites = set(data)
                elif isinstance(data, dict) and 'paths' in data:
                    self.favorites = set(data['paths'])
        except Exception:
            self.favorites = set()

    def _save_favorites(self):
        """保存收藏列表到 favorites.json"""
        try:
            import json
            self.fav_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fav_path, 'w', encoding='utf-8') as fp:
                json.dump({'paths': sorted(self.favorites)}, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _is_favorite(self, path_str: str) -> bool:
        return path_str in self.favorites

    def _toggle_favorite(self, path_str: str):
        """切换收藏状态，并持久化"""
        if path_str in self.favorites:
            self.favorites.discard(path_str)
        else:
            self.favorites.add(path_str)
        self._save_favorites()

    def _draw_fav_icon(self, screen, x: int, y: int, favorited: bool):
        """在 (x, y) 绘制收藏图标（心形，12x12）"""
        # 用心形多边形绘制
        # 简单方案：用红色/灰色圆圈 + 心形效果
        r = 6
        color = (230, 60, 90) if favorited else (90, 90, 110)
        # 画心形：两个圆 + 一个倒三角
        # 左圆
        pygame.draw.circle(screen, color, (x, y + 2), r // 2 + 1)
        # 右圆
        pygame.draw.circle(screen, color, (x + r - 1, y + 2), r // 2 + 1)
        # 倒三角（心形下半）
        points = [
            (x - r // 2 - 1, y + 2),
            (x + r + r // 2, y + 2),
            (x + r // 2, y + r + 4),
        ]
        pygame.draw.polygon(screen, color, points)
        # 如果未收藏，画个边框效果（空心感）
        if not favorited:
            # 在内层画个深色圆让它看起来是空心的
            inner_color = self.C_CELL_BG if hasattr(self, 'C_CELL_BG') else (28, 30, 40)
            pygame.draw.circle(screen, inner_color, (x, y + 2), r // 2 - 1)
            pygame.draw.circle(screen, inner_color, (x + r - 1, y + 2), r // 2 - 1)
            # 重绘边框
            pygame.draw.circle(screen, color, (x, y + 2), r // 2 + 1, 1)
            pygame.draw.circle(screen, color, (x + r - 1, y + 2), r // 2 + 1, 1)
            # 三角也只画边框
            pygame.draw.polygon(screen, inner_color, [
                (points[0][0] + 1, points[0][1] + 1),
                (points[1][0] - 1, points[1][1] + 1),
                (points[2][0], points[2][1] - 2),
            ])

    # ------------------------------------------------------------
    #  数据更新
    # ------------------------------------------------------------

    def set_recipes(self, effect_names: list[str], registry: TemplateRegistry):
        """载入配方列表（name, path）"""
        self._registry = registry
        self.all_recipes = []
        self._all_names_lower: list[str] = []  # 预构建小写名称，搜索加速
        for name in effect_names:
            path = registry.get_effect_path(name)
            if path is not None:
                p_str = str(path)
                self.all_recipes.append((name, p_str))
                self._all_names_lower.append(name.lower())
            else:
                print(f"[ThumbnailGrid] 警告: 找不到配方 {name} 的路径")

        # 预构建分类文件集合（加速过滤）
        self._cat_file_sets: dict[str, set[str]] = {}
        if registry and hasattr(registry, 'categories'):
            for cat_name, cat_val in registry.categories.items():
                if cat_name == '全部':
                    continue
                if isinstance(cat_val, (list, set)):
                    self._cat_file_sets[cat_name] = set(str(p) for p in cat_val)
                elif isinstance(cat_val, dict) and 'files' in cat_val:
                    self._cat_file_sets[cat_name] = set(str(p) for p in cat_val['files'])

        # 提取分类列表（确保"收藏"存在）
        self.categories = ['全部']
        if registry and hasattr(registry, 'categories'):
            for cat_name in registry.categories.keys():
                if cat_name != '全部':
                    self.categories.append(cat_name)
        # 追加"收藏"分类（排在最后）
        if '收藏' not in self.categories:
            self.categories.append('收藏')

        self._apply_filter('', '全部')
        self._recalc_layout()

    def set_thumb_dir(self, path: Path):
        self.thumb_dir = path

    def apply_filter(self, search_query: str, category: str):
        """由外部调用（搜索框/分类变化）"""
        self._apply_filter(search_query, category)
        self.scroll_y = 0
        self.selected_idx = -1
        self.hover_idx = -1

    def _apply_filter(self, query: str, category: str):
        """根据搜索词和分类过滤配方（优化：用预构建数据加速）"""
        query = query.strip().lower()

        # 从预构建集合取分类文件（O(1) 查找）
        cat_files = self._cat_file_sets.get(category, set()) if category not in ('全部', '收藏') else None

        filtered = []
        if category == '收藏':
            # 收藏分类：只显示已收藏的配方
            fav_set = self.favorites
            for i, (name, path) in enumerate(self.all_recipes):
                if path not in fav_set:
                    continue
                if query and query not in self._all_names_lower[i]:
                    continue
                filtered.append((name, path))
        elif query:
            # 用预构建小写列表加速
            for i, (name, path) in enumerate(self.all_recipes):
                if query not in self._all_names_lower[i]:
                    continue
                if cat_files is not None and path not in cat_files:
                    continue
                filtered.append((name, path))
        elif cat_files is not None:
            # 仅分类过滤（无搜索词）
            for name, path in self.all_recipes:
                if path in cat_files:
                    filtered.append((name, path))
        else:
            # 无过滤
            filtered = list(self.all_recipes)

        self.filtered = filtered
        self.total_rows = max(1, (len(filtered) + self.cols - 1) // self.cols)
        self._recalc_layout()
        self._refresh_preload_queue()

    def _recalc_layout(self):
        """根据当前宽高重新计算列数/可见行数"""
        # 顶部区域：标签栏 + 搜索框
        top_h = self.TAG_H + self.SEARCH_H + self.PADDING
        available_w = self.w - self.PADDING * 2
        self.cols = max(2, available_w // (self.THUMB_W + self.PADDING))
        cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
        grid_h = self.h - top_h - self.PADDING * 2 - 20  # 减去底部状态栏
        self.rows_visible = grid_h // cell_h + 1
        self._grid_top = top_h + self.PADDING
        self._grid_h = grid_h

    # ------------------------------------------------------------
    #  缩略图缓存 & 预加载
    # ------------------------------------------------------------

    def _cache_get(self, h: str) -> Optional[pygame.Surface]:
        """从 LRU 缓存中取缩略图，命中则移到末尾（最近使用）"""
        if h in self._thumb_cache:
            surf = self._thumb_cache.pop(h)
            self._thumb_cache[h] = surf
            return surf
        return None

    def _cache_put(self, h: str, surf: pygame.Surface):
        """放入 LRU 缓存，超过上限时淘汰最久未用的"""
        if h in self._thumb_cache:
            self._thumb_cache.pop(h)
        elif len(self._thumb_cache) >= self.MAX_CACHED:
            self._thumb_cache.popitem(last=False)  # 淘汰最久未用的
        self._thumb_cache[h] = surf

    def _recipe_hash(self, path_str: str) -> str:
        """从配方 JSON 计算 8 位哈希（与 gen_thumbs.py 一致）"""
        try:
            import json, hashlib
            with open(path_str, encoding='utf-8') as fp:
                recipe = json.load(fp)
            key_data = {
                'grid':       recipe.get('grid', {}),
                'evolution':  recipe.get('evolution', {}),
                'color':      recipe.get('color', {}),
                'cycle':      recipe.get('cycle', {}),
                'postprocess': recipe.get('postprocess', {}),
            }
            s = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha1(s.encode()).hexdigest()[:8]
        except Exception:
            return ''

    def _load_thumb_cached(self, path_str: str) -> Optional[pygame.Surface]:
        """
        仅从缓存取缩略图，不触发磁盘 I/O。
        用于 draw() 中，保证不卡顿。
        """
        h = self._recipe_hash(path_str)
        if not h:
            return None
        return self._cache_get(h)

    def _preload_one(self, path_str: str) -> bool:
        """
        实际加载一个缩略图到缓存（磁盘 I/O）。
        每帧调用少量次数（PRELOAD_PER_FRAME）。
        返回是否成功加载。
        """
        h = self._recipe_hash(path_str)
        if not h or h in self._thumb_cache:
            return False  # 已缓存或无效 hash

        if self.thumb_dir is None:
            return False
        thumb_path = self.thumb_dir / f"{h}.png"
        if not thumb_path.exists():
            return False
        try:
            surf = pygame.image.load(str(thumb_path))
            if surf.get_size() != (self.THUMB_W, self.THUMB_H):
                surf = pygame.transform.smoothscale(surf, (self.THUMB_W, self.THUMB_H))
            self._cache_put(h, surf)
            return True
        except Exception:
            return False

    def _refresh_preload_queue(self):
        """
        根据当前滚动位置和过滤结果，刷新预加载队列。
        预加载顺序：可见区域 → 向下缓冲 → 向上缓冲
        """
        if not self.filtered:
            self._preload_queue = []
            self._preload_set = set()
            return

        cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
        start_row = int(max(0, self.scroll_y // cell_h))
        end_row   = int(min(self.total_rows, start_row + self.rows_visible + 1))

        # 收集需要预加载的索引（可见 + 缓冲 2 屏）
        buffer_rows = self.rows_visible * 2
        preload_rows = range(
            max(0, start_row - buffer_rows),
            min(self.total_rows, end_row + buffer_rows)
        )
        new_queue = []
        new_set = set()
        for row in preload_rows:
            for col in range(self.cols):
                idx = row * self.cols + col
                if 0 <= idx < len(self.filtered):
                    _, path_str = self.filtered[idx]
                    h = self._recipe_hash(path_str)
                    if h and h not in self._thumb_cache and h not in new_set:
                        new_queue.append((h, path_str))
                        new_set.add(h)

        self._preload_queue = new_queue
        self._preload_set = new_set

    def update(self):
        """
        每帧调用一次，增量预加载缩略图。
        不阻塞：每帧最多加载 PRELOAD_PER_FRAME 个。
        """
        # 清空收藏按钮 rect 缓存（本帧会重新填充）
        self._fav_btn_rects.clear()

        # 检测滚动或过滤变化，刷新预加载队列
        if (self.scroll_y != self._last_scroll_y or
                len(self.filtered) != self._last_filtered_len):
            self._refresh_preload_queue()
            self._last_scroll_y = self.scroll_y
            self._last_filtered_len = len(self.filtered)

        # 增量加载
        loaded = 0
        while loaded < self.PRELOAD_PER_FRAME and self._preload_queue:
            h, path_str = self._preload_queue.pop(0)
            self._preload_set.discard(h)
            if h not in self._thumb_cache:
                self._preload_one(path_str)
                loaded += 1

    # ------------------------------------------------------------
    #  绘制
    # ------------------------------------------------------------

    def draw(self, screen: pygame.Surface):
        """绘制整个网格浏览器"""
        if not self.visible:
            return

        # 0. 背景
        bg = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        bg.fill((*self.C_BG, 255))
        screen.blit(bg, (self.x, self.y))

        # 1. 分类标签栏
        self._draw_tag_bar(screen)

        # 2. 搜索框
        self._draw_search_box(screen)

        # 3. 网格区域（标签栏 + 搜索框下方）
        grid_y = self.y + self._grid_top
        grid_h = self._grid_h

        if not self.filtered:
            # 空状态
            txt = self.font.render("没有找到匹配的配方", True, self.C_EMPTY)
            screen.blit(txt, (self.x + self.w // 2 - txt.get_width() // 2,
                             grid_y + grid_h // 2))
        else:
            # 计算可见范围
            cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
            start_row = max(0, self.scroll_y // cell_h)
            end_row   = min(self.total_rows, start_row + self.rows_visible + 1)

            # 绘制可见单元格
            for row in range(start_row, end_row):
                for col in range(self.cols):
                    idx = row * self.cols + col
                    if idx >= len(self.filtered):
                        break
                    self._draw_cell_at(screen, idx, row, col, grid_y)

            # 滚动条
            self._draw_scrollbar(screen, grid_y, grid_h)

        # 4. 状态栏（底部）
        self._draw_status_bar(screen)

    def _draw_cell(self, screen, idx: int, row: int, col: int):
        """绘制一个网格单元格（兼容旧接口）"""
        self._draw_cell_at(screen, idx, row, col, self.y + self._grid_top)

    def _draw_cell_at(self, screen, idx: int, row: int, col: int, grid_y: int):
        """绘制一个网格单元格（支持自定义网格起始 Y），含收藏按钮"""
        cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
        x = self.x + self.PADDING + col * (self.THUMB_W + self.PADDING)
        y = grid_y + self.PADDING + row * cell_h - self.scroll_y

        name, path_str = self.filtered[idx]

        # 背景
        bg_color = self.C_CELL_BG
        if idx == self.hover_idx:
            bg_color = self.C_CELL_HOVER
        if idx == self.selected_idx:
            bg_color = self.C_CELL_SEL

        cell_rect = pygame.Rect(x, y, self.THUMB_W + self.PADDING, cell_h)
        pygame.draw.rect(screen, bg_color, cell_rect, border_radius=4)

        # 缩略图（仅从缓存取，不触发磁盘 I/O）
        thumb = self._load_thumb_cached(path_str)
        thumb_y = y + self.PADDING // 2
        if thumb:
            screen.blit(thumb, (x + self.PADDING // 2, thumb_y))
        else:
            # 占位符（未缓存/未加载）
            ph_rect = pygame.Rect(
                x + self.PADDING // 2, thumb_y,
                self.THUMB_W, self.THUMB_H
            )
            pygame.draw.rect(screen, self.C_EMPTY, ph_rect, border_radius=3)
            # 如果正在预加载队列中，显示"…"，否则显示"×"（无缩略图）
            h = self._recipe_hash(path_str)
            label = "…" if h and (h in self._preload_set or h in self._thumb_cache) else "×"
            loading_txt = self.font_small.render(label, True, self.C_LOADING)
            screen.blit(loading_txt, (
                ph_rect.centerx - loading_txt.get_width() // 2,
                ph_rect.centery - loading_txt.get_height() // 2
            ))

        # ── 收藏按钮（右上角）───────────────────────
        fav_btn_size = 14
        fav_btn_x = x + self.THUMB_W + self.PADDING - fav_btn_size - 2
        fav_btn_y = y + 2
        fav_btn_rect = pygame.Rect(fav_btn_x, fav_btn_y, fav_btn_size, fav_btn_size)
        # 延迟创建 _fav_btn_rects
        if not hasattr(self, '_fav_btn_rects'):
            self._fav_btn_rects = {}
        self._fav_btn_rects[idx] = fav_btn_rect

        favorited = self._is_favorite(path_str)
        # 绘制心形图标
        cx = fav_btn_rect.centerx
        cy = fav_btn_rect.centery
        self._draw_fav_icon(screen, cx, cy, favorited)

        # ── 名称 ─────────────────────────────
        display_name = name if len(name) <= 12 else name[:11] + '…'
        name_color = self.C_NAME_SEL if idx == self.selected_idx else self.C_NAME
        txt = self.font_small.render(display_name, True, name_color)
        name_y = y + self.PADDING // 2 + self.THUMB_H + 2
        screen.blit(txt, (x + self.PADDING // 2, name_y))

    def _draw_scrollbar(self, screen, grid_y: int, grid_h: int):
        """绘制右侧滚动条"""
        if self.total_rows <= self.rows_visible:
            return  # 不需要滚动

        sb_w = 8
        sb_x = self.x + self.w - sb_w - 2
        sb_y = grid_y
        sb_h = grid_h

        # 背景
        pygame.draw.rect(screen, self.C_SCROLL_BG,
                        (sb_x, sb_y, sb_w, sb_h), border_radius=4)

        # 滑块
        total_h = self.total_rows * (self.THUMB_H + self.TEXT_H + self.PADDING)
        thumb_h = max(20, int(sb_h * grid_h / total_h))
        thumb_y = sb_y + int((self.scroll_y / max(1, total_h - grid_h)) * (sb_h - thumb_h))
        pygame.draw.rect(screen, self.C_SCROLL_FG,
                        (sb_x, thumb_y, sb_w, thumb_h), border_radius=4)

        self._scroll_bar_rect = pygame.Rect(sb_x, sb_y, sb_w, sb_h)

    def _draw_status_bar(self, screen):
        """底部状态栏：显示当前过滤结果数量"""
        bar_h = 20
        bar_y = self.y + self.h - bar_h
        pygame.draw.rect(screen, (20, 20, 28, 200),
                        (self.x, bar_y, self.w, bar_h))
        status = f"  {len(self.filtered)} / {len(self.all_recipes)}  个配方"
        txt = self.font_small.render(status, True, (120, 120, 150))
        screen.blit(txt, (self.x + 4, bar_y + 3))

    # ------------------------------------------------------------
    #  分类标签栏
    # ------------------------------------------------------------

    def _draw_tag_bar(self, screen):
        """绘制顶部分类标签栏（横向滚动），每个标签前加彩色图标"""
        bx = self.x + self.PADDING
        by = self.y + self.PADDING
        bw = self.w - self.PADDING * 2 - 40  # 留出搜索框位置
        bh = self.TAG_H

        # 背景
        pygame.draw.rect(screen, (20, 20, 28),
                        (self.x, self.y, self.w, self.TAG_H + self.PADDING * 2))

        # 计算标签位置
        x = bx - self.tag_scroll_x
        tag_rects = []
        self._tag_rects = tag_rects

        icon_r = self.CAT_ICON_R
        icon_gap = 4  # 图标与文字间距

        for i, cat in enumerate(self.categories):
            # 先渲染文字得到宽度
            txt_surf = self.font_small.render(cat, True, (200, 210, 230))
            tw = txt_surf.get_width() + self.TAG_PADDING * 2 + icon_r * 2 + icon_gap
            rect = pygame.Rect(x, by, tw, bh)
            tag_rects.append((rect, cat))

            # 颜色
            if i == self.tag_hover_idx:
                bg = self.C_TAG_HOVER
                fg = self.C_TAG_TEXT_ACT
            elif cat == self._current_category():
                bg = self.C_TAG_ACTIVE
                fg = self.C_TAG_TEXT_ACT
            else:
                bg = self.C_TAG_BG
                fg = self.C_TAG_TEXT

            pygame.draw.rect(screen, bg, rect, border_radius=4)

            # 分类图标（彩色圆圈）
            icon_color = self.CAT_COLORS.get(cat, (120, 120, 140))
            icon_cx = rect.x + self.TAG_PADDING + icon_r
            icon_cy = rect.centery
            pygame.draw.circle(screen, icon_color, (icon_cx, icon_cy), icon_r)
            # 给当前选中/悬停的图标加高亮边框
            if cat == self._current_category() or i == self.tag_hover_idx:
                pygame.draw.circle(screen, (255, 255, 255), (icon_cx, icon_cy), icon_r, 1)

            # 分类文字（右移给图标留空间）
            txt_x = icon_cx + icon_r + icon_gap
            txt_y = rect.y + (bh - txt_surf.get_height()) // 2
            txt_surf = self.font_small.render(cat, True, fg)
            screen.blit(txt_surf, (txt_x, txt_y))

            x += tw + self.TAG_MARGIN

        self._tag_total_w = x - bx + self.tag_scroll_x

    def _current_category(self) -> str:
        """返回当前选中的分类（从 registry 或从实例变量）"""
        if hasattr(self, '_active_category'):
            return self._active_category
        return '全部'

    def _draw_search_box(self, screen):
        """绘制网格内的搜索框"""
        sx = self.x + self.w - 140
        sy = self.y + self.PADDING
        sw = 134
        sh = self.SEARCH_H

        # 背景
        bg = self.C_SEARCH_BG if not self.search_active else (30, 30, 42)
        pygame.draw.rect(screen, bg, (sx, sy, sw, sh), border_radius=4)
        border_c = self.C_SEARCH_BORDER if not self.search_active else (90, 130, 220)
        pygame.draw.rect(screen, border_c, (sx, sy, sw, sh), 1, border_radius=4)

        # 文字
        if self.search_text:
            txt = self.font_small.render(self.search_text, True, self.C_SEARCH_TEXT)
            screen.blit(txt, (sx + self.SEARCH_PAD, sy + (sh - txt.get_height()) // 2))
        else:
            hint = "搜索..." if not self.search_active else ""
            txt = self.font_small.render(hint, True, self.C_SEARCH_HINT)
            screen.blit(txt, (sx + self.SEARCH_PAD, sy + (sh - txt.get_height()) // 2))

        # 光标
        if self.search_active and (pygame.time.get_ticks() // 500) % 2:
            cursor_x = sx + self.SEARCH_PAD + (txt.get_width() if self.search_text else 0)
            pygame.draw.line(screen, self.C_SEARCH_TEXT,
                             (cursor_x, sy + 4), (cursor_x, sy + sh - 4), 1)

        self._search_rect = pygame.Rect(sx, sy, sw, sh)

    # ------------------------------------------------------------
    #  事件处理：标签栏 + 搜索框 + 键盘导航
    # ------------------------------------------------------------

    def _handle_tag_bar_event(self, event) -> bool:
        """处理标签栏事件，返回是否消耗事件"""
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.tag_hover_idx = -1
            if hasattr(self, '_tag_rects'):
                for i, (rect, _) in enumerate(self._tag_rects):
                    if rect.collidepoint(mx, my):
                        self.tag_hover_idx = i
                        break
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if hasattr(self, '_tag_rects'):
                for i, (rect, cat) in enumerate(self._tag_rects):
                    if rect.collidepoint(mx, my):
                        self._active_category = cat
                        self.apply_filter(self.search_text, cat)
                        self._scroll_tag_to_visible(i)
                        return True
            # 标签栏区域滚轮横向滚动（加速：60px/格）
            if self.y <= my < self.y + self.TAG_H + self.PADDING * 2:
                if event.button == 4:
                    self.tag_scroll_x = max(0, self.tag_scroll_x - 60)
                    return True
                elif event.button == 5:
                    max_scroll = max(0, getattr(self, '_tag_total_w', 0) - (self.w - 180))
                    self.tag_scroll_x = min(max_scroll, self.tag_scroll_x + 60)
                    return True
        return False

    def _scroll_tag_to_visible(self, tag_idx: int):
        """把第 tag_idx 个标签滚动到可见区域"""
        if not hasattr(self, '_tag_rects') or tag_idx >= len(self._tag_rects):
            return
        rect, _ = self._tag_rects[tag_idx]
        tag_left = rect.x
        tag_right = rect.right
        visible_w = self.w - 180
        if tag_right > self.x + visible_w:
            self.tag_scroll_x += tag_right - (self.x + visible_w) + 10
        elif tag_left < self.x + self.PADDING:
            self.tag_scroll_x = max(0, self.tag_scroll_x - (self.x + self.PADDING - tag_left) - 10)

    def _handle_tag_key(self, key: int) -> bool:
        """处理标签栏键盘导航（左右键切换分类），返回是否消耗事件"""
        cats = self.categories
        cur = 0
        cur_cat = self._current_category()
        if cur_cat in cats:
            cur = cats.index(cur_cat)
        if key == pygame.K_LEFT and cur > 0:
            self._active_category = cats[cur - 1]
            self.apply_filter(self.search_text, self._active_category)
            self._scroll_tag_to_visible(cur - 1)
            return True
        elif key == pygame.K_RIGHT and cur < len(cats) - 1:
            self._active_category = cats[cur + 1]
            self.apply_filter(self.search_text, self._active_category)
            self._scroll_tag_to_visible(cur + 1)
            return True
        return False

    def _handle_search_event(self, event) -> bool:
        """处理搜索框事件，返回是否消耗事件"""
        if not hasattr(self, '_search_rect'):
            return False

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.search_hover = self._search_rect.collidepoint(mx, my)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._search_rect.collidepoint(mx, my):
                self.search_active = True
                return True
            else:
                self.search_active = False
                # 点击外部不清空搜索内容，只失焦
                return False

        if event.type == pygame.KEYDOWN and self.search_active:
            if event.key == pygame.K_ESCAPE:
                # ESC：如果搜索框有内容则清空，否则失焦
                if self.search_text:
                    self.search_text = ''
                    self.apply_filter('', self._current_category())
                else:
                    self.search_active = False
                return True
            elif event.key == pygame.K_RETURN:
                self.search_active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.search_text = self.search_text[:-1]
                self.apply_filter(self.search_text, self._current_category())
                return True
            else:
                if event.unicode and event.unicode.isprintable() and event.unicode != '`':
                    self.search_text += event.unicode
                    self.apply_filter(self.search_text, self._current_category())
                return True

        return False

    def _handle_keyboard_nav(self, event) -> Optional[tuple]:
        """
        键盘导航增强：
        - 方向键：移动选中
        - Ctrl+左/右：跳到行首/行尾
        - Ctrl+上/下：跳到首页/尾页
        - PageUp/PageDown：翻页
        - Home/End：首页/尾页
        - 字母键：快速跳转（搜索框非激活时）
        """
        key = event.key

        # 标签栏键盘导航（始终可用，除非搜索框激活）
        if not self.search_active and self._handle_tag_key(key):
            return ('consumed',)

        if key == pygame.K_DOWN:
            self._move_selection(+self.cols)
        elif key == pygame.K_UP:
            self._move_selection(-self.cols)
        elif key == pygame.K_RIGHT:
            self._move_selection(+1)
        elif key == pygame.K_LEFT:
            self._move_selection(-1)
        elif key == pygame.K_RETURN:
            if 0 <= self.selected_idx < len(self.filtered):
                return ('select', self.filtered[self.selected_idx])
        elif key == pygame.K_HOME:
            self.selected_idx = 0
            self._scroll_to_idx(self.selected_idx)
        elif key == pygame.K_END:
            self.selected_idx = max(0, len(self.filtered) - 1)
            self._scroll_to_idx(self.selected_idx)
        elif key == pygame.K_PAGEUP:
            self._move_selection(-max(1, self.cols * (self.rows_visible - 1)))
        elif key == pygame.K_PAGEDOWN:
            self._move_selection(+max(1, self.cols * (self.rows_visible - 1)))
        # Ctrl+方向键 增强
        elif key == pygame.K_HOME and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            self.selected_idx = 0
            self._scroll_to_idx(self.selected_idx)
        elif key == pygame.K_END and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            self.selected_idx = max(0, len(self.filtered) - 1)
            self._scroll_to_idx(self.selected_idx)
        elif key in (pygame.K_LEFT, pygame.K_RIGHT) and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            # Ctrl+左：跳到行首；Ctrl+右：跳到行尾
            if self.selected_idx >= 0:
                row_start = (self.selected_idx // self.cols) * self.cols
                if key == pygame.K_LEFT:
                    self.selected_idx = row_start
                else:
                    row_end = min(row_start + self.cols, len(self.filtered)) - 1
                    self.selected_idx = row_end
                self._scroll_to_idx(self.selected_idx)
        # 字母快速跳转（搜索框非激活时）
        elif event.unicode and event.unicode.isprintable() and not self.search_active:
            ch = event.unicode.lower()
            # 找到第一个名称以该字母开头的配方
            for i, (name, _) in enumerate(self.filtered):
                if name.lower().startswith(ch):
                    self.selected_idx = i
                    self._scroll_to_idx(i)
                    break
        else:
            return None  # 未处理的按键
        return ('consumed',)

    def handle_event(self, event: pygame.event.Event) -> Optional[tuple]:
        """
        处理事件，返回：
          None           → 事件未处理
          ('select', (name, path)) → 用户选中了某个配方
          ('mode_change', 'ca')    → 退出浏览模式
          ('consumed',)            → 事件已处理，无特殊动作
        """
        if not self.visible:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                self.visible = True
                return ('mode_change', 'browse')
            return None

        # ── 优先处理标签栏和搜索框 ──
        if self._handle_tag_bar_event(event):
            return ('consumed',)
        if self._handle_search_event(event):
            return ('consumed',)

        # ── 键盘导航（增强版）───────────────────────
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b or event.key == pygame.K_ESCAPE:
                self.visible = False
                return ('mode_change', 'ca')

            # F 键：切换当前选中配方的收藏状态
            if event.key == pygame.K_f and self.selected_idx >= 0:
                _, path_str = self.filtered[self.selected_idx]
                self._toggle_favorite(path_str)
                # 如果当前在"收藏"分类，需要刷新过滤
                if self._current_category() == '收藏':
                    self._apply_filter(self.search_text, '收藏')
                return ('consumed',)

            nav_result = self._handle_keyboard_nav(event)
            if nav_result is not None:
                return nav_result

        # ── 鼠标滚轮 ─────────────────────────
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            mx, my = event.pos
            grid_y = self.y + self._grid_top
            if self.x <= mx < self.x + self.w and grid_y <= my < grid_y + self._grid_h:
                cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
                delta = -cell_h * 3 if event.button == 4 else +cell_h * 3
                self._scroll(delta)
                return ('consumed',)

        # ── 鼠标点击 ────────────────────────
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # 优先检测是否点击了收藏按钮
            if hasattr(self, '_fav_btn_rects'):
                for idx, rect in self._fav_btn_rects.items():
                    if rect.collidepoint(mx, my):
                        _, path_str = self.filtered[idx]
                        self._toggle_favorite(path_str)
                        # 如果当前在"收藏"分类，需要刷新过滤
                        if self._current_category() == '收藏':
                            self._apply_filter(self.search_text, '收藏')
                        return ('consumed',)

            idx = self._idx_at_pos(mx, my)
            if idx >= 0:
                self.selected_idx = idx
                return ('select', self.filtered[idx])
            # 检查是否点击了滚动条
            if self._scroll_bar_rect and self._scroll_bar_rect.collidepoint(mx, my):
                self._scroll_drag = True
                self._scroll_drag_y = my
                return ('consumed',)
            # 点击网格区域空白位置 = 失焦搜索框
            if self.search_active:
                self.search_active = False

        # ── 鼠标释放 ────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP:
            self._scroll_drag = False

        # ── 鼠标移动 ────────────────────────
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self._scroll_drag:
                cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
                total_h = self.total_rows * cell_h
                ratio = total_h / max(1, self._grid_h)
                delta = (my - self._scroll_drag_y) * ratio
                self._scroll(delta)
                self._scroll_drag_y = my
                return ('consumed',)

            self.hover_idx = self._idx_at_pos(mx, my)

        return ('consumed',)

    # ------------------------------------------------------------
    #  内部辅助
    # ------------------------------------------------------------

    def _move_selection(self, delta: int):
        """移动选中项"""
        new_idx = self.selected_idx + delta
        new_idx = max(0, min(new_idx, len(self.filtered) - 1))
        if new_idx != self.selected_idx:
            self.selected_idx = new_idx
            self._scroll_to_idx(new_idx)

    def _scroll_to_idx(self, idx: int):
        """滚动到指定索引可见"""
        row = idx // self.cols
        cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
        target_y = row * cell_h
        if target_y < self.scroll_y:
            self.scroll_y = target_y
        elif target_y + cell_h > self.scroll_y + self.h:
            self.scroll_y = target_y + cell_h - self.h

    def _scroll(self, delta: float):
        """滚动视口"""
        cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
        max_scroll = max(0, self.total_rows * cell_h - self._grid_h)
        old_scroll = self.scroll_y
        self.scroll_y = int(max(0, min(self.scroll_y + delta, max_scroll)))
        # 滚动变化超过一行的 1/4 时刷新预加载队列
        if abs(self.scroll_y - old_scroll) > cell_h * 0.25:
            self._refresh_preload_queue()

    def _idx_at_pos(self, mx: int, my: int) -> int:
        """返回鼠标位置对应的配方索引，-1 表示无"""
        # 检查是否在网格区域内
        grid_y = self.y + self._grid_top
        grid_h = self._grid_h
        if not (self.x <= mx < self.x + self.w and grid_y <= my < grid_y + grid_h - 20):  # 减去状态栏
            return -1
        cell_h = self.THUMB_H + self.TEXT_H + self.PADDING
        col = (mx - self.x - self.PADDING) // (self.THUMB_W + self.PADDING)
        row = (my - grid_y + self.scroll_y - self.PADDING) // cell_h
        if 0 <= col < self.cols and 0 <= row < self.total_rows:
            idx = row * self.cols + col
            if 0 <= idx < len(self.filtered):
                return idx
        return -1

    def resize(self, x: int, y: int, w: int, h: int):
        """窗口尺寸变化时调用"""
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._recalc_layout()
