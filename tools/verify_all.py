"""
验证脚本：检查所有模板的 import 和表达式编译
"""
import sys, numpy as np
sys.path.insert(0, 'D:/allin/not/OK/draw')

print('=== 1. 检查模板加载 ===')
from templates import FORMULA_TEMPLATES, print_template, list_all_templates
from templates import SUPER_PARAM_DEFAULTS, resolve_super_params
cats = list(FORMULA_TEMPLATES.keys())
print(f'模板类别: {cats}')
total = sum(len(v) for v in FORMULA_TEMPLATES.values())
print(f'总模板数: {total}')

print('\n=== 2. 检查配置字段 ===')
from components.config import ConfigComponent
cfg = ConfigComponent(
    boundary='reflective',
    topology='hexagonal',
    postprocess='invert',
)
print(f'boundary={cfg.boundary}, topology={cfg.topology}, postprocess={cfg.postprocess}')

print('\n=== 3. 检查 GridComponent.build_kernel ===')
from components.grid import GridComponent
g = GridComponent(w=10, h=10)
for topo in ['square', 'hexagonal', 'triangular']:
    for nb in ['moore', 'von_neumann', 'hex', 'radius2', 'weighted']:
        try:
            g.build_kernel(topology=topo, nb_type=nb, nb_radius=1)
            print(f'  OK: topo={topo}, nb={nb}, kernel.sum={g.kernel.sum():.4f}')
        except Exception as e:
            print(f'  FAIL: topo={topo}, nb={nb}: {e}')

print('\n=== 4. 逐表达式编译检查 ===')
# 构造测试 namespace
ns = {
    'x': np.array([[0.25, 0.75], [0.25, 0.75]]),
    'y': np.array([[0.25, 0.25], [0.75, 0.75]]),
    'c': np.array([[0.5, 0.5], [0.5, 0.5]]),
    't': 0,
    'pi': np.pi,
    'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
    'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt,
    'abs': np.abs, 'min': min, 'max': max,
    'atan2': np.arctan2, 'tanh': np.tanh,
    'clip': np.clip, 'where': np.where,
    'amin': np.amin, 'amax': np.amax,
    'sum': np.sum, 'logical_not': np.logical_not,
    'random': lambda *a: np.random.random(a[0] if a else None),
    'e': np.e, 'int': int, 'complex': complex,
    'np': np,
}

passed = 0
failed = 0
fail_list = []

for cat in cats:
    for name, t in FORMULA_TEMPLATES[cat].items():
        # 处理 init/color 类别
        if cat == 'init':
            expr = t.get('expression', '')
            if not expr:
                continue
            try:
                resolved = resolve_super_params(expr)
                code = compile(resolved, '<test>', 'eval')
                # 不实际执行，只编译
                passed += 1
            except Exception as e:
                failed += 1
                fail_list.append((cat, name, str(e)))
        elif cat == 'color':
            for ch in ['red', 'green', 'blue']:
                expr = t.get(ch, '')
                if not expr:
                    continue
                try:
                    resolved = resolve_super_params(expr)
                    code = compile(resolved, '<test>', 'eval')
                    passed += 1
                except Exception as e:
                    failed += 1
                    fail_list.append((cat, f'{name}.{ch}', str(e)))
        else:  # evolution, boundary, postprocess, topology, neighborhood
            expr = t.get('expression', '')
            variables = t.get('variables', [])
            if not expr:
                continue
            try:
                resolved = resolve_super_params(expr)
                code = compile(resolved, '<test>', 'eval')
                passed += 1
            except Exception as e:
                failed += 1
                fail_list.append((cat, name, str(e)))

print(f'编译检查: {passed} 通过, {failed} 失败')
if fail_list:
    print('\n失败列表:')
    for cat, name, err in fail_list[:20]:  # 只显示前20个
        print(f'  [{cat}] {name}: {err}')
    if len(fail_list) > 20:
        print(f'  ... 还有 {len(fail_list)-20} 个')

print('\n=== 5. 快速执行测试（init + evolution 各挑3个）===')
# 只测试 init 和 evolution 类别的表达式能否实际执行
test_ns = ns.copy()
for cat in ['init', 'evolution']:
    count = 0
    for name, t in FORMULA_TEMPLATES[cat].items():
        if count >= 3:
            break
        expr = t.get('expression', '')
        if not expr:
            continue
        try:
            resolved = resolve_super_params(expr)
            code = compile(resolved, '<test>', 'eval')
            result = eval(code, {'__builtins__': {}}, test_ns)
            # 如果能执行到这，说明没报错
            count += 1
            print(f'  OK: [{cat}] {name}')
        except Exception as e:
            print(f'  FAIL: [{cat}] {name}: {e}')

print('\n=== 验证完成 ===')
print(f'总模板: {total}, 编译通过: {passed}, 编译失败: {failed}')
