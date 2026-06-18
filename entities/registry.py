"""
TemplateRegistry — 公式模板注册表
====================================
源自：templates.py（FORMULA_TEMPLATES dict）+ recipes.py（load_effects_from_dir）

职责：
    - 持有 153 个公式模板的索引（直接委托给 templates.FORMULA_TEMPLATES）
    - 持有 effects/ 目录扫描结果（{name: path}）
    - 提供查询接口，不含演化/渲染逻辑

ECS 视角：
    TemplateRegistry 是一个「单例 Entity」（World 中只有一个）。
    它不参与演化循环，仅被 UISystem / FormulaCompilerSystem 查询。

与旧代码的对应：
    recipes.load_effects_from_dir()  → TemplateRegistry.load_effects()
    FORMULA_TEMPLATES['init']        → TemplateRegistry.init_templates
    generate_recipe_from_templates() → TemplateRegistry.build_recipe_config()
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from templates import FORMULA_TEMPLATES
from components.config import ConfigComponent


class TemplateRegistry:
    """公式模板 + effects 目录的统一查询接口（只读，不含逻辑）。

    ECS 角色：单例 Entity，World 初始化时创建，此后只读访问。
    """

    def __init__(self):
        # 直接引用 templates.py 中的 dict（不复制，节省内存）
        self._templates = FORMULA_TEMPLATES

        # effects 目录扫描结果：{name: Path}
        self._effects: dict[str, Path] = {}

        # 分类信息：{category: [name, ...]}
        self._categories: dict[str, list[str]] = {}

    # ── 模板查询 ──────────────────────────────────────────

    @property
    def init_templates(self) -> dict:
        return self._templates.get('init', {})

    @property
    def evolution_templates(self) -> dict:
        return self._templates.get('evolution', {})

    @property
    def color_templates(self) -> dict:
        return self._templates.get('color', {})

    def get_template(self, category: str, name: str) -> dict | None:
        return self._templates.get(category, {}).get(name)

    def list_templates(self, category: str) -> list[str]:
        return list(self._templates.get(category, {}).keys())

    # ── Effects 目录 ──────────────────────────────────────

    def load_effects(self, effects_dir: str | Path,
                     progress_cb=None) -> 'TemplateRegistry':
        """扫描 effects/ 目录（对应 recipes.load_effects_from_dir）"""
        effects_dir = Path(effects_dir)
        self._effects = {}

        json_files = sorted(
            f for f in effects_dir.glob('*.json')
            if f.name != '_categories.json'
        )
        total = len(json_files)
        for i, fpath in enumerate(json_files):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = data.get('name', fpath.stem)
                self._effects[name] = fpath
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Registry] 跳过 {fpath.name}: {e}")
            if progress_cb:
                progress_cb(i + 1, total, fpath.name)

        # 加载分类
        cat_file = effects_dir / '_categories.json'
        if cat_file.exists():
            with open(cat_file, 'r', encoding='utf-8') as f:
                cat_data = json.load(f)
            raw_cats = cat_data.get('categories', {})
            for cat_name, cat_info in raw_cats.items():
                files = cat_info.get('files', [])
                # 将文件名反查为 effect 名
                fname_to_name = {v.name: k for k, v in self._effects.items()}
                self._categories[cat_name] = [
                    fname_to_name[f] for f in files
                    if f in fname_to_name
                ]

        return self

    @property
    def effect_names(self) -> list[str]:
        return list(self._effects.keys())

    @property
    def effect_count(self) -> int:
        return len(self._effects)

    def get_effect_path(self, name: str) -> Path | None:
        return self._effects.get(name)

    def iter_effects(self) -> Iterator[tuple[str, Path]]:
        yield from self._effects.items()

    @property
    def categories(self) -> dict[str, list[str]]:
        return self._categories

    def effects_in_category(self, cat: str) -> list[str]:
        if cat == '全部':
            return self.effect_names
        return self._categories.get(cat, [])

    def search(self, query: str) -> list[str]:
        """按关键词过滤 effect 名（大小写不敏感）"""
        q = query.strip().lower()
        if not q:
            return self.effect_names
        return [n for n in self._effects if q in n.lower()]

    # ── 配方生成（对应 recipes.generate_recipe_from_templates）────────────

    def build_recipe_config(self, init_name: str, evo_name: str,
                            color_name: str, name: str = '自定义配方',
                            w: int = 256, h: int = 192) -> ConfigComponent:
        """从三个模板名生成 ConfigComponent（不写文件）"""
        init_expr = self.init_templates.get(
            init_name, {}).get('expression', 'random()')
        evo_tpl = self.evolution_templates.get(evo_name, {})
        evo_rule = evo_tpl.get('expression', 'c + 0.2*(avg_n - c)')
        evo_vars = evo_tpl.get('variables',
                               ['c', 'sum_n', 'avg_n', 'x', 'y', 't'])
        col_tpl = self.color_templates.get(color_name, {})
        return ConfigComponent(
            name=name,
            grid_w=w,
            grid_h=h,
            init_expr=init_expr,
            evolution_rule=evo_rule,
            evolution_vars=evo_vars,
            color_red=col_tpl.get('red', 'v'),
            color_green=col_tpl.get('green', 'v'),
            color_blue=col_tpl.get('blue', 'v'),
        )
