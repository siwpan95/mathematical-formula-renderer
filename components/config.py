"""
ConfigComponent — 配方配置数据容器
===================================
源自：engine.CARenderEngine.load_config()

职责：
    持有从 JSON 配方解析出的所有配置字段（只读数据）。
    不包含任何计算逻辑。System 负责读取本组件并据此初始化其他组件。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass
class ConfigComponent:
    """来自 JSON 配方的原始配置数据。

    属性名与配方 JSON 字段一一对应，保持无损传递。

    原始来源（engine.py 中散落在 load_config 的各处赋值）：
        self.w, self.h, self.wrap              → grid_w, grid_h, wrap
        init_expr                               → init_expr
        ev['rule'], ev['variables']             → evolution_rule, evolution_vars
        col['red/green/blue']                   → color_red/green/blue
        nb['radius'], nb['type']                → nb_radius, nb_type
        tick['fps'], tick['steps_per_frame']    → fps, steps_per_frame
        cycle['steps']                          → cycle_steps
        config['name'], config['description']   → name, description
    """

    # ── 元数据 ──
    recipe_id: int = 0             # 配方唯一编号（1 ~ N）
    name: str = '未命名'
    description: str = ''
    version: str = '1.0'
    source_path: str = ''          # 来源 JSON 文件路径（用于热重载）

    # ── 网格 ──
    grid_w: int = 256
    grid_h: int = 192
    wrap: bool = True
    boundary: str = 'periodic'  # 边界条件类型
    topology: str = 'square'   # 网格拓扑类型

    # ── 初始化公式 ──
    init_expr: str = 'random()'

    # ── 演化规则 ──
    evolution_rule: str = 'c + 0.2*(avg_n - c)'
    evolution_vars: list[str] = field(
        default_factory=lambda: ['c', 'sum_n', 'avg_n', 'x', 'y', 't'])

    # ── 颜色映射 ──
    color_red: str = 'v'
    color_green: str = 'v'
    color_blue: str = 'v'
    postprocess: str = 'none'  # 新增：后处理特效

    # ── 邻域 ──
    nb_type: str = 'moore'
    nb_radius: int = 1

    # ── Tick ──
    fps: int = 30
    steps_per_frame: int = 1

    # ── 循环 ──
    cycle_steps: int = 0           # 0 = 不循环

    # ── 原始 dict（保留完整，便于 System 访问扩展字段）──
    raw: dict[str, Any] = field(default_factory=dict)

    # ─────────────────────────────────────────────────
    @classmethod
    def from_json_file(cls, path: str | Path) -> 'ConfigComponent':
        """从 JSON 文件加载（对应 engine.load_config）"""
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data, source_path=str(path))

    @classmethod
    def from_dict(cls, data: dict, source_path: str = '') -> 'ConfigComponent':
        """从已解析的 dict 构建（用于测试或内存配方）"""
        from templates import resolve_super_params

        g = data.get('grid', {})
        ev = data.get('evolution', {})
        col = data.get('color', {})
        nb = data.get('neighborhood', {})
        tick = data.get('tick', {})
        cycle = data.get('cycle', {})

        return cls(
            recipe_id=data.get('id', 0),
            name=data.get('name', '未命名'),
            description=data.get('description', ''),
            version=str(data.get('version', '1.0')),
            source_path=source_path,

            grid_w=g.get('width', 256),
            grid_h=g.get('height', 192),
            wrap=g.get('wrap', True),
            boundary=g.get('boundary', 'periodic'),
            topology=g.get('topology', 'square'),

            init_expr=resolve_super_params(
                g.get('initial', {}).get('expression', 'random()')),

            evolution_rule=resolve_super_params(
                ev.get('rule', 'c + 0.2*(avg_n - c)')),
            evolution_vars=ev.get('variables',
                                  ['c', 'sum_n', 'avg_n', 'x', 'y', 't']),

            color_red=resolve_super_params(col.get('red', 'v')),
            color_green=resolve_super_params(col.get('green', 'v')),
            color_blue=resolve_super_params(col.get('blue', 'v')),
            postprocess=col.get('postprocess', 'none'),  # 新增

            nb_type=nb.get('type', 'moore'),
            nb_radius=nb.get('radius', 1),

            fps=tick.get('fps', 30),
            steps_per_frame=tick.get('steps_per_frame', 1),

            cycle_steps=cycle.get('steps', 0),

            raw=data,
        )

    def to_dict(self) -> dict:
        """序列化回 JSON-compatible dict（用于保存/导出）"""
        return {
            'id': self.recipe_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'grid': {
                'width': self.grid_w,
                'height': self.grid_h,
                'wrap': self.wrap,
                'boundary': self.boundary,
                'topology': self.topology,
                'initial': {'type': 'formula', 'expression': self.init_expr},
            },
            'evolution': {
                'rule': self.evolution_rule,
                'variables': self.evolution_vars,
            },
            'color': {
                'mode': 'per_channel',
                'red': self.color_red,
                'green': self.color_green,
                'blue': self.color_blue,
                'postprocess': self.postprocess,  # 新增
            },
            'neighborhood': {'type': self.nb_type, 'radius': self.nb_radius},
            'tick': {'fps': self.fps, 'steps_per_frame': self.steps_per_frame},
            'cycle': {'steps': self.cycle_steps},
        }
