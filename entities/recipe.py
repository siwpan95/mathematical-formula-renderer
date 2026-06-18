"""
RecipeEntity — CA 配方实体
============================
源自：engine.CARenderEngine（整个类）

ECS 视角：
    - 现有 CARenderEngine 是一个「上帝类」：它既是数据（config / grid），
      又是逻辑（_compile / step / get_color_array）。
    - 重构后，RecipeEntity 只做「Entity」角色：
        持有一组 Component，不含逻辑。
    - 所有原来在 CARenderEngine 中的方法，移入对应的 System。

Component 组合：

    RecipeEntity
    ├── ConfigComponent    — JSON 配方解析后的配置字段
    ├── GridComponent      — 网格数组 + 坐标系 + kernel
    ├── FormulaComponent   — 编译后的 init/rule/color 函数
    └── PostProcessComponent — 后处理特效状态

生命周期：
    World 创建 RecipeEntity → 注册到 World.entities
    系统切换配方时：更新 ConfigComponent → 其他 System 检测变更后重新初始化
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from components.config import ConfigComponent
from components.grid import GridComponent
from components.formula import FormulaComponent
from components.postprocess import PostProcessComponent


@dataclass
class RecipeEntity:
    """CA 配方实体 — Entity-ID + Component 集合，不含逻辑。

    对应旧代码：
        CARenderEngine.__init__()  → 分散到各 Component.__init__()
        engine.load_config()       → ConfigComponent.from_json_file()
                                     + EvolutionSystem / FormulaCompilerSystem 响应
    """

    entity_id: str = ''                        # 唯一标识符（通常用文件名）

    # ── Components ──
    config: ConfigComponent = field(default_factory=ConfigComponent)
    grid: GridComponent = field(default_factory=GridComponent)
    formula: FormulaComponent = field(default_factory=FormulaComponent)
    postfx: PostProcessComponent = field(default_factory=PostProcessComponent)

    # ── 状态标志（供 System 检测「配方已切换，需重新初始化」）──
    _dirty: bool = True       # True = 需要重新编译公式 + 重置网格

    # ─────────────────────────────────────────────────
    @classmethod
    def from_json(cls, path: str | Path) -> 'RecipeEntity':
        """从 JSON 文件创建配方实体（不触发任何计算）"""
        path = Path(path)
        cfg = ConfigComponent.from_json_file(path)
        entity_id = path.stem
        return cls(
            entity_id=entity_id,
            config=cfg,
            grid=GridComponent(w=cfg.grid_w, h=cfg.grid_h, wrap=cfg.wrap),
            formula=FormulaComponent(),
            postfx=PostProcessComponent(),
            _dirty=True,
        )

    def mark_dirty(self):
        """配方内容已变更，通知 System 需要重新初始化"""
        self._dirty = True

    @classmethod
    def from_dict(cls, config: ConfigComponent) -> 'RecipeEntity':
        """从 ConfigComponent 直接创建实体（用于测试/内存配方）"""
        return cls(
            entity_id=config.name,
            config=config,
            grid=GridComponent(w=config.grid_w, h=config.grid_h, wrap=config.wrap),
            formula=FormulaComponent(),
            postfx=PostProcessComponent(),
            _dirty=True,
        )

    def mark_clean(self):
        """System 初始化完成后调用"""
        self._dirty = False

    @property
    def is_ready(self) -> bool:
        """Entity 已完全初始化（可以参与演化）"""
        return (not self._dirty
                and self.grid.is_ready
                and self.formula.is_ready)
