#!/usr/bin/env python3
"""统一 effects 目录下配方文件名：英文标识 + 8位内容哈希。"""

import hashlib
import json
import os
import re
import shutil
from collections import defaultdict

EFFECTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'effects')
EFFECTS_DIR = os.path.abspath(EFFECTS_DIR)

# 中文名 -> 英文关键词映射（用于文件名）
CN_TO_EN = {
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
    '棋盘': 'checkerboard', '波纹': 'wave', '网格': 'grid',
    '生命': 'life', '死亡': 'death', '诞生': 'birth', '毁灭': 'destruction',
    '创造': 'creation', '秩序': 'order', '熵': 'entropy',
}

def sanitize_name(name: str) -> str:
    """将任意名称转为安全的文件名前缀（英文）"""
    # 如果包含中文字符，尝试翻译
    if re.search(r'[\u4e00-\u9fff]', name):
        en_parts = []
        for cn, en in CN_TO_EN.items():
            if cn in name:
                en_parts.append(en)
        if en_parts:
            base = '_'.join(en_parts)
        else:
            # 无法翻译，用通用名
            base = 'recipe'
    else:
        # 已经是英文，直接 sanitize
        base = name
    
    # Sanitize：替换空格和特殊字符为 _
    base = re.sub(r'[^\w\-]', '_', base)
    base = re.sub(r'_+', '_', base).strip('_')
    return base[:40]  # 限制长度


def content_hash(recipe: dict) -> str:
    """计算配方内容的 8 位哈希"""
    # 用关键字段计算哈希（排除 name 和 id，因为它们不影响实际效果）
    key_data = {
        'grid': recipe.get('grid', {}),
        'evolution': recipe.get('evolution', {}),
        'color': recipe.get('color', {}),
        'cycle': recipe.get('cycle', {}),
    }
    s = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def build_new_filename(recipe: dict) -> str:
    """构建新文件名：{英文前缀}_{hash8}.json"""
    name = recipe.get('name', 'recipe')
    prefix = sanitize_name(name)
    h = content_hash(recipe)
    return f"{prefix}_{h}.json"


def main():
    os.chdir(EFFECTS_DIR)
    
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    print(f"找到 {len(files)} 个配方文件")
    
    # 第一步：计算所有文件的新文件名，检测冲突
    file_map = {}  # old_name -> new_name
    hash_groups = defaultdict(list)  # new_name -> [old_names]
    
    for fname in files:
        try:
            with open(fname, encoding='utf-8') as fp:
                recipe = json.load(fp)
        except Exception as e:
            print(f"  ❌ 读取失败: {fname}: {e}")
            continue
        
        new_name = build_new_filename(recipe)
        file_map[fname] = new_name
        hash_groups[new_name].append(fname)
    
    # 检查冲突（理论上不应该有，因为 hash8 在内容不同时极难碰撞）
    conflicts = {k: v for k, v in hash_groups.items() if len(v) > 1}
    if conflicts:
        print(f"\n⚠️  发现 {len(conflicts)} 个文件名冲突（哈希碰撞）：")
        for new_name, old_names in list(conflicts.items())[:10]:
            print(f"  {new_name}: {old_names}")
    else:
        print("✅ 无文件名冲突（哈希唯一）")
    
    # 第二步：执行重命名（先预览）
    print(f"\n--- 预览（前 20 个）---")
    for i, (old_name, new_name) in enumerate(sorted(file_map.items())[:20]):
        print(f"  {old_name}  ->  {new_name}")
    
    # 检查有多少需要重命名
    need_rename = sum(1 for old, new in file_map.items() if old != new)
    print(f"\n需要重命名的文件: {need_rename} / {len(files)}")
    
    if need_rename == 0:
        print("✅ 所有文件名已符合要求，无需重命名")
        return
    
    # 第三步：执行重命名
    print(f"\n开始重命名...")
    ok = 0
    err = 0
    skipped = 0
    
    for old_name, new_name in file_map.items():
        if old_name == new_name:
            skipped += 1
            continue
        
        try:
            # 如果目标文件已存在（理论上不会，因为 hash 唯一），跳过
            if os.path.exists(new_name):
                print(f"  ⚠️  目标已存在，跳过: {old_name} -> {new_name}")
                skipped += 1
                continue
            
            shutil.move(old_name, new_name)
            ok += 1
        except Exception as e:
            print(f"  ❌ 重命名失败: {old_name}: {e}")
            err += 1
    
    print(f"\n完成: {ok} 个重命名, {skipped} 个跳过, {err} 个错误")
    
    # 验证
    final_files = [f for f in os.listdir('.') if f.endswith('.json')]
    print(f"最终文件数: {len(final_files)}")


if __name__ == '__main__':
    main()
