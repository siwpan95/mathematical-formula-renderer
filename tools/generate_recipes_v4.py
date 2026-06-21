"""暴力扩容 draw/effects v4 —— 目标 2500+ 个配方"""
import json, os, random, re

random.seed(42)
BASE = os.path.dirname(os.path.abspath(__file__))
EFFECTS = os.path.abspath(os.path.join(BASE, "..", "effects"))
os.makedirs(EFFECTS, exist_ok=True)

# ── 加载模板 ────────────────────────────────────────────────────────
def load_tpl(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        ns = {}
        exec(f.read(), ns)
        for k, v in ns.items():
            if k.endswith("TEMPLATES") and isinstance(v, dict):
                return v
    return {}

T = {}
for fn, key in [
    ("init.py","init"),("evolution.py","evolution"),("color.py","color"),
    ("boundary.py","boundary"),("postprocess.py","postprocess"),
    ("topology.py","topology"),("neighborhood.py","neighborhood"),
]:
    fp = os.path.abspath(os.path.join(BASE, "..", "templates", fn))
    T[key] = load_tpl(fp) if os.path.exists(fp) else {}

INIT  = sorted(T["init"].keys())
EVO   = sorted(T["evolution"].keys())
COL   = sorted(T["color"].keys())
print(f"init={len(INIT)}, evolution={len(EVO)}, color={len(COL)}")

PP_LIST  = ["none","bloom","edge","motion_trail","invert","vignette"]
GRIDS   = [(64,64),(100,100),(128,128),(150,150),(180,180),
            (200,150),(256,192),(300,200),(320,240),(400,300),
            (512,384),(200,200),(160,160),(80,80),(240,180)]
CYCLES  = [0,100,200,300,500,800,1000,1200,1500,2000,3000,5000]

PREFIX  = ["幻境","星云","涟漪","火焰","冰晶","迷宫","脉冲","漩涡","极光",
           "量子","混沌","分形","湍流","扩散","反应","激发","螺旋","脉动",
           "谐振","潮汐","霜花","熔岩","彩虹","迷雾","雷暴","电浆","虚空",
           "光辉","深渊","梦境","风暴","微光","裂变","纠缠","坍缩","膨胀",
           "涌现","突变","进化","虫洞","时光","记忆","回声","极夜","晨曦",
           "星尘","银河","黑洞","等离子","晶格","拓扑","相变","共振","波动"]
SUFFIX  = ["之舞","之歌","之谜","之梦","之光","之影","之变","之旋","之浪",
           "之花","之森","之海","之山","之云","初现","绽放","消散","轮回",
           "永恒","瞬间","余辉","碎片","回响","图腾","诗篇","序曲","终章"]

_next_id = 20000

def make_name(init_name, evo_name, color_name, pp, grid):
    pp_tag = ("_" + pp) if pp and pp != "none" else ""
    return f"{init_name}_{evo_name}_{color_name}{pp_tag}_{grid[0]}x{grid[1]}"

def make_recipe(init_name, evo_name, color_name,
               grid=None, cycle=None, pp="none", name=None):
    global _next_id
    w, h = grid or random.choice(GRIDS)
    cyc  = cycle if cycle is not None else random.choice(CYCLES)
    t_init  = T["init"][init_name]
    t_evo   = T["evolution"][evo_name]
    t_color = T["color"][color_name]
    r = {
        "name": name or make_name(init_name, evo_name, color_name, pp, (w,h)),
        "grid": {
            "width": w, "height": h,
            "wrap": random.choice([True, False]),
            "initial": {"type":"formula","expression": t_init["expression"]}
        },
        "evolution": {
            "rule": t_evo["expression"],
            "variables": t_evo.get("variables", ["c","avg_n"])
        },
        "color": {
            "red":   t_color.get("red",  "v"),
            "green": t_color.get("green","v"),
            "blue":  t_color.get("blue", "v")
        },
        "cycle": {"steps": cyc},
        "id": _next_id
    }
    _next_id += 1
    if pp and pp != "none":
        r["postprocess"] = {"effect": pp}
    return r

def sname(name):
    return re.sub(r'[\\/*?:"<>|]',"_", name).strip("_")[:100]

def save(r):
    fp = os.path.join(EFFECTS, sname(r["name"]+".json"))
    with open(fp,"w",encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return fp

def existing_names():
    s = set()
    for f in os.listdir(EFFECTS):
        if not f.endswith(".json"): continue
        try:
            with open(os.path.join(EFFECTS,f),encoding="utf-8") as fp:
                s.add(json.load(fp).get("name",""))
        except: pass
    return s

def unique_name(base, taken):
    c = base
    i = 1
    while c in taken:
        c = base + "_" + str(i)
        i += 1
    taken.add(c)
    return c

def run():
    taken = existing_names()
    print(f"已有配方: {len(taken)}")
    cnt = 0

    # 阶段1: 每个 evolution 配多个 init+color+grid+pp
    print("阶段1: 核心组合...")
    evo_list = list(EVO)
    random.shuffle(evo_list)
    for evo in evo_list:
        ni = min(len(INIT), random.randint(5,14))
        nc = min(len(COL),  random.randint(3,8))
        for ini in random.sample(INIT, ni):
            for col in random.sample(COL, nc):
                for pp in random.sample(PP_LIST, k=random.randint(1,2)):
                    grid = random.choice(GRIDS)
                    base = make_name(ini, evo, col, pp, grid)
                    nm = unique_name(base, taken)
                    recipe = make_recipe(ini, evo, col, grid=grid, pp=pp, name=nm)
                    save(recipe)
                    cnt += 1
        if cnt >= 900:
            break
    print(f"  完成: {cnt}")

    # 阶段2: 后处理全遍历（精选组合）
    print("阶段2: 后处理全遍历...")
    pairs = []
    for evo in random.sample(EVO, k=min(12,len(EVO))):
        for ini in random.sample(INIT, k=random.randint(2,4)):
            pairs.append((ini, evo))
    pairs = pairs[:50]
    for ini, evo in pairs:
        for col in random.sample(COL, k=random.randint(2,5)):
            grid = random.choice(GRIDS)
            for pp in PP_LIST:
                base = make_name(ini, evo, col, pp, grid)
                nm = unique_name(base, taken)
                recipe = make_recipe(ini, evo, col, grid=grid, pp=pp, name=nm)
                save(recipe)
                cnt += 1
    print(f"  完成: {cnt}")

    # 阶段3: 中文命名
    print("阶段3: 中文命名...")
    used_cn = set()
    for i in range(700):
        cname = ""
        for _ in range(30):
            p = random.choice(PREFIX)
            s = random.choice(SUFFIX)
            t = p + s
            if t not in used_cn:
                used_cn.add(t)
                cname = t
                break
        if not cname:
            cname = random.choice(PREFIX) + str(i)
        nm = unique_name(cname, taken)
        ini  = random.choice(INIT)
        evo  = random.choice(EVO)
        col  = random.choice(COL)
        grid = random.choice(GRIDS)
        pp   = random.choice(PP_LIST)
        cyc  = random.choice(CYCLES)
        recipe = make_recipe(ini, evo, col, grid=grid, cycle=cyc, pp=pp, name=nm)
        save(recipe)
        cnt += 1
    print(f"  完成: {cnt}")

    # 阶段4: 填满到 2300
    print("阶段4: 随机补齐...")
    while cnt < 2300:
        ini  = random.choice(INIT)
        evo  = random.choice(EVO)
        col  = random.choice(COL)
        grid = random.choice(GRIDS)
        pp   = random.choice(PP_LIST)
        cyc  = random.choice(CYCLES)
        base = make_name(ini, evo, col, pp, grid)
        nm   = unique_name(base, taken)
        recipe = make_recipe(ini, evo, col, grid=grid, cycle=cyc, pp=pp, name=nm)
        save(recipe)
        cnt += 1
    print(f"  完成: {cnt}")

    total = len([f for f in os.listdir(EFFECTS) if f.endswith(".json")])
    print(f"\n{'='*50}")
    print(f"  新增: {cnt}")
    print(f"  目录共有: {total} 个配方")
    print(f"{'='*50}")

if __name__ == "__main__":
    run()
