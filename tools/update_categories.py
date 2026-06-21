"""
自动更新 _categories.json
根据 effect 文件名和 name 字段自动分类
"""
import json
from pathlib import Path

EFFECTS_DIR = Path(__file__).parent / 'effects'

# 分类规则：(category_name, keywords_in_filename)
CATEGORY_RULES = [
    ('超级公式', ['超级公式']),
    ('多公式组合', ['多公式', '三init', '三evol', '四阶段', '混合']),
    ('反应扩散_图灵斑图', ['反应扩散', 'Gray-Scott', 'Schnakenberg', 'Cahn-Hilliard', 'Turing', '相分离']),
    ('激发介质_振荡波', ['BZ', '激发', 'FHN', 'Ginzburg', '孤子', 'Swift-Hohenberg']),
    ('经典生命游戏', ['GoL', 'Game of Life', 'SmoothLife', 'Lenia', 'life_smooth']),
    ('流体力学_湍流', ['Burgers', '瑞利', '湍流', '水面', '涡旋', '驻波', '多次谐波']),
    ('生态_种群动力学', ['Lotka', 'SIRS', '捕食', '趋化', '竞争', '三态循环']),
    ('相变_晶体生长', ['固化', 'DLA', '雪花', 'Voronoi破裂']),
    ('几何_结构图案', ['Kagome', '三角形', '六边形', '准晶体', '各向异性']),
    ('混沌_分形', ['Mandelbrot', '分形', '超离散', 'Kuramoto', 'Fisher', '混沌']),
    ('神经动力学', ['Wilson-Cowan', '神经']),
    ('界面动力学', ['曲率', '相位场']),
    ('波传播', ['波传播', 'BZ_Aurora', '螺旋_BZ']),
    ('渗流_生长', ['渗流', 'Eden', 'DLA']),
    ('组合配方_精选', []),  # 默认分类
]

def auto_categorize():
    files = [f for f in EFFECTS_DIR.glob('*.json') if f.name != '_categories.json']

    categories = {cat: {'desc': cat, 'files': []} for cat, _ in CATEGORY_RULES}
    uncategorized = []

    for f in files:
        assigned = False
        fname = f.stem
        for cat, keywords in CATEGORY_RULES:
            if any(kw in fname for kw in keywords):
                categories[cat]['files'].append(f.name)
                assigned = True
                break
        if not assigned:
            uncategorized.append(f.name)

    # 把未分类的放到"组合配方_精选"
    categories['组合配方_精选']['files'].extend(uncategorized)

    # 构建输出
    output = {
        'description': 'effects 配方分类清单 —— 按数学模型/物理系统/组合分类',
        'version': '3.0',
        'categories': {}
    }
    for cat, _ in CATEGORY_RULES:
        if categories[cat]['files']:
            output['categories'][cat] = {
                'desc': categories[cat]['desc'],
                'files': sorted(categories[cat]['files'])
            }

    with open(EFFECTS_DIR / '_categories.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'分类完成：{len(files)} 个 effects')
    for cat in output['categories']:
        print(f'  {cat}: {len(output["categories"][cat]["files"])} 个')

if __name__ == '__main__':
    auto_categorize()
