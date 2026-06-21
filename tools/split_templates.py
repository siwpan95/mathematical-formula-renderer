"""
Split templates.py into separate files by category.
Run from D:/allin/not/OK/draw/
"""
import os
import re

base = r'D:\allin\not\OK\draw'
templates_py = os.path.join(base, 'templates.py')
out_dir = os.path.join(base, 'templates')

os.makedirs(out_dir, exist_ok=True)

with open(templates_py, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the FORMULA_TEMPLATES dict as text
# Find start: "FORMULA_TEMPLATES = {"
# Find end: the matching closing } for the whole dict
start = content.index('FORMULA_TEMPLATES = {')
# Find the helpers section: "# =====" after the dict
helpers_start = content.index('\n\n# ===', start)
formulas_text = content[start:helpers_start].strip()
# Now we have FORMULA_TEMPLATES = { ... } as text
# Parse it by executing in a safe namespace
ns = {}
exec(content[:helpers_start], ns)
FORMULA_TEMPLATES = ns['FORMULA_TEMPLATES']
SUPER_PARAM_DEFAULTS = ns['SUPER_PARAM_DEFAULTS']
resolve_src = content[content.index('def resolve_super_params'):content.index('\n\ndef ', content.index('def resolve_super_params')+1)]
# Actually, let's just get the full helper section
helpers_section = content[helpers_start:].strip()

def format_template_dict(data, indent=4):
    """Format a template dict as clean Python source."""
    lines = []
    sp = ' ' * indent
    for name, t in data.items():
        lines.append(f'{sp}"{name}": {{')
        for k, v in t.items():
            lines.append(f'{sp}    "{k}": {repr(v)},')
        lines.append(f'{sp}}},')
    return '\n'.join(lines)

# Write init.py
with open(os.path.join(out_dir, 'init.py'), 'w', encoding='utf-8') as f:
    f.write('"""Init templates (初始条件)."""\n\n')
    f.write('INIT_TEMPLATES = {\n')
    f.write(format_template_dict(FORMULA_TEMPLATES['init']))
    f.write('\n}\n')

# Write evolution.py
with open(os.path.join(out_dir, 'evolution.py'), 'w', encoding='utf-8') as f:
    f.write('"""Evolution templates (演化规则)."""\n\n')
    f.write('EVOLUTION_TEMPLATES = {\n')
    f.write(format_template_dict(FORMULA_TEMPLATES['evolution']))
    f.write('\n}\n')

# Write color.py
with open(os.path.join(out_dir, 'color.py'), 'w', encoding='utf-8') as f:
    f.write('"""Color templates (颜色映射)."""\n\n')
    f.write('COLOR_TEMPLATES = {\n')
    f.write(format_template_dict(FORMULA_TEMPLATES['color']))
    f.write('\n}\n')

# Write super_params.py
with open(os.path.join(out_dir, 'super_params.py'), 'w', encoding='utf-8') as f:
    f.write('"""Super formula parameter defaults and resolver."""\n\n')
    f.write(f'SUPER_PARAM_DEFAULTS = {repr(SUPER_PARAM_DEFAULTS)}\n\n')
    f.write('def resolve_super_params(expr: str) -> str:\n')
    f.write('    """将超级公式参数名替换为默认数值，使表达式可以独立编译执行。"""\n')
    f.write('    import re\n')
    f.write('    for name, value in SUPER_PARAM_DEFAULTS.items():\n')
    f.write('        expr = re.sub(r"\\b" + re.escape(name) + r"\\b", str(value), expr)\n')
    f.write('    return expr\n')

# Write __init__.py
with open(os.path.join(out_dir, '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('"""Formula templates package."""\n\n')
    f.write('from .init import INIT_TEMPLATES\n')
    f.write('from .evolution import EVOLUTION_TEMPLATES\n')
    f.write('from .color import COLOR_TEMPLATES\n')
    f.write('from .super_params import SUPER_PARAM_DEFAULTS, resolve_super_params\n\n')
    f.write('FORMULA_TEMPLATES = {\n')
    f.write('    "init": INIT_TEMPLATES,\n')
    f.write('    "evolution": EVOLUTION_TEMPLATES,\n')
    f.write('    "color": COLOR_TEMPLATES,\n')
    f.write('}\n\n')
    f.write('\n# Helpers (kept for compatibility)\n')
    f.write('def print_template(ttype, name=None):\n')
    f.write('    """Print template(s) by category or single template."""\n')
    f.write('    from . import FORMULA_TEMPLATES\n')
    f.write('    if name is not None:\n')
    f.write('        t = FORMULA_TEMPLATES[ttype][name]\n')
    f.write('        print(f"\\n{"=" * 60}")\n')
    f.write('        print(f"  [{ttype.upper()}] {name}")\n')
    f.write('        print(f"\\n{"=" * 60}")\n')
    f.write('        print(f"  描述: {t[\"description\"]}")\n')
    f.write('        if ttype == "init":\n')
    f.write('            print(f"  表达式: {t[\"expression\"]}")\n')
    f.write('        elif ttype == "evolution":\n')
    f.write('            print(f"  表达式: {t[\"expression\"]}")\n')
    f.write('            print(f"  变量: {t[\"variables\"]}")\n')
    f.write('        else:\n')
    f.write('            print(f"  红(R): {t[\"red\"]}")\n')
    f.write('            print(f"  绿(G): {t[\"green\"]}")\n')
    f.write('            print(f"  蓝(B): {t[\"blue\"]}")\n')
    f.write('        print(f"  备注: {t[\"notes\"]}")\n')
    f.write('    else:\n')
    f.write('        from . import FORMULA_TEMPLATES\n')
    f.write('        categories = ["init", "evolution", "color"] if ttype == "all" else [ttype]\n')
    f.write('        for cat in categories:\n')
    f.write('            templates = FORMULA_TEMPLATES[cat]\n')
    f.write('            print(f"\\n{"=" * 60}\\n  [{cat.upper()}] 共 {len(templates)} 个模板\\n{"=" * 60}")\n')
    f.write('            for nm, t in templates.items():\n')
    f.write('                print(f"\\n  --- {nm} ---")\n')
    f.write('                print(f"  描述: {t[\"description\"]}")\n')
    f.write('                if cat == "init":\n')
    f.write('                    print(f"  表达式: {t[\"expression\"]}")\n')
    f.write('                elif cat == "evolution":\n')
    f.write('                    print(f"  表达式: {t[\"expression\"]}")\n')
    f.write('                    print(f"  变量: {t[\"variables\"]}")\n')
    f.write('                else:\n')
    f.write('                    print(f"  红(R): {t[\"red\"]}")\n')
    f.write('                    print(f"  绿(G): {t[\"green\"]}")\n')
    f.write('                    print(f"  蓝(B): {t[\"blue\"]}")\n')
    f.write('                print(f"  备注: {t[\"notes\"]}")\n\n')
    f.write('def list_all_templates():\n')
    f.write('    """列出所有模板名称，按类别分组。"""\n')
    f.write('    from . import FORMULA_TEMPLATES\n')
    f.write('    print(f"\\n{"=" * 60}\\n  公式模板库 — 共 {sum(len(FORMULA_TEMPLATES[c]) for c in FORMULA_TEMPLATES)} 个模板")\n')
    f.write('    print(f"\\n{"=" * 60}\\n  公式模板库 — 共 {sum(len(FORMULA_TEMPLATES[c]) for c in FORMULA_TEMPLATES)} 个模板")\n')
    f.write('    for cat in ["init", "evolution", "color"]:\n')
    f.write('        templates = FORMULA_TEMPLATES[cat]\n')
    f.write('        print(f"\\n  [{cat.upper()}] {len(templates)} 个:")\n')
    f.write('        for i, (name, t) in enumerate(templates.items()):\n')
    f.write('            print(f"    {i+1:3d}. {name:<35s} {t[\"description\"]}")\n\n')
    f.write('if __name__ == "__main__":\n')
    f.write('    list_all_templates()\n')

print("Split complete!")
print(f"Files written to: {out_dir}")
for fn in os.listdir(out_dir):
    fp = os.path.join(out_dir, fn)
    print(f"  {fn}: {os.path.getsize(fp)} bytes")
