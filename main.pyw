"""
CA 渲染引擎 (ECS 架构) —— 从 effects/ 目录加载数学公式配方
==============================================================
纯 ECS 架构：
  - Components (ecs/components/)：纯数据（Grid、Formula、Config、PostProcess）
  - Systems (ecs/systems/)：纯逻辑（Evolution、Color、Render、UI）
  - Widgets (ecs/widgets/)：纯 UI 组件（Dropdown、SearchBox、HUD 等）
  - World (ecs/world.py)：调度器，持有 Entity + Systems，驱动主循环

用法：
    python main.pyw                         # 启动可视化（ECS 模式）
    python main.pyw --template init         # 打印初始化公式模板
    python main.pyw --template evolution    # 打印演化规则模板
    python main.pyw --template color        # 打印颜色映射模板
    python main.pyw --template all          # 打印全部模板
    python main.pyw --template-list         # 列出所有模板名称
    python main.pyw --generate <模板名>     # 交互式生成新配方
"""

import json
import sys
from pathlib import Path

from templates import FORMULA_TEMPLATES, print_template, list_all_templates
from recipes import generate_recipe_from_templates


def main():
    script_dir = Path(__file__).parent
    effects_dir = script_dir / 'effects'

    if '--template' in sys.argv:
        idx = sys.argv.index('--template')
        ttype = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else 'all'
        print_template(ttype)

    elif '--template-list' in sys.argv:
        list_all_templates()

    elif '--generate' in sys.argv:
        idx = sys.argv.index('--generate')
        args = sys.argv[idx + 1:]
        if len(args) >= 3:
            init, evo, col = args[0], args[1], args[2]
            name = args[3] if len(args) > 3 else f'{init}_{evo}_{col}'
            recipe = generate_recipe_from_templates(init, evo, col, name=name)
            effects_dir.mkdir(exist_ok=True)
            safe_name = name.replace(' ', '_').replace('/', '_')
            out_path = effects_dir / f'{safe_name}.json'
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(recipe, f, indent=2, ensure_ascii=False)
            print(f"[√] 已生成: {out_path}")
        else:
            print("用法: python main.pyw --generate <初始化模板> <演化模板> <颜色模板> [配方名称]")
            print("示例: python main.pyw --generate '中心脉冲' '反应扩散（Gray-Scott简化）' '绿紫双色'")

    else:
        # ── ECS 模式（默认）──
        from world import CAWorld
        world = CAWorld()
        world.run(effects_dir)


if __name__ == '__main__':
    main()
