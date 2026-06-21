"""查重 & 清理 draw/effects 中的重复/近似配方

判断重复的标准：
  1. 完全相同：init + evolution + color + grid + postprocess + cycle 全部相同
  2. 名称相似：去掉 _数字 后缀后名称相同

用法:
  cd D:/allin/not/OK/draw
  python tools/dedup_recipes.py           # 仅报告，不删除
  python tools/dedup_recipes.py --delete # 删除重复项（保留每组的第一个）
"""
import json
import os
import re
import sys
import hashlib
from collections import defaultdict

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
EFFECTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "effects"))


def load_recipe(fpath):
    try:
        with open(fpath, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def recipe_fingerprint(r):
    """生成用于判重的指纹（忽略 id 和 name）"""
    grid  = r.get("grid", {})
    evo   = r.get("evolution", {})
    color = r.get("color", {})
    pp    = "none"
    if r.get("postprocess"):
        pp = r["postprocess"].get("effect", "none")
    cycle = r.get("cycle", {}).get("steps", 0)

    parts = [
        grid.get("initial", {}).get("expression", ""),
        evo.get("rule", ""),
        color.get("red", ""),
        color.get("green", ""),
        color.get("blue", ""),
        str(grid.get("width", 0)),
        str(grid.get("height", 0)),
        str(grid.get("wrap", "")),
        pp,
        str(cycle),
    ]
    raw = "|".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def dedup(dry_run=True):
    files = [f for f in os.listdir(EFFECTS_DIR) if f.endswith(".json")]
    print(f"扫描 {len(files)} 个文件...")

    # 按指纹分组 / 按基础名分组
    fp_map  = defaultdict(list)   # 指纹 -> [(fname, recipe), ...]
    name_map = defaultdict(list)   # 基础名 -> [(fname, recipe), ...]
    id_map   = {}                  # id -> fname

    for fname in files:
        fpath = os.path.join(EFFECTS_DIR, fname)
        r = load_recipe(fpath)
        if r is None:
            print(f"  ⚠ 无法解析: {fname}")
            continue

        fp = recipe_fingerprint(r)
        fp_map[fp].append((fname, r))

        # 基础名（去掉末尾 _数字）
        bn = re.sub(r'_\d+\.json$', '', fname)
        name_map[bn].append((fname, r))

        rid = r.get("id")
        if rid is not None:
            if rid in id_map:
                print(f"  ⚠ ID 冲突: {rid} <- {fname} 与 {id_map[rid]}")
            id_map[rid] = fname

    # ── 报告完全相同 ──────────────────────────────────────
    exact = {fp: flist for fp, flist in fp_map.items() if len(flist) > 1}
    print(f"\n{'='*60}")
    print(f"完全相同（指纹相同）: {len(exact)} 组")
    n_exact = sum(len(v) - 1 for v in exact.values())
    print(f"  可删除冗余: {n_exact} 个")

    for fp, flist in sorted(exact.items(), key=lambda x: -len(x[1])):
        names = "  ".join(
            f"{fname} (保留)" if i == 0 else f"{fname} (可删)"
            for i, (fname, _) in enumerate(flist)
        )
        print(f"  [{len(flist)} 个] {names}")

    # ── 报告名称相似 ──────────────────────────────────────
    similar = {bn: flist for bn, flist in name_map.items() if len(flist) > 1}
    print(f"\n{'='*60}")
    print(f"名称相似（去掉 _数字 后缀后相同）: {len(similar)} 组")
    n_similar = sum(len(v) - 1 for v in similar.values())
    print(f"  可删除冗余: {n_similar} 个")

    for bn, flist in sorted(similar.items(), key=lambda x: -len(x[1]))[:30]:
        print(f"  [{len(flist)} 个] {bn}:")
        for i, (fname, r) in enumerate(flist):
            mark = " (保留)" if i == 0 else " (可删)"
            print(f"    {fname}{mark}")
            if r:
                init_expr  = r.get("grid", {}).get("initial", {}).get("expression", "")[:40]
                evo_rule  = r.get("evolution", {}).get("rule", "")[:50]
                print(f"      init={init_expr}... evo={evo_rule}...")

    # ── 执行删除 ──────────────────────────────────────
    if dry_run:
        total_del = n_exact + n_similar
        print(f"\n{'='*60}")
        print(f"以上是预览，共可删除 {total_del} 个冗余文件。")
        print(f"要执行删除，请加 --delete 参数。")
        print(f"建议先备份 effects/ 目录。")
        return

    deleted = 0
    # 删除完全相同的冗余（保留每组第一个）
    for fp, flist in exact.items():
        for fname, _ in flist[1:]:
            fpath = os.path.join(EFFECTS_DIR, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
                deleted += 1
                print(f"  删除（完全相同）: {fname}")

    # 删除名称相似的冗余（保留每组第一个）
    for bn, flist in similar.items():
        for fname, _ in flist[1:]:
            fpath = os.path.join(EFFECTS_DIR, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
                deleted += 1
                print(f"  删除（名称相似）: {fname}")

    remaining = len([f for f in os.listdir(EFFECTS_DIR) if f.endswith(".json")])
    print(f"\n{'='*60}")
    print(f"共删除 {deleted} 个冗余文件，剩余 {remaining} 个")
    print(f"{'='*60}")


if __name__ == "__main__":
    dry = "--delete" not in sys.argv
    print("=" * 60)
    print("  CA Render Engine —— 配方查重 & 清理")
    print("=" * 60)
    dedup(dry_run=dry)
