"""暴力扩容 draw/effects —— 目标 2500+ 个配方（完全正确版）

正确使用 templates 模块的方式：
  from templates import FORMULA_TEMPLATES
  FORMULA_TEMPLATES 是一个 dict，key 为分类名，value 为该分类的模板 dict：
    "init" / "evolution" / "color" / "boundary" / "postprocess" / "topology" / "neighborhood"

用法:
  cd D:/allin/not/OK/draw
  python tools/gen_recipes.py          # 默认补齐到 2500
  python tools/gen_recipes.py 6000    # 补齐到 6000
"""
import json
import os
import random
import re
import sys

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
sys.path.insert(0, PROJECT_DIR)

from templates import FORMULA_TEMPLATES

EFFECTS_DIR = os.path.join(PROJECT_DIR, "effects")
os.makedirs(EFFECTS_DIR, exist_ok=True)

# ── 所有模板分类 ──────────────────────────────────────────────────
CATEGORIES = ["init", "evolution", "color", "boundary",
               "postprocess", "topology", "neighborhood"]

print("模板统计:")
TMPL = {}   # cat -> {name: {...}}
NAMES = {}   # cat -> [name1, name2, ...]
for cat in CATEGORIES:
    d = FORMULA_TEMPLATES.get(cat, {})
    TMPL[cat]  = d
    NAMES[cat] = sorted(d.keys())
    print(f"  {cat:15s}: {len(NAMES[cat])} 个")

n_init  = len(NAMES["init"])
n_evo   = len(NAMES["evolution"])
n_color = len(NAMES["color"])
print(f"\n  核心组合数: {n_init} × {n_evo} × {n_color} = {n_init*n_evo*n_color}")

# ── 参数空间 ──────────────────────────────────────────────────────
PP_LIST  = ["none", "bloom", "edge", "motion_trail", "invert", "vignette"]
GRIDS   = [
    (64, 64),   (100, 100),  (128, 128),  (150, 150),
    (180, 180), (200, 150),  (256, 192),  (300, 200),
    (320, 240), (400, 300),  (512, 384),  (200, 200),
    (160, 160), (80, 80),    (240, 180),  (600, 400),
]
CYCLES  = [0, 100, 200, 300, 500, 600, 800, 1000, 1200,
           1500, 2000, 3000, 5000]

CN_PRE = [
    "幻境", "星云", "涟漪", "火焰", "冰晶", "迷宫", "脉冲",
    "漩涡", "极光", "量子", "混沌", "分形", "波函数", "湍流",
    "扩散", "反应", "激发", "螺旋", "脉动", "谐振", "潮汐",
    "霜花", "熔岩", "彩虹", "迷雾", "雷暴", "电浆", "虚空",
    "光辉", "深渊", "梦境", "炼狱", "天堂", "风暴", "微光",
    "裂变", "纠缠", "坍缩", "膨胀", "震荡", "漂移",
    "涌现", "突变", "进化", "虫洞", "时光", "记忆", "回声",
    "极夜", "晨曦", "黄昏", "星尘", "银河", "黑洞", "中子",
    "等离子", "超流体", "玻色", "费米", "晶格", "拓扑", "相变",
    "共振", "波动", "折射", "散射", "干涉", "衍射", "极化",
]
CN_SUF = [
    "之舞", "之歌", "之谜", "之梦", "之光", "之影", "之变",
    "之旋", "之浪", "之花", "之森", "之海", "之山", "之云",
    "初现", "绽放", "消散", "轮回", "永恒", "瞬间", "余辉",
    "碎片", "回响", "烙印", "图腾", "诗篇", "序曲", "终章",
    "深渊", "彼岸", "星轨", "光年", "维度", "奇点", "弦论",
]

_next_id = 50000


def make_recipe(init_name, evo_name, color_name,
                grid_size=None, cycle_steps=None,
                postprocess="none", name_override=None):
    global _next_id
    w, h = grid_size or random.choice(GRIDS)
    if cycle_steps is None:
        cycle_steps = random.choice(CYCLES)

    init_tpl  = TMPL["init"][init_name]
    evo_tpl   = TMPL["evolution"][evo_name]
    color_tpl = TMPL["color"][color_name]

    if name_override:
        name = name_override
    else:
        pp_tag = f"_{postprocess}" if postprocess and postprocess != "none" else ""
        name = f"{init_name}_{evo_name}_{color_name}{pp_tag}_{w}x{h}"

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
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip("_")[:100]


def save_recipe(recipe):
    fname = safe_filename(recipe["name"] + ".json")
    fpath = os.path.join(EFFECTS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(recipe, f, ensure_ascii=False, indent=2)


def get_existing_names():
    names = set()
    if not os.path.exists(EFFECTS_DIR):
        return names
    for f in os.listdir(EFFECTS_DIR):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(EFFECTS_DIR, f), encoding="utf-8") as fp:
                names.add(json.load(fp).get("name", ""))
        except Exception:
            pass
    return names


def unique_name(base, taken):
    c = base
    i = 1
    while c in taken:
        c = f"{base}_{i}"
        i += 1
    taken.add(c)
    return c


def run(target=2500):
    taken = get_existing_names()
    existing = len(taken)
    print(f"\n已有配方: {existing} 个，目标: {target}+\n")
    cnt = 0

    # ── 阶段 1: 核心组合 ──────────────────────────────────────
    print("[1/5] 核心组合...")
    evo_list = list(NAMES["evolution"])
    random.shuffle(evo_list)

    for evo_name in evo_list:
        ni = min(n_init, random.randint(6, 16))
        nc = min(n_color, random.randint(4, 10))
        for init_name in random.sample(NAMES["init"], ni):
            for color_name in random.sample(NAMES["color"], nc):
                pp   = random.choice(PP_LIST)
                grid = random.choice(GRIDS)
                base = f"{init_name}_{evo_name}_{color_name}_{pp}_{grid[0]}x{grid[1]}"
                nm   = unique_name(base, taken)
                recipe = make_recipe(init_name, evo_name, color_name,
                                    grid_size=grid, postprocess=pp, name_override=nm)
                save_recipe(recipe)
                cnt += 1
        if cnt >= 900:
            break
    print(f"  新增: {cnt}")

    # ── 阶段 2: 后处理全遍历 ─────────────────────────────────
    print("\n[2/5] 后处理全遍历...")
    pairs = []
    for evo in random.sample(list(NAMES["evolution"]), k=min(12, n_evo)):
        for ini in random.sample(NAMES["init"], k=random.randint(2, 4)):
            pairs.append((ini, evo))
    pairs = pairs[:50]

    for ini, evo in pairs:
        for col in random.sample(NAMES["color"], k=random.randint(2, 5)):
            grid = random.choice(GRIDS)
            for pp in PP_LIST:
                base = f"{ini}_{evo}_{col}_{pp}_{grid[0]}x{grid[1]}"
                nm   = unique_name(base, taken)
                recipe = make_recipe(ini, evo, col,
                                    grid_size=grid, postprocess=pp, name_override=nm)
                save_recipe(recipe)
                cnt += 1
    print(f"  累计新增: {cnt}")

    # ── 阶段 3: 网格 + cycle 变体 ────────────────────────────
    print("\n[3/5] 网格 + cycle 变体...")
    for _ in range(500):
        ini  = random.choice(NAMES["init"])
        evo  = random.choice(NAMES["evolution"])
        col  = random.choice(NAMES["color"])
        pp   = random.choice(PP_LIST)
        grid = random.choice(GRIDS)
        cyc  = random.choice(CYCLES)
        base = f"{ini}_{evo}_{col}_{pp}_{grid[0]}x{grid[1]}_c{cyc}"
        nm   = unique_name(base, taken)
        recipe = make_recipe(ini, evo, col,
                            grid_size=grid, cycle_steps=cyc,
                            postprocess=pp, name_override=nm)
        save_recipe(recipe)
        cnt += 1
    print(f"  累计新增: {cnt}")

    # ── 阶段 4: 中文命名配方 ─────────────────────────────────
    print("\n[4/5] 中文命名配方...")
    used_cn = set()
    for i in range(600):
        for _ in range(30):
            cname = random.choice(CN_PRE) + random.choice(CN_SUF)
            if cname not in used_cn:
                used_cn.add(cname)
                break
        else:
            cname = random.choice(CN_PRE) + str(i)
        nm = unique_name(cname, taken)
        ini  = random.choice(NAMES["init"])
        evo  = random.choice(NAMES["evolution"])
        col  = random.choice(NAMES["color"])
        pp   = random.choice(PP_LIST)
        grid = random.choice(GRIDS)
        recipe = make_recipe(ini, evo, col,
                            grid_size=grid, postprocess=pp, name_override=nm)
        save_recipe(recipe)
        cnt += 1
    print(f"  累计新增: {cnt}")

    # ── 阶段 5: 随机补齐到 target ─────────────────────────────
    print(f"\n[5/5] 随机补齐到 {target}+...")
    while len(taken) < target:
        ini  = random.choice(NAMES["init"])
        evo  = random.choice(NAMES["evolution"])
        col  = random.choice(NAMES["color"])
        pp   = random.choice(PP_LIST)
        grid = random.choice(GRIDS)
        base = f"{ini}_{evo}_{col}_{pp}_{grid[0]}x{grid[1]}"
        nm   = unique_name(base, taken)
        recipe = make_recipe(ini, evo, col,
                            grid_size=grid, postprocess=pp, name_override=nm)
        save_recipe(recipe)
        cnt += 1

    total = len(get_existing_names())
    print(f"\n{'='*50}")
    print(f"  本次新增: {cnt}")
    print(f"  目录共有: {total} 个配方")
    print(f"{'='*50}")


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 2500
    print("=" * 60)
    print("  CA Render Engine —— 配方暴力扩容（完全正确版）")
    print("=" * 60)
    run(target=target)
