"""
暴力扩容 draw/effects —— 目标 2500+ 个配方（修掉同名覆盖 bug）
用法: python generate_recipes_v3.py
"""
import json
import os
import random
import re

random.seed(42)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
EFFECTS_DIR = os.path.join(BASE_DIR, "..", "effects")
EFFECTS_DIR = os.path.abspath(EFFECTS_DIR)
os.makedirs(EFFECTS_DIR, exist_ok=True)


def parse_template_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    ns = {}
    exec(content, ns)
    for key, val in ns.items():
        if key.endswith("TEMPLATES") and isinstance(val, dict):
            return val
    return {}


# ── 加载模板 ──────────────────────────────────────────────────────
print("加载模板...")
TEMPLATES = {}
for fname, key in [
    ("init.py",          "init"),
    ("evolution.py",     "evolution"),
    ("color.py",         "color"),
    ("boundary.py",      "boundary"),
    ("postprocess.py",   "postprocess"),
    ("topology.py",      "topology"),
    ("neighborhood.py",  "neighborhood"),
]:
    fpath = os.path.join(BASE_DIR, "..", "templates", fname)
    fpath = os.path.abspath(fpath)
    if os.path.exists(fpath):
        TEMPLATES[key] = parse_template_file(fpath)
    else:
        TEMPLATES[key] = {}

INIT_NAMES       = sorted(TEMPLATES["init"].keys())
EVOLUTION_NAMES = sorted(TEMPLATES["evolution"].keys())
COLOR_NAMES     = sorted(TEMPLATES["color"].keys())
print(f"  模板: init={len(INIT_NAMES)}, evolution={len(EVOLUTION_NAMES)}, "
      f"color={len(COLOR_NAMES)}")

POSTPROCESS_LIST = ["none", "bloom", "edge", "motion_trail", "invert", "vignette"]
GRID_SIZES = [
    (64, 64),   (100, 100),  (128, 128),  (150, 150),  (180, 180),
    (200, 150), (256, 192),  (300, 200),  (320, 240),  (400, 300),
    (512, 384), (600, 400),  (80, 60),    (160, 120),  (240, 180),
]
CYCLES = [0, 100, 200, 300, 500, 600, 800, 1000, 1200, 1500, 2000, 3000, 5000]

_NAME_PREFIXES = [
    "幻境", "星云", "涟漪", "火焰", "冰晶", "迷宫", "脉冲",
    "漩涡", "极光", "量子", "混沌", "分形", "波函数", "湍流",
    "扩散", "反应", "激发", "螺旋", "脉动", "谐振", "潮汐",
    "霜花", "熔岩", "彩虹", "迷雾", "雷暴", "电浆", "虚空",
    "光辉", "深渊", "梦境", "炼狱", "天堂", "风暴", "微光",
    "裂变", "纠缠", "坍缩", "膨胀", "震荡", "漂移",
    "涌现", "突变", "进化", "虫洞", "时光", "记忆", "回声",
    "极夜", "晨曦", "黄昏", "星尘", "银河", "黑洞", "中子",
    "等离子", "超流体", "玻色", "费米", "晶格", "拓扑", "相变",
]
_NAME_SUFFIXES = [
    "之舞", "之歌", "之谜", "之梦", "之光", "之影", "之变",
    "之旋", "之浪", "之花", "之森", "之海", "之山", "之云",
    "初现", "绽放", "消散", "轮回", "永恒", "瞬间", "余辉",
    "碎片", "回响", "烙印", "图腾", "诗篇", "序曲", "终章",
]

_next_id = 10000   # 从大号开始，避免与现有 id 冲突


def make_recipe(init_name, evo_name, color_name,
                grid_size=None, cycle_steps=None,
                postprocess="none", name_override=None):
    global _next_id
    init_tpl  = TEMPLATES["init"][init_name]
    evo_tpl   = TEMPLATES["evolution"][evo_name]
    color_tpl = TEMPLATES["color"][color_name]

    w, h = grid_size or random.choice(GRID_SIZES)
    if cycle_steps is None:
        cycle_steps = random.choice(CYCLES)

    if name_override:
        name = name_override
    else:
        pp_tag = f"_{postprocess}" if postprocess != "none" else ""
        name   = f"{init_name}_{evo_name}_{color_name}{pp_tag}_{w}x{h}"

    recipe = {
        "name": name,
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
        "cycle": {"steps": cycle_steps},
        "id": _next_id
    }
    _next_id += 1

    if postprocess and postprocess != "none":
        recipe["postprocess"] = {"effect": postprocess}
    return recipe


def safe_filename(name):
    s = re.sub(r'[\\/*?:"<>|]', "_", name)
    return s.strip("_")[:100]


def save_recipe(recipe):
    fname = safe_filename(recipe["name"] + ".json")
    fpath = os.path.join(EFFECTS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(recipe, f, ensure_ascii=False, indent=2)
    return fpath


def get_existing_names():
    """获取 effects/ 中已有的所有配方 name"""
    names = set()
    if not os.path.exists(EFFECTS_DIR):
        return names
    for f in os.listdir(EFFECTS_DIR):
        if not f.endswith(".json"):
            continue
        fpath = os.path.join(EFFECTS_DIR, f)
        try:
            with open(fpath, encoding="utf-8") as fp:
                r = json.load(fp)
                names.add(r.get("name", ""))
        except Exception:
            pass
    return names


def generate():
    existing_names = get_existing_names()
    print(f"已有配方 name 数: {len(existing_names)}")
    count = 0

    # ── 阶段 1: 核心组合（init × evolution，每对配 3~6 个 color + 变体） ──
    print("阶段1: 核心组合...")
    evo_sample = EVOLUTION_NAMES[:]
    random.shuffle(evo_sample)

    for evo_name in evo_sample:
        n_init  = min(len(INIT_NAMES), random.randint(5, 15))
        n_color = min(len(COLOR_NAMES), random.randint(3, 8))
        chosen_inits  = random.sample(INIT_NAMES, n_init)
        chosen_colors = random.sample(COLOR_NAMES, n_color)

        for init_name in chosen_inits:
            for color_name in chosen_colors:
                for pp in random.sample(POSTPROCESS_LIST, k=random.randint(1, 2)):
                    grid  = random.choice(GRID_SIZES)
                    cycle = random.choice(CYCLES)
                    pp_tag  = f"_{pp}" if pp != "none" else ""
                    base_name = f"{init_name}_{evo_name}_{color_name}{pp_tag}_{grid[0]}x{grid[1]}"
                    # 唯一化
                    candidate = base_name
                    attempt = 1
                    while candidate in existing_names:
                        candidate = base_name + f"_{attempt}"
                        attempt += 1
                    existing_names.add(candidate)

                    recipe = make_recipe(
                        init_name, evo_name, color_name,
                        grid_size=grid, cycle_steps=cycle,
                        postprocess=pp, name_override=candidate
                    )
                    save_recipe(recipe)
                    count += 1
        if count >= 800:
            break
    print(f"  阶段1完成: {count} 条")

    # ── 阶段 2: 网格尺寸变体 ────────────────────────────────────
    print("阶段2: 网格尺寸变体...")
    # 从已有 name 反推一些 (init, evo, color, pp) 组合
    sampled = []
    for name in list(existing_names)[:600]:
        parts = name.split("_")
        if len(parts) >= 3:
            sampled.append(name)
    random.shuffle(sampled)

    for base_name in sampled[:300]:
        # 解析 base_name 不太可靠，直接随机选新 grid
        init_name  = random.choice(INIT_NAMES)
        evo_name   = random.choice(EVOLUTION_NAMES)
        color_name = random.choice(COLOR_NAMES)
        pp         = random.choice(POSTPROCESS_LIST)
        grid       = random.choice(GRID_SIZES)
        cycle      = random.choice(CYCLES)

        candidate = f"{init_name}_{evo_name}_{color_name}_{pp}_{grid[0]}x{grid[1]}"
        if candidate in existing_names:
            candidate += f"_{random.randint(10,99)}"
        if candidate in existing_names:
            continue
        existing_names.add(candidate)

        recipe = make_recipe(init_name, evo_name, color_name,
                             grid_size=grid, cycle_steps=cycle,
                             postprocess=pp, name_override=candidate)
        save_recipe(recipe)
        count += 1
        if count >= 1300:
            break
    print(f"  阶段2完成: {count} 条")

    # ── 阶段3: 后处理全遍历（精选 60 个组合）────────────────
    print("阶段3: 后处理全遍历...")
    random.shuffle(evo_sample)
    精选 = []
    for evo_name in evo_sample[:15]:
        for init_name in random.sample(INIT_NAMES, k=random.randint(2, 4)):
            精选.append((init_name, evo_name))
    精选 = 精选[:60]

    for init_name, evo_name in 精选:
            for pp in POSTPROCESS_LIST:
                candidate = f"{init_name}_{evo_name}_{color_name}_{pp}_{grid[0]}x{grid[1]}"
                if candidate in existing_names:
                    candidate += f"_{random.randint(10,99)}"
                if candidate in existing_names:
                    continue
                existing_names.add(candidate)
                recipe = make_recipe(init_name, evo_name, color_name,
                                     grid_size=grid, postprocess=pp,
                                     name_override=candidate)
                save_recipe(recipe)
                count += 1
    print(f"  阶段3完成: {count} 条")

    # ── 阶段 4: 中文命名配方 ────────────────────────────────────
    print("阶段4: 中文命名配方...")
    used_chinese = set()
    for i in range(600):
        attempts = 0
        while attempts < 50:
            prefix = random.choice(_NAME_PREFIXES)
            suffix = random.choice(_NAME_SUFFIXES)
            cname  = prefix + suffix
            if cname not in used_chinese:
                used_chinese.add(cname)
                break
            attempts += 1
        else:
            cname = f"{random.choice(_NAME_PREFIXES)}{i}"

        init_name  = random.choice(INIT_NAMES)
        evo_name   = random.choice(EVOLUTION_NAMES)
        color_name = random.choice(COLOR_NAMES)
        pp         = random.choice(POSTPROCESS_LIST)
        grid       = random.choice(GRID_SIZES)
        cycle      = random.choice(CYCLES)

        if cname in existing_names:
            cname += f"_{random.randint(10,99)}"
        existing_names.add(cname)

        recipe = make_recipe(init_name, evo_name, color_name,
                             grid_size=grid, cycle_steps=cycle,
                             postprocess=pp, name_override=cname)
        save_recipe(recipe)
        count += 1
    print(f"  阶段4完成: {count} 条")

    # ── 阶段 5: 随机广撒网，填满到 2200 ───────────────────────
    print("阶段5: 随机广撒网...")
    while count < 2200:
        init_name  = random.choice(INIT_NAMES)
        evo_name   = random.choice(EVOLUTION_NAMES)
        color_name = random.choice(COLOR_NAMES)
        pp         = random.choice(POSTPROCESS_LIST)
        grid       = random.choice(GRID_SIZES)
        cycle      = random.choice(CYCLES)

        candidate = f"{init_name}_{evo_name}_{color_name}_{pp}_{grid[0]}x{grid[1]}"
        if candidate in existing_names:
            candidate += f"_{count}"
        if candidate in existing_names:
            continue
        existing_names.add(candidate)

        recipe = make_recipe(init_name, evo_name, color_name,
                             grid_size=grid, cycle_steps=cycle,
                             postprocess=pp, name_override=candidate)
        save_recipe(recipe)
        count += 1

    print(f"  阶段5完成: {count} 条")
    return count


if __name__ == "__main__":
    print("=" * 60)
    print("CA Render Engine —— 配方暴力扩容 v3")
    print("=" * 60)
    n = generate()
    total = len([f for f in os.listdir(EFFECTS_DIR) if f.endswith(".json")])
    print("=" * 60)
    print(f"  本次新增: {n} 个")
    print(f"  目录共有: {total} 个 JSON 配方")
    print("=" * 60)
