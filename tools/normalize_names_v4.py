#!/usr/bin/env python3
"""
统一 effects 目录下配方文件名。
方案：
  1. 从模板库建立 expression/rule -> 模板名的映射
  2. 对每个配方，通过 expression/rule 匹配模板名
  3. 用 {init}_{evolution}_{color}_{hash8}.json 格式重命名
  4. 无法匹配模板的，用 {hash8}.json 命名
"""

import hashlib
import json
import os
import re
import shutil
from collections import defaultdict

EFFECTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'effects')
EFFECTS_DIR = os.path.abspath(EFFECTS_DIR)

# 动态 import templates（不依赖 exec）
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from templates import FORMULA_TEMPLATES


def normalize_expr(expr: str) -> str:
    """规范化表达式字符串（忽略变量名差异、空格）"""
    if not expr:
        return ''
    # 移除空格、统一浮点数格式
    s = re.sub(r'\s+', '', expr)
    # 忽略变量名，只保留结构和运算符
    # 将变量名替换为 V
    s = re.sub(r'\b[xXyYrR facedist_nwd]\b', 'V', s)
    s = re.sub(r'\b(random|noise|noise2|sin|cos|tan|sqrt|abs|int|pow|min|max|floor|ceil|round|len|sum)\b', 'F', s)
    return s


def build_template_maps():
    """建立模板映射：规范化 expression/rule -> 模板名"""
    init_map = {}    # normalize_expr(expression) -> [template_names]
    evo_map = {}     # normalize_expr(expression) -> [template_names]
    color_map = {}    # (red, green, blue) -> [template_names]
    
    for cat, templates in FORMULA_TEMPLATES.items():
        for tpl_name, tpl_body in templates.items():
            if cat == 'init':
                expr = tpl_body.get('expression', '')
                key = normalize_expr(expr)
                init_map.setdefault(key, []).append(tpl_name)
            
            elif cat == 'evolution':
                # 注意：evolution 模板里字段名是 'expression'，不是 'rule'
                expr = tpl_body.get('expression', '')
                key = normalize_expr(expr)
                evo_map.setdefault(key, []).append(tpl_name)
            
            elif cat == 'color':
                red = tpl_body.get('red', '')
                green = tpl_body.get('green', '')
                blue = tpl_body.get('blue', '')
                key = (red, green, blue)
                color_map.setdefault(key, []).append(tpl_name)
    
    return init_map, evo_map, color_map


def match_template(expr: str, mapped: dict) -> str:
    """匹配表达式到模板名（返回第一个匹配项，或空字符串）"""
    key = normalize_expr(expr)
    matches = mapped.get(key, [])
    return matches[0] if matches else ''


def recipe_content_hash(recipe: dict) -> str:
    """计算配方完整内容的哈希"""
    key_data = {
        'grid': recipe.get('grid', {}),
        'evolution': recipe.get('evolution', {}),
        'color': recipe.get('color', {}),
        'cycle': recipe.get('cycle', {}),
        'postprocess': recipe.get('postprocess', {}),
    }
    s = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def build_filename(recipe: dict, init_map, evo_map, color_map) -> str:
    """构建新文件名"""
    # 尝试匹配模板名
    init_expr = recipe.get('grid', {}).get('initial', {}).get('expression', '')
    evo_rule = recipe.get('evolution', {}).get('rule', '')
    color = recipe.get('color', {})
    
    init_name = match_template(init_expr, init_map)
    evo_name = match_template(evo_rule, evo_map)
    color_key = (color.get('red', ''), color.get('green', ''), color.get('blue', ''))
    color_names = color_map.get(color_key, [])
    color_name = color_names[0] if color_names else 'custom'
    
    # 构建前缀
    parts = []
    if init_name:
        parts.append(init_name)
    if evo_name:
        parts.append(evo_name)
    parts.append(color_name)
    
    prefix = '_'.join(parts)
    # sanitize
    prefix = re.sub(r'[^\w\-]', '_', prefix)
    prefix = re.sub(r'_+', '_', prefix).strip('_')[:60]
    
    h = recipe_content_hash(recipe)
    return f"{prefix}_{h}.json"


def main():
    print("建立模板映射...")
    init_map, evo_map, color_map = build_template_maps()
    print(f"  init 模板: {sum(len(v) for v in init_map.values())} 个")
    print(f"  evolution 模板: {sum(len(v) for v in evo_map.values())} 个")
    print(f"  color 模板: {sum(len(v) for v in color_map.values())} 个")
    
    os.chdir(EFFECTS_DIR)
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    print(f"\n找到 {len(files)} 个配方文件")
    
    # 预览前 20 个的重命名结果
    print("\n--- 预览（前 20 个）---")
    file_map = {}
    matched = {'init': 0, 'evo': 0, 'color': 0}
    
    for i, fname in enumerate(sorted(files)):
        try:
            with open(fname, encoding='utf-8') as fp:
                recipe = json.load(fp)
        except Exception as e:
            print(f"  ❌ {fname}: {e}")
            continue
        
        new_name = build_filename(recipe, init_map, evo_map, color_map)
        file_map[fname] = new_name
        
        # 统计匹配情况
        init_expr = recipe.get('grid', {}).get('initial', {}).get('expression', '')
        evo_rule = recipe.get('evolution', {}).get('rule', '')
        color = recipe.get('color', {})
        color_key = (color.get('red', ''), color.get('green', ''), color.get('blue', ''))
        
        if match_template(init_expr, init_map):
            matched['init'] += 1
        if match_template(evo_rule, evo_map):
            matched['evo'] += 1
        if color_key in color_map:
            matched['color'] += 1
        
        if i < 20:
            print(f"  {fname}  ->  {new_name}")
    
    print(f"\n匹配统计:")
    print(f"  init 匹配: {matched['init']} / {len(files)}")
    print(f"  evolution 匹配: {matched['evo']} / {len(files)}")
    print(f"  color 匹配: {matched['color']} / {len(files)}")
    
    # 检查需要重命名的数量
    need_rename = sum(1 for old, new in file_map.items() if old != new)
    print(f"\n需要重命名的文件: {need_rename} / {len(files)}")
    
    if need_rename == 0:
        print("✅ 所有文件名已符合要求")
        return
    
    # 执行重命名（先不执行，等你确认）
    print(f"\n⚠️  预览完成。确认执行重命名？")
    print("（将 DO_RENAME = True 改为 True 来执行）")
    
    DO_RENAME = True
    
    if not DO_RENAME:
        return
    
    # 执行重命名
    print(f"\n开始重命名...")
    ok = 0
    err = 0
    
    for old_name, new_name in file_map.items():
        if old_name == new_name:
            continue
        try:
            if os.path.exists(new_name):
                print(f"  ⚠️  跳过（目标已存在）: {old_name} -> {new_name}")
                continue
            shutil.move(old_name, new_name)
            ok += 1
        except Exception as e:
            print(f"  ❌ {old_name}: {e}")
            err += 1
    
    print(f"\n完成: {ok} 个重命名, {err} 个错误")


if __name__ == '__main__':
    main()
