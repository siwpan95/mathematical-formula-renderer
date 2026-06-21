#!/usr/bin/env python3
"""
缩略图生成器 — 为 effects/ 目录下的所有配方生成 128×128 缩略图。

用法：
    python tools/gen_thumbs.py [--size 128] [--steps 100] [--workers 1]

输出：
    effects/thumbs/ 目录，每个配方对应一个 {hash8}.png 文件。
    文件名与配方 JSON 的 hash8 对应，方便主程序加载。

注意：
    由于 EvolutionSystem 内部有全局状态（numba JIT 等），
    多线程可能引发问题。默认使用单线程（--workers 1）。
    如需加速，建议分批次运行。
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

# ── 确保可以 import draw 包 ─────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pygame
import numpy as np

from entities.recipe import RecipeEntity
from systems.evolution import EvolutionSystem
from systems.colormap import ColorSystem


# ================================================================
#  缩略图渲染器（使用 pygame 保存，无需 PIL）
# ================================================================

class ThumbnailRenderer:
    """渲染器：加载配方 → 演化 N 步 → 输出 RGB 数组 → 保存 PNG"""

    def __init__(self, thumb_size=128, evo_steps=80):
        self.thumb_size = thumb_size
        self.evo_steps = evo_steps
        self.evo_sys = EvolutionSystem()
        self.color_sys = ColorSystem()
        # 最小 pygame 初始化（不需要窗口）
        pygame.display.init()

    def render(self, json_path: Path) -> np.ndarray | None:
        """
        渲染单个配方的缩略图。
        返回 (thumb_size, thumb_size, 3) uint8 数组，失败返回 None。
        """
        try:
            # 1. 加载配方
            entity = RecipeEntity.from_json(str(json_path))

            # 2. 初始化（编译公式 + 初始化网格）
            self.evo_sys._initialize(entity)

            # 3. 演化 N 步（让图案变得有趣）
            for _ in range(self.evo_steps):
                self.evo_sys.update(entity)

            # 4. 计算颜色
            self.color_sys.update(entity)

            # 5. 获取 RGB 数组 (h, w, 3) uint8
            rgb_hw = entity.grid.rgb_hw
            if rgb_hw is None:
                return None

            return rgb_hw

        except Exception as e:
            print(f"  ❌ {json_path.name}: {e}")
            return None

    def save_thumb(self, rgb_hw: np.ndarray, thumb_path: Path) -> bool:
        """将 RGB 数组保存为 PNG（使用 pygame）"""
        try:
            # pygame.surfarray.make_surface 需要 (w, h, 3) 的 uint8 数组
            # rgb_hw 是 (h, w, 3)，需要转置
            rgb_wh = np.transpose(rgb_hw, (1, 0, 2))  # (h,w,3) → (w,h,3)
            surf = pygame.surfarray.make_surface(rgb_wh)
            surf = pygame.transform.smoothscale(surf, (self.thumb_size, self.thumb_size))
            pygame.image.save(surf, str(thumb_path))
            return True
        except Exception as e:
            print(f"  ❌ 保存失败 {thumb_path.name}: {e}")
            return False


def recipe_content_hash(recipe: dict) -> str:
    """计算配方内容的 8 位哈希（与 normalize_names_v4.py 一致）"""
    key_data = {
        'grid': recipe.get('grid', {}),
        'evolution': recipe.get('evolution', {}),
        'color': recipe.get('color', {}),
        'cycle': recipe.get('cycle', {}),
        'postprocess': recipe.get('postprocess', {}),
    }
    s = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def scan_recipes(effects_dir: Path) -> list[Path]:
    """扫描 effects 目录，返回所有 JSON 文件路径"""
    return sorted(effects_dir.glob('*.json'))


def process_one(json_path: Path, thumbs_dir: Path,
                thumb_size: int, evo_steps: int) -> tuple[str, bool]:
    """
    处理单个配方。
    返回 (json_path.name, success)。
    """
    try:
        with open(json_path, encoding='utf-8') as fp:
            recipe = json.load(fp)

        h = recipe_content_hash(recipe)
        thumb_path = thumbs_dir / f"{h}.png"

        # 跳过已存在的缩略图
        if thumb_path.exists():
            return (json_path.name, True)

        renderer = ThumbnailRenderer(thumb_size=thumb_size, evo_steps=evo_steps)
        rgb = renderer.render(json_path)
        if rgb is None:
            return (json_path.name, False)

        success = renderer.save_thumb(rgb, thumb_path)
        return (json_path.name, success)

    except Exception as e:
        print(f"  ❌ {json_path.name}: {e}")
        return (json_path.name, False)


def main():
    parser = argparse.ArgumentParser(description='为配方生成缩略图')
    parser.add_argument('--effects-dir', type=Path,
                        default=PROJECT_ROOT / 'effects',
                        help='配方目录 (默认: effects/)')
    parser.add_argument('--thumbs-dir', type=Path,
                        default=PROJECT_ROOT / 'effects' / 'thumbs',
                        help='缩略图输出目录 (默认: effects/thumbs/)')
    parser.add_argument('--size', type=int, default=128,
                        help='缩略图尺寸 (默认: 128)')
    parser.add_argument('--steps', type=int, default=80,
                        help='演化步数 (默认: 80)')
    parser.add_argument('--workers', type=int, default=1,
                        help='并行线程数 (默认: 1，因 ECS 系统限制)')
    parser.add_argument('--force', action='store_true',
                        help='强制重新生成所有缩略图')
    parser.add_argument('--limit', type=int, default=0,
                        help='只生成前 N 个（测试用）')
    args = parser.parse_args()

    effects_dir = args.effects_dir
    thumbs_dir = args.thumbs_dir
    thumb_size = args.size
    evo_steps = args.steps
    workers = args.workers
    limit = args.limit

    if not effects_dir.exists():
        print(f"❌ 配方目录不存在: {effects_dir}")
        sys.exit(1)

    thumbs_dir.mkdir(parents=True, exist_ok=True)

    # 扫描配方
    recipes = scan_recipes(effects_dir)
    total = len(recipes)
    print(f"找到 {total} 个配方文件")

    if total == 0:
        print("❌ 没有找到任何配方文件")
        sys.exit(1)

    # 统计已存在的缩略图
    existing = list(thumbs_dir.glob('*.png'))
    if not args.force:
        print(f"已存在 {len(existing)} 个缩略图，跳过")
        # 过滤掉已有缩略图的配方
        to_process = []
        for rp in recipes:
            try:
                with open(rp, encoding='utf-8') as fp:
                    recipe = json.load(fp)
                h = recipe_content_hash(recipe)
                if not (thumbs_dir / f"{h}.png").exists():
                    to_process.append(rp)
            except Exception:
                to_process.append(rp)  # 读取失败也加入
        print(f"需要生成: {len(to_process)} 个")
    else:
        to_process = recipes
        print(f"强制重新生成所有 {total} 个缩略图")

    if limit > 0 and len(to_process) > limit:
        to_process = to_process[:limit]
        print(f"限制模式：只生成前 {limit} 个")

    if len(to_process) == 0:
        print("✅ 所有缩略图已生成完毕")
        return

    # 单线程生成（避免 ECS 系统冲突）
    print(f"\n开始生成缩略图 (单线程, {evo_steps} 步演化)...")
    start_time = time.time()

    ok = 0
    failed = 0

    for i, rp in enumerate(to_process, 1):
        name, success = process_one(rp, thumbs_dir, thumb_size, evo_steps)
        if success:
            ok += 1
        else:
            failed += 1

        # 进度显示（每 20 个更新一次）
        if i % 20 == 0 or i == len(to_process):
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(to_process) - i) / rate if rate > 0 else 0
            print(f"  {i}/{len(to_process)} "
                  f"({ok} ✅, {failed} ❌) "
                  f"速度: {rate:.1f}/s, 预计: {eta:.0f}s")

    elapsed = time.time() - start_time
    print(f"\n完成: {ok} 个成功, {failed} 个失败")
    if elapsed > 0:
        print(f"总耗时: {elapsed:.1f}s ({ok/elapsed:.1f} 个/秒)")

    # 最终统计
    final_count = len(list(thumbs_dir.glob('*.png')))
    print(f"缩略图目录: {thumbs_dir} ({final_count} 个文件)")


if __name__ == '__main__':
    main()
