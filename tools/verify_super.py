"""
验证 templates.py 中的超级公式
"""
import sys
import math

sys.path.insert(0, 'D:/allin/not/OK/draw')
from templates import FORMULA_TEMPLATES, SUPER_PARAM_DEFAULTS, resolve_super_params

def check_super_formula(category, name, template):
    """检查超级公式的语法正确性"""
    expr_fields = []
    if category == 'init':
        expr_fields = [('expression', template['expression'])]
    elif category == 'evolution':
        expr_fields = [('expression', template['expression'])]
    else:  # color
        expr_fields = [('red', template['red']), ('green', template['green']), ('blue', template['blue'])]

    for field_name, expr in expr_fields:
        try:
            resolved = resolve_super_params(expr)
            # 测试 eval（提供必要变量）
            test_vars = {
                'x': 0.5, 'y': 0.5,
                'c': 0.5, 'sum_n': 2.0, 'avg_n': 0.5,
                'neighbors': [0.5, 0.5, 0.5, 0.5],
                't': 0, 'v': 0.5,
                'random': lambda: 0.5,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'sqrt': math.sqrt, 'exp': math.exp, 'log': math.log,
                'atan2': math.atan2, 'pi': math.pi,
                'abs': abs, 'int': int, 'min': min, 'max': max,
                'clip': lambda x, a, b: max(a, min(b, x)),
            }
            result = eval(resolved, {"__builtins__": {}}, test_vars)
            print(f"  ✅ {category}/{name}.{field_name}: OK (result={result:.3f})")
            return True
        except Exception as e:
            print(f"  ❌ {category}/{name}.{field_name}: ERROR - {e}")
            print(f"     表达式: {expr}")
            print(f"     解析后: {resolved}")
            return False

print("=" * 60)
print("验证超级公式")
print("=" * 60)

super_count = 0
total_count = 0
errors = 0

for cat in ['init', 'evolution', 'color']:
    for name, t in FORMULA_TEMPLATES[cat].items():
        total_count += 1
        if name.startswith('Super_'):
            super_count += 1
            if not check_super_formula(cat, name, t):
                errors += 1

print("=" * 60)
print(f"总计: {total_count} 个模板，其中 {super_count} 个超级公式")
print(f"错误: {errors} 个")
print("=" * 60)

# 列出所有超级公式
print("\n所有超级公式:")
for cat in ['init', 'evolution', 'color']:
    supers = [n for n in FORMULA_TEMPLATES[cat] if n.startswith('Super_')]
    print(f"  [{cat.upper()}] {len(supers)} 个: {supers}")
