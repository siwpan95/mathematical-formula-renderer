#!/usr/bin/env python3
"""统一 effects 目录下配方文件名：英文前缀 + 8位内容哈希（含 postprocess）。"""

import hashlib
import json
import os
import re
import shutil
from collections import defaultdict

EFFECTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'effects')
EFFECTS_DIR = os.path.abspath(EFFECTS_DIR)

# 中文名关键词 -> 英文映射
CN_MAP = {
    '幻境': 'fantasy', '之歌': 'song', '星云': 'nebula', '混沌': 'chaos',
    '之舞': 'dance', '之影': 'shadow', '之光': 'light', '之梦': 'dream',
    '之火': 'fire', '之水': 'water', '之风': 'wind', '之土': 'earth',
    '迷宫': 'maze', '螺旋': 'spiral', '波纹': 'ripple', '碎片': 'shard',
    '棱镜': 'prism', '极光': 'aurora', '深渊': 'abyss', '苍穹': 'sky',
    '星尘': 'stardust', '月光': 'moonlight', '日出': 'sunrise', '日落': 'sunset',
    '暴雨': 'storm', '雪花': 'snow', '烈焰': 'flame', '寒冰': 'frost',
    '雷鸣': 'thunder', '地震': 'quake', '飓风': 'hurricane', '海啸': 'tsunami',
    '龙卷风': 'tornado', '彩虹': 'rainbow', '极夜': 'polar_night',
    '永恒': 'eternal', '瞬间': 'moment', '无限': 'infinite',
    '旅途': 'journey', '归途': 'return', '起点': 'origin', '终点': 'end',
    '心跳': 'heartbeat', '呼吸': 'breath', '脉搏': 'pulse',
    '棋盘': 'checkerboard', '网格': 'grid', '条纹': 'stripe',
    '生命': 'life', '死亡': 'death', '诞生': 'birth', '毁灭': 'destruction',
    '创造': 'creation', '秩序': 'order', '熵': 'entropy',
    '环': 'annulus', '高斯': 'gaussian', '噪声': 'noise', '平滑': 'smooth',
    '梯度': 'grad', '径向': 'radial', '朱利亚': 'julia', '曼德博': 'mandelbrot',
    '正弦': 'sine', '余弦': 'cosine', '正切': 'tan', '双曲': 'hyperbolic',
    '反应': 'reaction', '扩散': 'diffusion', '波动': 'wave', '热': 'heat',
    '薛定谔': 'schrodinger', '伊辛': 'ising', '格拉斯': 'glasser',
    '洛伦兹': 'lorenz', '罗斯勒': 'rossler', '杜芬': 'duffing',
    '分形': 'fractal', '细胞': 'cellular', '免疫': 'immune', '捕食': 'predator',
    '竞争': 'competition', '合作': 'cooperation',
}

def name_to_prefix(name: str) -> str:
    """将 name 字段转为英文文件名前缀"""
    if not name:
        return 'recipe'
    
    # 已经是英文
    if not re.search(r'[\u4e00-\u9fff]', name):
        # sanitize
        prefix = re.sub(r'[^\w\-]', '_', name)
        prefix = re.sub(r'_+', '_', prefix).strip('_')
        return prefix[:50]
    
    # 中文：尝试映射翻译
    words = set()
    for cn, en in CN_MAP.items():
        if cn in name:
            words.add(en)
    
    if words:
        prefix = '_'.join(sorted(words))
    else:
        # 无法翻译，用 pinyin 首字母？直接用 recipe
        prefix = 'recipe'
    
    return prefix[:50]


def recipe_content_hash(recipe: dict) -> str:
    """计算配方完整内容的哈希（包含所有影响渲染的字段）"""
    # 收集所有影响渲染的字段
    key_data = {
        'grid': recipe.get('grid', {}),
        'evolution': recipe.get('evolution', {}),
        'color': recipe.get('color', {}),
        'cycle': recipe.get('cycle', {}),
        'postprocess': recipe.get('postprocess', {}),
    }
    s = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def build_new_filename(recipe: dict) -> str:
    """构建新文件名：{英文前缀}_{hash8}.json"""
    prefix = name_to_prefix(recipe.get('name', ''))
    h = recipe_content_hash(recipe)
    return f"{prefix}_{h}.json"


def main():
    os.chdir(EFFECTS_DIR)
    
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    print(f"找到 {len(files)} 个配方文件")
    
    # 第一步：计算所有文件的新文件名
    file_map = {}  # old_name -> new_name
    hash_groups = defaultdict(list)  # hash8 -> [old_names]
    
    for fname in files:
        try:
            with open(fname, encoding='utf-8') as fp:
                recipe = json.load(fp)
        except Exception as e:
            print(f"  ❌ 读取失败: {fname}: {e}")
            continue
        
        new_name = build_new_filename(recipe)
        file_map[fname] = new_name
        
        h = recipe_content_hash(recipe)
        hash_groups[h].append(fname)
    
    # 检查哈希碰撞（8位哈希理论碰撞概率很低，但内容相同才算真碰撞）
    true_dupes = []
    for h, fnames in hash_groups.items():
        if len(fnames) <= 1:
            continue
        # 检查内容是否真相同
        contents = []
        for fn in fnames:
            with open(fn, encoding='utf-8') as fp:
                contents.append(json.dumps(json.load(fp), sort_keys=True))
        if len(set(contents)) == 1:
            true_dupes.append((h, fnames))
    
    if true_dupes:
        print(f"\n⚠️  发现 {len(true_dupes)} 组内容完全相同的文件（真·重复）：")
        for h, fnames in true_dupes[:10]:
            print(f"  hash={h}: {fnames}")
    else:
        print("\n✅ 无内容完全相同的重复文件")
    
    # 第二步：预览重命名
    print(f"\n--- 预览（前 30 个）---")
    need_rename = 0
    for i, (old_name, new_name) in enumerate(sorted(file_map.items())):
        if old_name != new_name:
            need_rename += 1
            if i < 30:
                print(f"  {old_name}  ->  {new_name}")
    
    print(f"\n需要重命名的文件: {need_rename} / {len(files)}")
    
    if need_rename == 0:
        print("✅ 所有文件名已符合要求")
        # 但还要检查是否有 true dupes 需要清理
        if true_dupes:
            print(f"发现 {sum(len(v) for _, v in true_dupes)} 个重复文件，建议清理")
        return
    
    # 第三步：确认后执行重命名
    print(f"\n⚠️  即将重命名 {need_rename} 个文件")
    print("确认执行？(代码中直接修改 DO_RENAME = True 来执行)")
    
    DO_RENAME = False  # 改为 True 来执行重命名
    
    if not DO_RENAME:
        print("\n（预览模式结束，未执行重命名）")
        print("请确认预览结果正确后，将 DO_RENAME 改为 True 重新运行")
        return
    
    # 执行重命名
    print(f"\n开始重命名...")
    ok = 0
    err = 0
    skipped = 0
    
    for old_name, new_name in file_map.items():
        if old_name == new_name:
            skipped += 1
            continue
        
        try:
            if os.path.exists(new_name):
                # 目标已存在：检查是否内容相同
                with open(old_name, encoding='utf-8') as f1, \
                     open(new_name, encoding='utf-8') as f2:
                    if json.dumps(json.load(f1), sort_keys=True) == \
                       json.dumps(json.load(f2), sort_keys=True):
                        # 内容相同，删除旧文件
                        os.remove(old_name)
                        print(f"  🗑️  删除重复: {old_name} (与 {new_name} 相同)")
                        skipped += 1
                        continue
                # 内容不同，用更长哈希
                h = recipe_content_hash(json.load(open(old_name, encoding='utf-8')))
                longer_h = hashlib.sha1(
                    json.dumps(json.load(open(old_name, encoding='utf-8')), 
                              sort_keys=True).encode()
                ).hexdigest()[:12]
                new_name = new_name.replace(f"_{h}.json", f"_{longer_h}.json")
            
            shutil.move(old_name, new_name)
            ok += 1
        except Exception as e:
            print(f"  ❌ 失败: {old_name}: {e}")
            err += 1
    
    print(f"\n完成: {ok} 个重命名, {skipped} 个跳过/删除, {err} 个错误")
    
    # 最终统计
    final = [f for f in os.listdir('.') if f.endswith('.json')]
    print(f"最终文件数: {len(final)}")


if __name__ == '__main__':
    main()
