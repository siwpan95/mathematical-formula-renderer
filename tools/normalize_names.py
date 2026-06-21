"""统一 effects/ 文件名 & 清理中文名碰撞

规则：
  文件名 = {init}_{evo}_{color}_{pp}_{W}x{H}_{hash8}.json
  （hash8 = init+evo+color+grid+pp+cycle 的 SHA1 前 8 位，保证内容不同则文件名不同）

  JSON 内 name 字段 = 人类可读名（保留原有中/英文名，仅去重）
     中文名去重方式：在 JSON name 后加 ·后缀（不是文件名后缀）

用法:
  cd D:/allin/not/OK/draw
  python tools/normalize_names.py          # 预览，不修改
  python tools/normalize_names.py --apply # 执行重命名
"""
import json
import os
import re
import sys
import hashlib
from collections import defaultdict

BASE   = os.path.dirname(os.path.abspath(__file__))
EFFECTS = os.path.abspath(os.path.join(BASE, "..", "effects"))


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def content_hash(r):
    """内容指纹（忽略 id / name / filename）"""
    grid  = r.get("grid", {})
    evo   = r.get("evolution", {})
    color = r.get("color", {})
    pp    = ""
    if r.get("postprocess"):
        pp = r["postprocess"].get("effect", "")
    cycle = r.get("cycle", {}).get("steps", 0)

    blob = "|".join([
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
    ])
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:8]


def safe(s):
    return re.sub(r'[\\/*?:"<>|]', "_", s).strip("_")[:60]


def build_filename(r):
    """统一文件名（不含 .json）"""
    init_name  = r.get("grid", {}).get("initial", {}).get("type", "formula")
    # 从原 name 或 rule 里尽量还原模板名（取 JSON name 的前三段）
    raw_name = r.get("name", "unknown")
    parts = raw_name.split("_")
    # 尝试还原 init / evo / color 名
    ini  = parts[0] if len(parts) > 0 else "init"
    evo  = parts[1] if len(parts) > 1 else "evo"
    col  = parts[2] if len(parts) > 2 else "color"

    grid = r.get("grid", {})
    w = grid.get("width", 0)
    h = grid.get("height", 0)

    pp = "none"
    if r.get("postprocess"):
        pp = r["postprocess"].get("effect", "none")

    h8 = content_hash(r)
    return f"{safe(ini)}_{safe(evo)}_{safe(col)}_{pp}_{w}x{h}_{h8}"


def normalize(dry_run=True):
    files = [f for f in os.listdir(EFFECTS) if f.endswith(".json")]
    print(f"扫描 {len(files)} 个文件...")

    # ── 第 1 步：按内容哈希分组，找出真正的内容重复 ──────
    hash_groups = defaultdict(list)   # hash8 -> [(fname, recipe)]
    for fname in files:
        r = load(os.path.join(EFFECTS, fname))
        if r is None:
            print(f"  ⚠ 无法解析: {fname}")
            continue
        h8 = content_hash(r)
        hash_groups[h8].append((fname, r))

    true_dupes = {h: v for h, v in hash_groups.items() if len(v) > 1}
    print(f"\n真正内容重复（跨文件）: {len(true_dupes)} 组")
    total_dup = sum(len(v) - 1 for v in true_dupes.values())
    if total_dup > 0:
        print(f"  可清理: {total_dup} 个")
        for h8, flist in sorted(true_dupes.items(), key=lambda x: -len(x[1])):
            print(f"  [{len(flist)} 个] hash={h8}")
            for i, (fn, _) in enumerate(flist):
                tag = "（保留）" if i == 0 else "（删除）"
                print(f"    {fn} {tag}")

    # ── 第 2 步：构建新文件名，检测碰撞 ───────────────────
    new_names = {}   # old_fname -> new_fname (不含 .json)
    used_new  = {}   # new_fname -> old_fname（检测碰撞）

    for fname in files:
        r = load(os.path.join(EFFECTS, fname))
        if r is None:
            continue
        base = build_filename(r)
        new = base
        suffix = 1
        while new in used_new:
            # 极小概率：不同内容产生相同文件名，加序号区分
            new = f"{base}_{suffix}"
            suffix += 1
        used_new[new] = fname
        new_names[fname] = new

    collisions = {new: old for new, old in used_new.items()
                 if sum(1 for v in new_names.values() if v.startswith(new)) > 1}

    # ── 第 3 步：更新 JSON name 字段（去重）────────────────
    # 收集所有人类可读名，给重复的加 ·序号
    hr_names = defaultdict(list)   # human_readable_name -> [fname, ...]
    for fname in files:
        r = load(os.path.join(EFFECTS, fname))
        if r is None:
            continue
        hr = r.get("name", fname.replace(".json", ""))
        hr_names[hr].append(fname)

    name_map = {}   # fname -> 去重后的 name
    for hr, fnames in hr_names.items():
        if len(fnames) == 1:
            name_map[fnames[0]] = hr
        else:
            for i, fn in enumerate(fnames):
                if i == 0:
                    name_map[fn] = hr
                else:
                    name_map[fn] = f"{hr}·{i+1}"

    # ── 报告 ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"新文件名预览（前 30 个）:")
    print(f"{'='*60}")
    for fname in sorted(files)[:30]:
        if fname in new_names:
            r   = load(os.path.join(EFFECTS, fname))
            hr  = name_map.get(fname, fname)
            mark = ""
            if fname.replace(".json","") != new_names[fname]:
                mark = " ← 改名"
            print(f"  {fname:50s} -> {new_names[fname]}.json{mark}")
            print(f"       name字段: {hr}")

    changed = sum(1 for f in files if f.replace(".json","") != new_names.get(f,""))
    print(f"\n需改名文件: {changed} 个")
    print(f"内容重复组: {len(true_dupes)} 组 ({total_dup} 个冗余)")

    if dry_run:
        print(f"\n{'='*60}")
        print(f"以上为预览。要执行，加 --apply 参数。")
        print(f"建议先备份 effects/ 目录。")
        return

    # ── 执行 ──────────────────────────────────────────────
    # 先删除真正重复的文件
    deleted = 0
    for h8, flist in true_dupes.items():
        for fn, _ in flist[1:]:
            os.remove(os.path.join(EFFECTS, fn))
            deleted += 1
            print(f"  删除重复: {fn}")
    print(f"  删除内容重复: {deleted} 个")

    # 更新 JSON name 字段 & 重命名文件
    renamed = 0
    for fname in files:
        if not os.path.exists(os.path.join(EFFECTS, fname)):
            continue   # 已被删除
        r    = load(os.path.join(EFFECTS, fname))
        new = new_names.get(fname, fname.replace(".json",""))
        new_fn = new + ".json"

        # 更新 name 字段
        if fname in name_map:
            r["name"] = name_map[fname]

        # 先写回 JSON（用新文件名）
        new_path = os.path.join(EFFECTS, new_fn)
        save(new_path, r)

        # 如果新旧文件名不同，删除旧文件
        old_path = os.path.join(EFFECTS, fname)
        if old_path != new_path and os.path.exists(old_path):
            os.remove(old_path)
            renamed += 1

    final = len([f for f in os.listdir(EFFECTS) if f.endswith(".json")])
    print(f"\n{'='*60}")
    print(f"  重命名: {renamed} 个")
    print(f"  删除重复: {deleted} 个")
    print(f"  最终文件数: {final}")
    print(f"{'='*60}")


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    print("=" * 60)
    print("  CA Render Engine —— 文件名统一 & 去重")
    print("=" * 60)
    normalize(dry_run=dry)
