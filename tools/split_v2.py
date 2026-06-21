"""
Split templates.py into separate files by category.
Run from D:/allin/not/OK/draw
"""
import sys
import os

base = r'D:\allin\not\OK\draw'
os.chdir(base)

# Execute templates.py to get the dictionaries
with open('templates.py', 'r', encoding='utf-8') as f:
    code = f.read()

ns = {}
exec(code, ns)
FORMULA_TEMPLATES = ns['FORMULA_TEMPLATES']
SUPER_PARAM_DEFAULTS = ns['SUPER_PARAM_DEFAULTS']

os.makedirs('templates', exist_ok=True)

# ---------- helpers ----------
def dict_to_src(d, indent=0):
    """Convert a dict to Python source string (no repr, proper format)."""
    sp = ' ' * indent
    sp1 = ' ' * (indent + 4)
    lines = []
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f'{sp}"{k}": {{')
            lines.append(dict_to_src(v, indent + 4))
            lines.append(f'{sp}}},')
        elif isinstance(v, list):
            lines.append(f'{sp}"{k}": {v},')
        else:
            lines.append(f'{sp}"{k}": {repr(v)},')
    return '\n'.join(lines)

def write_category(filepath, var_name, templates):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'"""{var_name} (由 templates.py 自动拆分生成)."""\n\n')
        f.write(f'{var_name} = {{\n')
        f.write(dict_to_src(templates, 0))
        f.write('\n}\n')

# ---------- write 3 category files ----------
write_category(
    os.path.join('templates', 'init.py'),
    'INIT_TEMPLATES',
    FORMULA_TEMPLATES['init']
)
print('  written: templates/init.py')

write_category(
    os.path.join('templates', 'evolution.py'),
    'EVOLUTION_TEMPLATES',
    FORMULA_TEMPLATES['evolution']
)
print('  written: templates/evolution.py')

write_category(
    os.path.join('templates', 'color.py'),
    'COLOR_TEMPLATES',
    FORMULA_TEMPLATES['color']
)
print('  written: templates/color.py')

# ---------- write super_params.py ----------
with open(os.path.join('templates', 'super_params.py'), 'w', encoding='utf-8') as f:
    f.write('"""超级公式参数默认值 & 解析函数."""\n\n')
    # Write the dict in a clean format
    f.write('SUPER_PARAM_DEFAULTS = {\n')
    for k, v in SUPER_PARAM_DEFAULTS.items():
        f.write(f'    "{k}": {v},\n')
    f.write('}\n\n')

    f.write('def resolve_super_params(expr: str) -> str:\n')
    f.write('    """将超级公式参数名替换为默认数值，使表达式可以独立编译执行。"""\n')
    f.write('    import re\n')
    f.write('    for name, value in SUPER_PARAM_DEFAULTS.items():\n')
    f.write('        expr = re.sub(r"\\b" + re.escape(name) + r"\\b", str(value), expr)\n')
    f.write('    return expr\n')

print('  written: templates/super_params.py')

# ---------- write __init__.py ----------
with open(os.path.join('templates', '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('"""Formula templates package (自动生成)."""\n')
    f.write('from .init import INIT_TEMPLATES\n')
    f.write('from .evolution import EVOLUTION_TEMPLATES\n')
    f.write('from .color import COLOR_TEMPLATES\n')
    f.write('from .super_params import SUPER_PARAM_DEFAULTS, resolve_super_params\n\n')
    f.write('FORMULA_TEMPLATES = {\n')
    f.write('    "init": INIT_TEMPLATES,\n')
    f.write('    "evolution": EVOLUTION_TEMPLATES,\n')
    f.write('    "color": COLOR_TEMPLATES,\n')
    f.write('}\n')

print('  written: templates/__init__.py')
print('Split complete!')
