"""Formula templates package (自动生成)."""
from .init import INIT_TEMPLATES
from .evolution import EVOLUTION_TEMPLATES
from .color import COLOR_TEMPLATES
from .boundary import BOUNDARY_TEMPLATES
from .postprocess import POSTPROCESS_TEMPLATES
from .topology import TOPOLOGY_TEMPLATES
from .neighborhood import NEIGHBORHOOD_TEMPLATES
from .super_params import SUPER_PARAM_DEFAULTS, resolve_super_params

FORMULA_TEMPLATES = {
    "init": INIT_TEMPLATES,
    "evolution": EVOLUTION_TEMPLATES,
    "color": COLOR_TEMPLATES,
    "boundary": BOUNDARY_TEMPLATES,
    "postprocess": POSTPROCESS_TEMPLATES,
    "topology": TOPOLOGY_TEMPLATES,
    "neighborhood": NEIGHBORHOOD_TEMPLATES,
}


def list_all_templates():
    """打印全部模板名称（按类别）"""
    for category, templates in FORMULA_TEMPLATES.items():
        print(f"\n=== {category} ({len(templates)} 个) ===")
        for name in sorted(templates.keys()):
            entry = templates[name]
            flags = []
            if 'super' in entry.get('description', '').lower() or '超级' in entry.get('description', ''):
                flags.append('[超级公式]')
            print(f"  {name}  {' '.join(flags)}")


def print_template(ttype='all'):
    """打印指定类别的模板（格式化输出）"""
    if ttype == 'all':
        categories = FORMULA_TEMPLATES.keys()
    elif ttype in FORMULA_TEMPLATES:
        categories = [ttype]
    else:
        print(f"未知类别: {ttype}")
        return

    for cat in categories:
        print(f"\n{'='*60}")
        print(f"  {cat.upper()} 模板（{len(FORMULA_TEMPLATES[cat])} 个）")
        print(f"{'='*60}")
        for name, entry in sorted(FORMULA_TEMPLATES[cat].items()):
            desc = entry.get('description', '')
            expr = entry.get('expression', '')
            red = entry.get('red', '')
            green = entry.get('green', '')
            blue = entry.get('blue', '')
            notes = entry.get('notes', '')
            variables = entry.get('variables', [])
            print(f"\n  【{name}】")
            print(f"    描述: {desc}")
            if expr:
                print(f"    公式: {expr[:80]}{'...' if len(expr) > 80 else ''}")
            if red:
                print(f"    颜色: R={red[:40]}... G={green[:40]}... B={blue[:40]}...")
            if variables:
                print(f"    变量: {variables}")
            if notes:
                print(f"    说明: {notes}")
