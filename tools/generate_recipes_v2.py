"""
暴力扩容 draw/effects —— 目标 1000+ 个配方
用法: python generate_recipes_v2.py
"""
import json
import os
import random
import re

random.seed(42)

EFFECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "effects")
EFFECTS_DIR = os.path.abspath(EFFECTS_DIR)
os.makedirs(EFFECTS_DIR, exist_ok=True)


def parse_template_file(filepath):
    """从 Python 模板文件中提取所有模板字典"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    ns = {}
    exec(content, ns)
    for key, val in ns.items():
        if key.endswith("TEMPLATES") and isinstance(val, dict):
            return val
    return {}


# 加载所有模板
TEMPLATES = {}
template_files = [
    ("init.py", "init"),
    ("evolution.py", "evolution"),
    ("color.py", "color"),
    ("boundary.py", "boundary"),
    ("postprocess.py", "postprocess"),
    ("topology.py", "topology"),
    ("neighborhood.py", "neighborhood"),
]
for fname, key in template_files:
    fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", fname)
    fpath = os.path.abspath(fpath)
    if os.path.exists(fpath):
        TEMPLATES[key] = parse_template_file(fpath)
        print(f"  加载 {key}: {len(TEMPLATES[key])} 个")
    else:
        TEMPLATES[key] = {}

INIT_NAMES       = sorted(TEMPLATES["init"].keys())
EVOLUTION_NAMES = sorted(TEMPLATES["evolution"].keys())
COLOR_NAMES     = sorted(TEMPLATES["color"].keys())

print(f"模板总计: init={len(INIT_NAMES)}, evolution={len(EVOLUTION_NAMES)}, "
      f"color={len(COLOR_NAMES)}")

POSTPROCESS_EFFECTS = ["none", "bloom", "edge", "motion_trail", "invert", "vignette"]

GRID_SIZES = [
    (200, 150), (256, 192), (300, 200), (400, 300),
    (512, 384), (150, 150), (100, 100), (64, 64),
    (128, 128), (180, 180), (240, 180), (320, 240),
    (600, 400), (80, 60), (160, 120),
]

_name_prefixes = [
    "幻境", "星云", "涟漪", "火焰", "冰晶", "迷宫", "脉冲",
    "漩涡", "极光", "量子", "混沌", "分形", "波函数", "湍流",
    "扩散", "反应", "激发", "螺旋", "脉动", "谐振", "潮汐",
    "霜花", "熔岩", "彩虹", "迷雾", "雷暴", "电浆", "虚空",
    "光辉", "深渊", "梦境", "炼狱", "天堂", "风暴", "微光",
    "裂变", "纠缠", "坍缩", "膨胀", "震荡", "漂移",
    "涌现", "突变", "进化", "虫洞", "时光", "记忆", "回声",
]
_name_suffixes = [
    "之舞", "之歌", "之谜", "之梦", "之光", "之影", "之变",
    "之旋", "之浪", "之花", "之森", "之海", "之山", "之云",
    "初现", "绽放", "消散", "轮回", "永恒", "瞬间", "余辉",
]

_next_id = 1000


def make_recipe(init_name, evo_name, color_name,
                grid_size=None, cycle_steps=None,
                postprocess="none", suffix=""):
    global _next_id
    init_tpl  = TEMPLATES["init"][init_name]
    evo_tpl   = TEMPLATES["evolution"][evo_name]
    color_tpl = TEMPLATES["color"][color_name]

    w, h = grid_size or random.choice(GRID_SIZES)
    cycle = cycle_steps
    if cycle is None:
        cycle = random.choice([0, 200, 300, 500, 600, 800, 1000, 1200, 1500, 2000])

    recipe = {
        "name": f"{init_name}_{evo_name}_{color_name}{suffix}",
        "grid": {
            "width":  w,
            "height": h,
            "wrap":   random.choice([True, False]),
            "initial": {
                "type":       "formula",
                "expression": init_tpl["expression"]
            }
        },
        "evolution": {
            "rule":      evo_tpl["expression"],
            "variables": evo_tpl.get("variables", ["c", "avg_n"])
        },
        "color": {
            "red":   color_tpl.get("red",   "v"),
            "green": color_tpl.get("green", "v"),
            "blue":  color_tpl.get("blue",  "v")
        },
        "cycle": {"steps": cycle},
        "id": _next_id
    }
    _next_id += 1

    if postprocess and postprocess != "none":
        recipe["postprocess"] = {"effect": postprocess}

    return recipe


def safe_filename(name):
    s = re.sub(r'[\\/*?:"<>|]', "_", name)
    s = s.strip("_")
    return s[:80]


def save_recipe(recipe):
    fname = safe_filename(recipe["name"] + ".json")
    fpath = os.path.join(EFFECTS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(recipe, f, ensure_ascii=False, indent=2)
    return fpath


def generate():
    existing_keys = set()
    count = 0

    # ── 阶段 1: 基础组合 ──────────────────────────────────────
    print("阶段1: 基础组合...")
    for evo_name in EVOLUTION_NAMES:
        n_init  = min(len(INIT_NAMES), random.randint(4, 10))
        n_color = min(len(COLOR_NAMES), random.randint(3, 7))
        chosen_inits  = random.sample(INIT_NAMES, n_init)
        chosen_colors = random.sample(COLOR_NAMES, n_color)

        for init_name in chosen_inits:
            for color_name in chosen_colors:
                pp = random.choice(POSTPROCESS_EFFECTS)
                grid = random.choice(GRID_SIZES)
                key = (init_name, evo_name, color_name, pp, grid)
                if key in existing_keys:
                    continue
                existing_keys.add(key)

                recipe = make_recipe(init_name, evo_name, color_name,
                                     grid_size=grid, postprocess=pp)
                save_recipe(recipe)
                count += 1
                if count % 200 == 0:
                    print(f"  已生成 {count} 条...")
        if count >= 600:
            break
    print(f"阶段1完成: {count} 条")

    # ── 阶段 2: 网格尺寸变体 ─────────────────────────────────
    print("阶段2: 网格尺寸变体...")
    seed_keys = [k for k in existing_keys
                 if isinstance(k, tuple) and len(k) >= 5]
    random.shuffle(seed_keys)
    for key in seed_keys[:300]:
        if not isinstance(key, tuple) or len(key) < 5:
            continue
        init_name, evo_name, color_name, pp, grid = key[:5]
        for new_grid in random.sample(GRID_SIZES, k=random.randint(1, 2)):
            if new_grid == grid:
                continue
            new_key = (init_name, evo_name, color_name, pp, new_grid)
            if new_key in existing_keys:
                continue
            existing_keys.add(new_key)
            recipe = make_recipe(init_name, evo_name, color_name,
                                 grid_size=new_grid, postprocess=pp)
            save_recipe(recipe)
            count += 1
            if count >= 1000:
                break
        if count >= 1000:
            break
    print(f"阶段2完成: {count} 条")

    # ── 阶段 3: 后处理全遍历（精选组合）────────────────────
    print("阶段3: 后处理全遍历...")
    random.shuffle(seed_keys)
    scanned = 0
    for key in seed_keys:
        if not isinstance(key, tuple) or len(key) < 5:
            continue
        init_name, evo_name, color_name, pp0, grid = key[:5]
        for pp in POSTPROCESS_EFFECTS:
            new_key = (init_name, evo_name, color_name, pp, grid, "pp")
            if new_key in existing_keys:
                continue
            existing_keys.add(new_key)
            recipe = make_recipe(init_name, evo_name, color_name,
                                 grid_size=grid, postprocess=pp)
            save_recipe(recipe)
            count += 1
        scanned += 1
        if scanned >= 80:
            break
    print(f"阶段3完成: {count} 条")

    # ── 阶段 4: cycle 步数变体 ───────────────────────────────
    print("阶段4: cycle 步数变体...")
    cycles = [0, 100, 250, 400, 500, 750, 1000, 1500, 2000, 3000, 5000]
    random.shuffle(seed_keys)
    for key in seed_keys[:200]:
        if not isinstance(key, tuple) or len(key) < 5:
            continue
        init_name, evo_name, color_name, pp, grid = key[:5]
        for new_cycle in random.sample(cycles, k=2):
            new_key = (init_name, evo_name, color_name, pp, grid, new_cycle, "c")
            if new_key in existing_keys:
                continue
            existing_keys.add(new_key)
            recipe = make_recipe(init_name, evo_name, color_name,
                                 grid_size=grid, cycle_steps=new_cycle,
                                 postprocess=pp)
            save_recipe(recipe)
            count += 1
    print(f"阶段4完成: {count} 条")

    # ── 阶段 5: 中文命名配方 ──────────────────────────────────
    print("阶段5: 中文命名配方...")
    used_chinese_names = set()
    for i in range(500):
        init_name  = random.choice(INIT_NAMES)
        evo_name   = random.choice(EVOLUTION_NAMES)
        color_name = random.choice(COLOR_NAMES)
        pp         = random.choice(POSTPROCESS_EFFECTS)
        grid       = random.choice(GRID_SIZES)
        cycle      = random.choice([0, 300, 500, 800, 1000, 2000])

        attempts = 0
        while attempts < 20:
            prefix = random.choice(_name_prefixes)
            suffix = random.choice(_name_suffixes)
            chinese_name = prefix + suffix
            if chinese_name not in used_chinese_names:
                used_chinese_names.add(chinese_name)
                break
            attempts += 1
        else:
            chinese_name = f"{random.choice(_name_prefixes)}{i}"

        recipe = make_recipe(init_name, evo_name, color_name,
                             grid_size=grid, cycle_steps=cycle,
                             postprocess=pp)
        recipe["name"] = chinese_name
        save_recipe(recipe)
        count += 1

    print(f"阶段5完成: {count} 条")

    # ── 阶段 6: 随机混合（填满到 1200+）─────────────────────
    print("阶段6: 随机混合补齐...")
    for i in range(200):
        init_name  = random.choice(INIT_NAMES)
        evo_name   = random.choice(EVOLUTION_NAMES)
        color_name = random.choice(COLOR_NAMES)
        pp         = random.choice(POSTPROCESS_EFFECTS)
        grid       = random.choice(GRID_SIZES)
        cycle      = random.choice([0, 200, 500, 1000, 2000])
        suffix     = f"_v{i}" if random.random() < 0.5 else ""

        recipe = make_recipe(init_name, evo_name, color_name,
                             grid_size=grid, cycle_steps=cycle,
                             postprocess=pp, suffix=suffix)
        save_recipe(recipe)
        count += 1

    print(f"阶段6完成: {count} 条")
    return count


if __name__ == "__main__":
    print("=" * 60)
    print("CA Render Engine —— 配方暴力扩容脚本")
    print("=" * 60)
    n = generate()
    print("=" * 60)
    print(f"共生成 {n} 个配方，保存在:\n  {EFFECTS_DIR}")
    total = len([f for f in os.listdir(EFFECTS_DIR) if f.endswith(".json")])
    print(f"effects/ 目录共有 {total} 个 JSON 文件")
    print("=" * 60)
